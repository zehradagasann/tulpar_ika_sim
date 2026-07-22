#!/usr/bin/env python3
"""Nav2 uzerinden duz hat NavigateToPose testi.

Kullanim:
  ros2 launch tulpar_description gazebo.launch.py
  ros2 launch tulpar_description nav2_bringup.launch.py   (ayri terminal)
  python3 test_kanit/duz_hat_testi.py [hedef_x] [hedef_y]

Gazebo calismiyorsa 5sn icinde /odom gelmez, abort eder.
Sonuc CSV'ye yazilir, companion duz_hat_grafik.py ile cizilebilir.
"""
import csv
import sys
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy

from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu


class DuzHatTesti(Node):
    def __init__(self, hedef_x: float, hedef_y: float):
        super().__init__('duz_hat_testi')
        self.hedef_x = hedef_x
        self.hedef_y = hedef_y
        self.rows = []
        self.t0 = None
        self.son_odom = None

        qos = QoSProfile(depth=10)
        self.create_subscription(Odometry, '/odom', self._odom_cb, qos)
        self.create_subscription(Imu, '/imu', self._imu_cb, qos)
        self._son_imu = None

        self._action_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

    def _odom_cb(self, msg: Odometry):
        self.son_odom = msg
        if self.t0 is None:
            return
        pitch = self._pitch_from_imu()
        self.rows.append([
            time.time() - self.t0,
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.twist.twist.linear.x,
            msg.twist.twist.angular.z,
            pitch,
        ])

    def _imu_cb(self, msg: Imu):
        self._son_imu = msg

    def _pitch_from_imu(self):
        if self._son_imu is None:
            return 0.0
        q = self._son_imu.orientation
        # standart quaternion -> pitch (Y ekseni etrafinda donus)
        sinp = 2.0 * (q.w * q.y - q.z * q.x)
        sinp = max(-1.0, min(1.0, sinp))
        import math
        return math.asin(sinp)

    def bekle_odom(self, timeout=5.0):
        deadline = time.time() + timeout
        while rclpy.ok() and time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.son_odom is not None:
                return True
        return False

    def hedefe_git(self):
        if not self._action_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('navigate_to_pose action server bulunamadi - Nav2 calisiyor mu?')
            return False

        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = self.hedef_x
        goal.pose.pose.position.y = self.hedef_y
        goal.pose.pose.orientation.w = 1.0

        self.t0 = time.time()
        send_future = self._action_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Nav2 hedefi reddetti')
            return False

        result_future = goal_handle.get_result_async()
        deadline = time.time() + 120.0
        while rclpy.ok() and not result_future.done() and time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)

        if not result_future.done():
            self.get_logger().error('120sn icinde hedefe ulasilamadi (timeout)')
            return False

        result = result_future.result()
        basarili = result.status == 4  # GoalStatus.STATUS_SUCCEEDED
        self.get_logger().info(f'Nav2 sonuc kodu: {result.status} (4=basarili)')
        return basarili

    def csv_yaz(self, dosya='duz_hat_sonuc.csv'):
        with open(dosya, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['t_sn', 'x', 'y', 'linear_x', 'angular_z', 'pitch_rad'])
            w.writerows(self.rows)
        self.get_logger().info(f'{len(self.rows)} satir {dosya} dosyasina yazildi')


def main():
    hedef_x = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    hedef_y = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0

    rclpy.init()
    node = DuzHatTesti(hedef_x, hedef_y)

    if not node.bekle_odom():
        node.get_logger().error('/odom 5sn icinde gelmedi - Gazebo calisiyor mu kontrol et')
        node.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    basarili = node.hedefe_git()
    node.csv_yaz()
    node.get_logger().info(f'TEST {"BASARILI" if basarili else "BASARISIZ"}')

    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if basarili else 1)


if __name__ == '__main__':
    main()
