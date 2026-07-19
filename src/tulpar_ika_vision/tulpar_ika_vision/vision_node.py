import cv2
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


def odd_positive(value: int) -> int:
    value = max(int(value), 1)
    if value % 2 == 0:
        value += 1
    return value


def preprocess_image(frame, blur_kernel_size: int):
    """Bulanıklaştırma + HSV dönüşümü yapar.
    NOT: Gerçek bir renk maskelemesi (inRange) burada YOK.
    Renk bazlı filtreleme istiyorsanız cv2.inRange ile bir eşik
    aralığı eklemeniz gerekir.
    """
    kernel_size = odd_positive(blur_kernel_size)
    blurred = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
    hsv_frame = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # HSV verisini bgr8 diye publish etmek downstream node'lar icin
    # sessiz hata uretir; goruntu amacli topic icin tekrar BGR'a cevir.
    return cv2.cvtColor(hsv_frame, cv2.COLOR_HSV2BGR)


class VisionNode(Node):
    def __init__(self) -> None:
        super().__init__('vision_node')

        self.declare_parameter('input_topic', '/camera/image_raw')
        self.declare_parameter('output_topic', '/vision/image_preprocessed')
        self.declare_parameter('blur_kernel_size', 5)

        input_topic = self.get_parameter(
            'input_topic'
        ).get_parameter_value().string_value
        output_topic = self.get_parameter(
            'output_topic'
        ).get_parameter_value().string_value

        self.bridge = CvBridge()

        # NOT: Kamera sürücüleri genelde BEST_EFFORT (sensor) QoS ile
        # yayın yapar; bu yüzden qos_profile_sensor_data kullanılıyor.
        self.subscription = self.create_subscription(
            Image,
            input_topic,
            self.image_callback,
            qos_profile_sensor_data,
        )

        self.publisher = self.create_publisher(
            Image,
            output_topic,
            qos_profile_sensor_data,
        )

        self.get_logger().info('Görüntü İşleme Düğümü Başlatıldı.')
        self.get_logger().info(f'Girdi: {input_topic}')
        self.get_logger().info(f'Çıktı: {output_topic}')

    @staticmethod
    def is_valid_frame(frame) -> bool:
        """Frame'in işlenebilir olup olmadığını kontrol eder.

        None, boş veya beklenmeyen kanal sayısına sahip frame'leri
        GaussianBlur/cvtColor'a göndermeden önce eler.
        """
        if frame is None:
            return False

        if frame.size == 0:
            return False

        if frame.ndim != 3 or frame.shape[2] != 3:
            return False

        return True

    def image_callback(self, msg: Image) -> None:
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except CvBridgeError as error:
            self.get_logger().error(f'Görüntü dönüşüm hatası: {error}')
            return

        if not self.is_valid_frame(frame):
            self.get_logger().warning(
                f'Geçersiz frame alındı (shape={getattr(frame, "shape", None)}), atlanıyor.'
            )
            return

        try:
            output_frame = preprocess_image(
                frame,
                blur_kernel_size=self.get_parameter('blur_kernel_size').value,
            )
        except Exception as error:
            self.get_logger().error(f'Görüntü işleme hatası: {error}')
            return

        try:
            output_msg = self.bridge.cv2_to_imgmsg(output_frame, encoding='bgr8')
        except CvBridgeError as error:
            self.get_logger().error(f'Çıktı mesajı oluşturma hatası: {error}')
            return

        output_msg.header = msg.header
        self.publisher.publish(output_msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    vision_node = VisionNode()

    try:
        rclpy.spin(vision_node)
    except KeyboardInterrupt:
        pass
    finally:
        vision_node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
