#!/usr/bin/env python3

import cv2
import rclpy

from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class WebcamPublisher(Node):
    """USB webcam görüntüsünü ROS 2 Image mesajı olarak yayınlar."""

    def __init__(self) -> None:
        super().__init__('webcam_publisher')

        self.declare_parameter('device_index', 0)
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 20.0)

        device_index = int(
            self.get_parameter('device_index').value
        )
        width = int(self.get_parameter('width').value)
        height = int(self.get_parameter('height').value)
        fps = float(self.get_parameter('fps').value)

        self.bridge = CvBridge()

        self.publisher = self.create_publisher(
            Image,
            '/camera/front/color/image_raw',
            qos_profile_sensor_data,
        )

        self.capture = cv2.VideoCapture(device_index)

        if not self.capture.isOpened():
            raise RuntimeError(
                f'Kamera açılamadı. device_index={device_index}'
            )

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, fps)

        period = 1.0 / max(fps, 1.0)

        self.timer = self.create_timer(
            period,
            self.publish_frame,
        )

        self.get_logger().info(
            f'Webcam açıldı: index={device_index}, '
            f'{width}x{height}, {fps:.1f} FPS'
        )

    def publish_frame(self) -> None:
        success, frame = self.capture.read()

        if not success:
            self.get_logger().warning(
                'Kameradan görüntü alınamadı.'
            )
            return

        message = self.bridge.cv2_to_imgmsg(
            frame,
            encoding='bgr8',
        )

        message.header.stamp = (
            self.get_clock().now().to_msg()
        )
        message.header.frame_id = (
            'camera_front_optical_frame'
        )

        self.publisher.publish(message)

    def destroy_node(self) -> bool:
        if self.capture.isOpened():
            self.capture.release()

        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = WebcamPublisher()

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
