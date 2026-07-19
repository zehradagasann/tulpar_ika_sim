#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from tulpar_ika_msgs.msg import (
    Detection2D,
    Detection2DArray,
    SignDetection,
)


class InterfaceTestPublisher(Node):
    """TULPAR Gün 1 mesaj ve topic sözleşmelerini test eder."""

    def __init__(self) -> None:
        super().__init__('interface_test_publisher')

        self.detection_publisher = self.create_publisher(
            Detection2DArray,
            '/detections',
            10,
        )

        self.sign_publisher = self.create_publisher(
            SignDetection,
            '/sign_detected',
            10,
        )

        # Saniyede iki kez çalışır.
        self.timer = self.create_timer(
            0.5,
            self.publish_test_messages,
        )

        self.counter = 0

        self.get_logger().info(
            'Interface test publisher başlatıldı.'
        )
        self.get_logger().info(
            'Yayınlanan topikler: /detections, /sign_detected'
        )

    def publish_test_messages(self) -> None:
        timestamp = self.get_clock().now().to_msg()

        self.publish_detection(timestamp)
        self.publish_sign(timestamp)

        self.counter += 1

        if self.counter % 10 == 0:
            self.get_logger().info(
                f'{self.counter} yayın çevrimi tamamlandı.'
            )

    def publish_detection(self, timestamp) -> None:
        """Örnek mavi koni tespiti yayınlar."""

        array_message = Detection2DArray()

        array_message.header.stamp = timestamp
        array_message.header.frame_id = (
            'camera_front_optical_frame'
        )

        array_message.image_width = 1280
        array_message.image_height = 720

        detection = Detection2D()

        detection.class_id = 10
        detection.class_name = 'blue_cone'
        detection.confidence = 0.92

        detection.bbox.x_offset = 420
        detection.bbox.y_offset = 260
        detection.bbox.width = 90
        detection.bbox.height = 180
        detection.bbox.do_rectify = False

        detection.center_px.x = 465.0
        detection.center_px.y = 350.0
        detection.center_px.z = 0.0

        detection.depth_m = 2.4
        detection.depth_valid = True

        detection.track_id = 0
        detection.track_id_valid = False

        detection.source = Detection2D.SOURCE_OPENCV

        array_message.detections.append(detection)

        self.detection_publisher.publish(array_message)

    def publish_sign(self, timestamp) -> None:
        """Karar node'lariyla uyumlu tekil stage tespiti yayinlar."""

        sign = SignDetection()

        sign.class_id = 4
        sign.class_name = 'stage_05'
        sign.confidence = 0.95

        sign.bbox.x_offset = 550
        sign.bbox.y_offset = 150
        sign.bbox.width = 160
        sign.bbox.height = 180
        sign.bbox.do_rectify = False

        sign.center_px.x = 630.0
        sign.center_px.y = 240.0
        sign.center_px.z = 0.0

        sign.distance_m = 4.5
        sign.distance_valid = True

        sign.action = SignDetection.ACTION_UNKNOWN

        sign.speed_limit_mps = 0.0
        sign.speed_limit_valid = False

        self.sign_publisher.publish(sign)


def main(args=None) -> None:
    rclpy.init(args=args)

    node = InterfaceTestPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info(
            'Publisher kullanıcı tarafından durduruldu.'
        )
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
