"""/parkur/slalom_target (tulpar_ika_msgs/SlalomTarget) -> /tulpar_bt/hedef_pose
(geometry_msgs/PoseStamped) + /parkur/hiz_seviyesi (std_msgs/String).

TASLAK (18 Temmuz 2026) - Zehra'nin slalom_core.py'si henuz bu repoya
alinmadi ve /parkur/slalom_target'i kendisi hic yayinlamiyor. Bu node,
Talha'nin onerdigi "waypoint" yaklasimini (Zehra'nin onayiyla, bkz.
CLAUDE.md) somut/calisir hale getiren bir baslangic noktasi - Zehra kendi
node'unu yazarken bunu temel alabilir ya da degistirebilir.

Sozlesme:
  - SlalomTarget.target_x_px/target_y_px piksel koordinati, header.frame_id
    hangi kamera optik frame'inde hesaplandigini soyler.
  - obstacle_injector'dan farkli olarak burada Detection2D.depth_m yok -
    slalom_core sadece piksel uretiyor, derinlik BU node icinde depth
    goruntusunden (ayni kamera) o pikselden ornekleniyor.
  - target_x_px/y_px, msg.source_width/height cozunurlugunde hesaplanmis
    olabilir (orn. Zehra'nin RGB uzerinde calisan algoritmasi) - bu, derinlik
    goruntusunun kendi cozunurlugunden FARKLIYSA piksel oransal olarak
    derinlik goruntusune olceklenir (19 Temmuz 2026, onceden bu ayrim
    yapilmiyordu - RGB/derinlik cozunurlugu farkliysa hedef sessizce yanlis
    hesaplaniyordu). Bu sadece FOV/hizalama ozdesse gecerli bir yaklastirma -
    gercek donanimda RGB-derinlik hizalanmasi (align) farkliysa Zehra ile
    tekrar gozden gecirilmeli.
  - turn_direction ayrica tasinmiyor (pose'un konumundan cikarilabilir,
    CLAUDE.md'deki tartismayla tutarli).
  - speed_level PoseStamped'te yer olmadigi icin ayri bir topic'te
    (/parkur/hiz_seviyesi, std_msgs/String) yayinlaniyor - Nav2/MPPI'nin
    kendi hiz limitine ek/override olarak nasil kullanilacagi henuz
    kararlastirilmadi, bu sadece veriyi disari cikariyor.
"""

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped, PointStamped
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import String
from tulpar_ika_msgs.msg import SlalomTarget

import tf2_ros
import tf2_geometry_msgs  # noqa: F401  (PointStamped tf2 donusumunu kaydeder)
from tf2_ros import TransformException


