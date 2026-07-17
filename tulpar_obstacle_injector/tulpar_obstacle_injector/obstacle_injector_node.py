"""/detections (tulpar_ika_msgs/Detection2DArray) -> /parkur/koni_tespitleri (geometry_msgs/PoseArray).

Sozlesme (17 Temmuz 2026, Zehra/Emin ile netlesildi):
  - class_name == "traffic_cone" olan tespitler koni sayilir.
  - Detection2D.depth_m / depth_valid zaten perception tarafinda hesaplaniyor,
    burada ayrica derinlik cikarimi yapilmiyor - sadece pikselden 3D'ye
    pinhole geri izdusumu + TF ile odom'a tasima yapilir.
  - Cikan PoseArray, gelen her /detections mesajindan taze uretilir (gecmis
    biriktirilmez) - "sadece o an gorunen koniler" sozlesmesiyle tutarli.
"""

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from geometry_msgs.msg import Pose, PoseArray, PointStamped
from sensor_msgs.msg import CameraInfo
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
        self.declare_parameter('target_frame', 'odom')
        self.declare_parameter('tf_timeout_sec', 0.2)

        self.cone_class_name = self.get_parameter('cone_class_name').value
        self.target_frame = self.get_parameter('target_frame').value
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

        self.get_logger().info(
            f"obstacle_injector basladi: '{self.cone_class_name}' siniflarini "
            f"{self.get_parameter('detections_topic').value} uzerinden dinliyor, "
            f"{self.get_parameter('output_topic').value} ({self.target_frame}) "
            "olarak yayinlayacak."
        )

    def _camera_info_callback(self, msg: CameraInfo):
        self.camera_info = msg

    def _detections_callback(self, msg: Detection2DArray):
        pose_array = PoseArray()
        pose_array.header.stamp = msg.header.stamp
        pose_array.header.frame_id = self.target_frame

        if self.camera_info is None:
            self.get_logger().warn(
                'Henuz camera_info alinmadi, koni konumlari hesaplanamiyor.',
                throttle_duration_sec=5.0,
            )
            self.pose_array_pub.publish(pose_array)
            return

        fx = self.camera_info.k[0]
        fy = self.camera_info.k[4]
        cx = self.camera_info.k[2]
        cy = self.camera_info.k[5]

        source_frame = msg.header.frame_id

        for det in msg.detections:
            if det.class_name != self.cone_class_name:
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

        self.pose_array_pub.publish(pose_array)


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
