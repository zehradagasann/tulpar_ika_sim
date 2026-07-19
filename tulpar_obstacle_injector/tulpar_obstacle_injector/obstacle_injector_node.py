"""/detections (tulpar_ika_msgs/Detection2DArray) -> /parkur/koni_tespitleri (geometry_msgs/PoseArray).

Sozlesme (17 Temmuz 2026, Zehra/Emin ile netlesildi):
  - class_name == "traffic_cone" olan tespitler koni sayilir.
  - Detection2D.depth_m / depth_valid zaten perception tarafinda hesaplaniyor,
    burada ayrica derinlik cikarimi yapilmiyor - sadece pikselden 3D'ye
    pinhole geri izdusumu + TF ile odom'a tasima yapilir.
  - Cikan PoseArray, gelen her /detections mesajindan taze uretilir (gecmis
    biriktirilmez) - "sadece o an gorunen koniler" sozlesmesiyle tutarli.
  - min_confidence (18 Temmuz 2026, Emin'in fine-tuning sonucuna gore onerisi):
    traffic_cone'un mAP50-95=0.869 (domain gap riski, "uzakta kacirma" sorunu
    biliniyor) cikmasi nedeniyle varsayilan YOLO esigi (0.5) yerine 0.6
    kullaniliyor.
  - PointCloud2 koprusu (18 Temmuz 2026): Nav2'nin nav2_costmap_2d::ObstacleLayer
    plugin'i PoseArray kabul etmiyor, sadece LaserScan/PointCloud2 - bu yuzden
    ayni koni noktalari ayrica /parkur/koni_engelleri (PointCloud2, target_frame)
    olarak da yayinlaniyor. PoseArray sozlesmesi (baska tuketicisi olabilir diye)
    dokunulmadan korundu, PointCloud2 sadece costmap icin ek bir cikti.
"""

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from geometry_msgs.msg import Pose, PoseArray, PointStamped
from sensor_msgs.msg import CameraInfo, PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header
from tulpar_ika_msgs.msg import Detection2DArray

import tf2_ros
import tf2_geometry_msgs  # noqa: F401  (PointStamped tf2 donusumunu kaydeder)
from tf2_ros import TransformException


class ObstacleInjector(Node):

    def __init__(self):
        super().__init__('obstacle_injector')

        self.declare_parameter('cone_class_name', 'traffic_cone')
        self.declare_parameter('detections_topic', '/detections')
        self.declare_parameter('camera_info_topic', '/d435if/depth/camera_info')
        self.declare_parameter('output_topic', '/parkur/koni_tespitleri')
        self.declare_parameter('pointcloud_output_topic', '/parkur/koni_engelleri')
        self.declare_parameter('target_frame', 'odom')
        self.declare_parameter('tf_timeout_sec', 0.2)
        # Emin'in fine-tuning sonucuna gore onerisi (18 Temmuz): traffic_cone
        # P=0.99/R=0.951 ama mAP50-95=0.869 (domain gap riski var, "uzakta
        # kacirma" sorunu biliniyor) - YOLO'nun varsayilan 0.5 esigi yerine
        # daha temkinli 0.6 kullanilmasi onerildi, dusuk-guven tespitler
        # gurultu sayilip costmap'e beslenmemeli.
        self.declare_parameter('min_confidence', 0.6)

        self.cone_class_name = self.get_parameter('cone_class_name').value
        self.target_frame = self.get_parameter('target_frame').value
        self.min_confidence = self.get_parameter('min_confidence').value
        self.tf_timeout = Duration(
            seconds=self.get_parameter('tf_timeout_sec').value)

        self.camera_info = None

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
            Detection2DArray,
            self.get_parameter('detections_topic').value,
            self._detections_callback,
            qos,
        )
        self.pose_array_pub = self.create_publisher(
            PoseArray,
            self.get_parameter('output_topic').value,
            qos,
        )
        self.pointcloud_pub = self.create_publisher(
            PointCloud2,
            self.get_parameter('pointcloud_output_topic').value,
            qos,
        )

        self.get_logger().info(
            f"obstacle_injector basladi: '{self.cone_class_name}' siniflarini "
            f"{self.get_parameter('detections_topic').value} uzerinden dinliyor, "
            f"{self.get_parameter('output_topic').value} ({self.target_frame}) "
            "olarak yayinlayacak."
        )

    def _camera_info_callback(self, msg: CameraInfo):
        self.camera_info = msg

    def _publish_pointcloud(self, stamp, points_xyz):
        header = Header()
        header.stamp = stamp
        header.frame_id = self.target_frame
        cloud = point_cloud2.create_cloud_xyz32(header, points_xyz)
        self.pointcloud_pub.publish(cloud)

    def _detections_callback(self, msg: Detection2DArray):
        pose_array = PoseArray()
        pose_array.header.stamp = msg.header.stamp
        pose_array.header.frame_id = self.target_frame
        points_xyz = []

        if self.camera_info is None:
            self.get_logger().warn(
                'Henuz camera_info alinmadi, koni konumlari hesaplanamiyor.',
                throttle_duration_sec=5.0,
            )
            self.pose_array_pub.publish(pose_array)
            self._publish_pointcloud(msg.header.stamp, points_xyz)
            return

        fx = self.camera_info.k[0]
        fy = self.camera_info.k[4]
        cx = self.camera_info.k[2]
        cy = self.camera_info.k[5]

        source_frame = msg.header.frame_id

        for det in msg.detections:
            if det.class_name != self.cone_class_name:
                continue
            if det.confidence < self.min_confidence:
                continue
            if not det.depth_valid or det.depth_m <= 0.0:
                continue

            depth = det.depth_m
            u = det.center_px.x
            v = det.center_px.y

            point = PointStamped()
            point.header.stamp = msg.header.stamp
            point.header.frame_id = source_frame
            point.point.x = (u - cx) / fx * depth
            point.point.y = (v - cy) / fy * depth
            point.point.z = depth

            try:
                transformed = self.tf_buffer.transform(
                    point, self.target_frame, timeout=self.tf_timeout)
            except TransformException as ex:
                self.get_logger().warn(
                    f"TF donusumu basarisiz ({source_frame} -> "
                    f"{self.target_frame}): {ex}",
                    throttle_duration_sec=5.0,
                )
                continue

            pose = Pose()
            pose.position.x = transformed.point.x
            pose.position.y = transformed.point.y
            pose.position.z = transformed.point.z
            pose.orientation.w = 1.0
            pose_array.poses.append(pose)
            points_xyz.append(
                (transformed.point.x, transformed.point.y, transformed.point.z))

        self.pose_array_pub.publish(pose_array)
        self._publish_pointcloud(msg.header.stamp, points_xyz)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleInjector()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
