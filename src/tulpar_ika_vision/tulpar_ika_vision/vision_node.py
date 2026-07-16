import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

def preprocess_image(frame):
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv_frame = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    return hsv_frame

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',  # Kameranın yayın yaptığı topic ismi
            self.image_callback,
            10)
        self.bridge = CvBridge()
        self.get_logger().info('Görüntü İşleme Düğümü Başlatıldı.')

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        hsv_frame = preprocess_image(frame)

        # Görüntüleri ekranda göstermek için:
        cv2.imshow("Kamera Orijinal", frame)
        cv2.imshow("HSV Maskeli", hsv_frame)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    vision_node = VisionNode()
    rclpy.spin(vision_node)
    vision_node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()