#!/usr/bin/env python3

from typing import Sequence

import cv2
import numpy as np
import rclpy

from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class ImagePreprocessor(Node):
    """Renk iyileştirme, HSV maskeleme ve gürültü temizleme node'u."""

    def __init__(self) -> None:
        super().__init__('image_preprocessor')

        # Başlangıç olarak mavi renk aralığı.
        # Gerçek kamera görüntüsünde yeniden kalibre edilecek.
        self.declare_parameter(
            'lower_hsv',
            [90, 80, 50],
        )
        self.declare_parameter(
            'upper_hsv',
            [135, 255, 255],
        )

        self.declare_parameter('blur_size', 5)
        self.declare_parameter('kernel_size', 5)

        self.declare_parameter('use_clahe', True)
        self.declare_parameter('clahe_clip_limit', 2.0)
        self.declare_parameter('clahe_grid_size', 8)

        self.bridge = CvBridge()

        self.subscription = self.create_subscription(
            Image,
            '/camera/front/color/image_raw',
            self.image_callback,
            qos_profile_sensor_data,
        )

        self.preprocessed_publisher = self.create_publisher(
            Image,
            '/perception/front/image_preprocessed',
            qos_profile_sensor_data,
        )

        self.mask_publisher = self.create_publisher(
            Image,
            '/perception/front/color_mask',
            qos_profile_sensor_data,
        )

        self.get_logger().info(
            'OpenCV ön işleme node’u çalışıyor.'
        )

        self.get_logger().info(
            'Girdi: /camera/front/color/image_raw'
        )

        self.get_logger().info(
            'Çıktılar: '
            '/perception/front/image_preprocessed, '
            '/perception/front/color_mask'
        )

    @staticmethod
    def odd_positive(value: int) -> int:
        """Filtre çekirdeğini pozitif tek sayıya dönüştürür."""
        value = max(int(value), 1)

        if value % 2 == 0:
            value += 1

        return value

    @staticmethod
    def hsv_array(values: Sequence[int]) -> np.ndarray:
        """ROS parametre listesini uint8 NumPy dizisine çevirir."""
        if len(values) != 3:
            raise ValueError(
                'HSV parametresi tam olarak üç değer içermelidir.'
            )

        return np.asarray(values, dtype=np.uint8)

    def apply_clahe(
        self,
        frame: np.ndarray,
    ) -> np.ndarray:
        """LAB renk uzayında yalnızca parlaklık kanalını iyileştirir."""
        use_clahe = bool(
            self.get_parameter('use_clahe').value
        )

        if not use_clahe:
            return frame

        clip_limit = float(
            self.get_parameter('clahe_clip_limit').value
        )

        grid_size = self.odd_positive(
            self.get_parameter('clahe_grid_size').value
        )

        lab = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2LAB,
        )

        lightness, channel_a, channel_b = cv2.split(lab)

        clahe = cv2.createCLAHE(
            clipLimit=max(clip_limit, 0.1),
            tileGridSize=(grid_size, grid_size),
        )

        improved_lightness = clahe.apply(lightness)

        improved_lab = cv2.merge(
            (
                improved_lightness,
                channel_a,
                channel_b,
            )
        )

        return cv2.cvtColor(
            improved_lab,
            cv2.COLOR_LAB2BGR,
        )

    def image_callback(self, message: Image) -> None:
        try:
            frame = self.bridge.imgmsg_to_cv2(
                message,
                desired_encoding='bgr8',
            )
        except Exception as error:
            self.get_logger().error(
                f'Görüntü dönüşüm hatası: {error}'
            )
            return

        try:
            lower_hsv = self.hsv_array(
                self.get_parameter('lower_hsv').value
            )

            upper_hsv = self.hsv_array(
                self.get_parameter('upper_hsv').value
            )
        except ValueError as error:
            self.get_logger().error(str(error))
            return

        blur_size = self.odd_positive(
            self.get_parameter('blur_size').value
        )

        kernel_size = self.odd_positive(
            self.get_parameter('kernel_size').value
        )

        # 1. Gürültü azaltma
        blurred = cv2.GaussianBlur(
            frame,
            (blur_size, blur_size),
            0,
        )

        # 2. Kontrast ve parlaklık iyileştirme
        enhanced = self.apply_clahe(blurred)

        # 3. HSV renk uzayına geçiş
        hsv = cv2.cvtColor(
            enhanced,
            cv2.COLOR_BGR2HSV,
        )

        # 4. Renk maskesi
        mask = cv2.inRange(
            hsv,
            lower_hsv,
            upper_hsv,
        )

        # 5. Gürültü temizleme
        kernel = np.ones(
            (kernel_size, kernel_size),
            dtype=np.uint8,
        )

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            kernel,
        )

        # 6. Maskedeki küçük boşlukları kapatma
        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            kernel,
        )

        # 7. Yalnızca seçilen renk bölgelerini göster
        preprocessed = cv2.bitwise_and(
            enhanced,
            enhanced,
            mask=mask,
        )

        preprocessed_message = self.bridge.cv2_to_imgmsg(
            preprocessed,
            encoding='bgr8',
        )
        preprocessed_message.header = message.header

        mask_message = self.bridge.cv2_to_imgmsg(
            mask,
            encoding='mono8',
        )
        mask_message.header = message.header

        self.preprocessed_publisher.publish(
            preprocessed_message
        )

        self.mask_publisher.publish(mask_message)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ImagePreprocessor()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
