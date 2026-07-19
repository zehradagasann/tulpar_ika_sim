import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

from tulpar_ika_perception.brightness_filter import process_frame


class BrightnessFilterNode(Node):
    """
    Ham kamera goruntusunu dinler, parlaklik/kontrast analizine gore
    CLAHE uygular, isli goruntuyu yeni topic'e yayinlar.
    TODO: hangi kamera topic'i (front/rear/rpi_hq) dinlenecek, Talha/Emin
    ile netlesince input_topic parametrize edilecek.
    """

    def __init__(self) -> None:
        super().__init__("brightness_filter_node")
        self.declare_parameter("input_topic", "/rear_camera/image_raw")
        self.declare_parameter("output_topic", "/camera/image_enhanced")

        self._bridge = CvBridge()
        input_topic = self.get_parameter("input_topic").get_parameter_value().string_value
        output_topic = self.get_parameter("output_topic").get_parameter_value().string_value

        self._sub = self.create_subscription(
            Image, input_topic, self._on_image, 10,
        )
        self._pub = self.create_publisher(
            Image, output_topic, 10,
        )

        self._frame_count = 0
        self.get_logger().info(
            f"BrightnessFilterNode basladi. input_topic={input_topic} "
            f"output_topic={output_topic}"
        )

    def _on_image(self, msg: Image) -> None:
        try:
            cv_image = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            output_image, analysis = process_frame(cv_image)
            out_msg = self._bridge.cv2_to_imgmsg(output_image, encoding="bgr8")
        except (CvBridgeError, ValueError) as exc:
            self.get_logger().warning(f"Goruntu frame'i islenemedi: {exc}")
            return

        out_msg.header = msg.header
        self._pub.publish(out_msg)

        self._frame_count += 1
        if self._frame_count % 5 == 0:
            self.get_logger().info(
                "durum=" + analysis.condition
                + " mean=" + f"{analysis.mean_brightness:.1f}"
                + " std=" + f"{analysis.std_contrast:.1f}"
                + " clahe=" + str(analysis.clahe_applied)
            )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = BrightnessFilterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