class SlalomHedefBridge(Node):

    def __init__(self):
        super().__init__('slalom_hedef_bridge')

        self.declare_parameter('slalom_target_topic', '/parkur/slalom_target')
        self.declare_parameter('camera_info_topic', '/d435if/depth/camera_info')
        self.declare_parameter('depth_image_topic', '/d435if/depth/image_raw')
        self.declare_parameter('hedef_pose_topic', '/tulpar_bt/hedef_pose')
        self.declare_parameter('hiz_seviyesi_topic', '/parkur/hiz_seviyesi')
        self.declare_parameter('target_frame', 'odom')
        self.declare_parameter('tf_timeout_sec', 0.2)
        self.declare_parameter('depth_sample_window_px', 2)

        self.target_frame = self.get_parameter('target_frame').value
        self.tf_timeout = Duration(
            seconds=self.get_parameter('tf_timeout_sec').value)
        self.depth_window = self.get_parameter('depth_sample_window_px').value

        self.camera_info = None
        self.latest_depth = None  # numpy array, metre cinsinden

        self.cv_bridge = CvBridge()
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.create_subscription(
            CameraInfo,
            self.get_parameter('camera_info_topic').value,
            self._camera_info_callback,
            qos,
        )
        self.create_subscription(
            Image,
            self.get_parameter('depth_image_topic').value,
            self._depth_callback,
            qos,
        )
        self.create_subscription(
            SlalomTarget,
            self.get_parameter('slalom_target_topic').value,
            self._slalom_target_callback,
            qos,
        )
        self.hedef_pose_pub = self.create_publisher(
            PoseStamped,
            self.get_parameter('hedef_pose_topic').value,
            qos,
        )
        self.hiz_seviyesi_pub = self.create_publisher(
            String,
            self.get_parameter('hiz_seviyesi_topic').value,
            qos,
        )

        self.get_logger().info(
            f"slalom_hedef_bridge basladi: "
            f"{self.get_parameter('slalom_target_topic').value} dinleniyor, "
            f"{self.get_parameter('hedef_pose_topic').value} ({self.target_frame}) "
            "olarak yayinlanacak."
        )

    def _camera_info_callback(self, msg: CameraInfo):
        self.camera_info = msg

    def _depth_callback(self, msg: Image):
        depth = self.cv_bridge.imgmsg_to_cv2(msg)
        if msg.encoding in ('16UC1', 'mono16'):
            depth = depth.astype(np.float32) * 0.001  # mm -> m
        else:
            depth = depth.astype(np.float32)
        self.latest_depth = depth

    def _sample_depth(self, u_px: int, v_px: int):
        if self.latest_depth is None:
            return None
        h, w = self.latest_depth.shape[:2]
        win = self.depth_window
        u0, u1 = max(0, u_px - win), min(w, u_px + win + 1)
        v0, v1 = max(0, v_px - win), min(h, v_px + win + 1)
        if u0 >= u1 or v0 >= v1:
            return None
        patch = self.latest_depth[v0:v1, u0:u1]
        valid = patch[np.isfinite(patch) & (patch > 0.0)]
        if valid.size == 0:
            return None
        return float(np.median(valid))

    def _slalom_target_callback(self, msg: SlalomTarget):
        if self.camera_info is None:
            self.get_logger().warn(
                'Henuz camera_info alinmadi, slalom hedefi hesaplanamiyor.',
                throttle_duration_sec=5.0,
            )
            return

        target_x_px = msg.target_x_px
        target_y_px = msg.target_y_px
        if (msg.source_width and msg.source_height
                and (msg.source_width != self.camera_info.width
                     or msg.source_height != self.camera_info.height)):
            scale_x = self.camera_info.width / msg.source_width
            scale_y = self.camera_info.height / msg.source_height
            target_x_px *= scale_x
            target_y_px *= scale_y
            self.get_logger().warn(
                f"slalom_target cozunurlugu ({msg.source_width}x{msg.source_height}) "
                f"derinlik goruntusunden ({self.camera_info.width}x{self.camera_info.height}) "
                "farkli - piksel oransal olceklendi, yaklastirma.",
                throttle_duration_sec=5.0,
            )

        u_px = int(round(target_x_px))
        v_px = int(round(target_y_px))
        depth = self._sample_depth(u_px, v_px)
        if depth is None:
            self.get_logger().warn(
                f"Piksel ({u_px},{v_px}) icin gecerli derinlik bulunamadi, "
                "hedef pose yayinlanmiyor.",
                throttle_duration_sec=5.0,
            )
            return

        fx = self.camera_info.k[0]
        fy = self.camera_info.k[4]
        cx = self.camera_info.k[2]
        cy = self.camera_info.k[5]

        point = PointStamped()
        point.header.stamp = msg.header.stamp
        point.header.frame_id = msg.header.frame_id
        point.point.x = (u_px - cx) / fx * depth
        point.point.y = (v_px - cy) / fy * depth
        point.point.z = depth

        try:
            transformed = self.tf_buffer.transform(
                point, self.target_frame, timeout=self.tf_timeout)
        except TransformException as ex:
            self.get_logger().warn(
                f"TF donusumu basarisiz ({msg.header.frame_id} -> "
                f"{self.target_frame}): {ex}",
                throttle_duration_sec=5.0,
            )
            return

        pose = PoseStamped()
        pose.header.stamp = msg.header.stamp
        pose.header.frame_id = self.target_frame
        pose.pose.position.x = transformed.point.x
        pose.pose.position.y = transformed.point.y
        pose.pose.position.z = 0.0  # zemin uzerindeki hedef, Nav2 2D calisiyor
        pose.pose.orientation.w = 1.0
        self.hedef_pose_pub.publish(pose)

        if msg.speed_level:
            hiz_msg = String()
            hiz_msg.data = msg.speed_level
            self.hiz_seviyesi_pub.publish(hiz_msg)


def main(args=None):
    rclpy.init(args=args)
    node = SlalomHedefBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
