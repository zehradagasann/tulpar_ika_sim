import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

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

        self._bridge = CvBridge()

        self._sub = self.create_subscription(
            Image, "/rear_camera/image_raw", self._on_image, 10,
        )
        self._pub = self.create_publisher(
            Image, "/camera/image_enhanced", 10,
        )

        self._frame_count = 0
        self.get_logger().info("BrightnessFilterNode basladi.")

    def _on_image(self, msg: Image) -> None:
        cv_image = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        output_image, analysis = process_frame(cv_image)

        out_msg = Image()
        out_msg.header = msg.header
        out_msg.height = output_image.shape[0]
        out_msg.width = output_image.shape[1]
        out_msg.encoding = "bgr8"
        out_msg.is_bigendian = 0
        out_msg.step = output_image.shape[1] * 3
        out_msg.data = output_image.tobytes()
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
