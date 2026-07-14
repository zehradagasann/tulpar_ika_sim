#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import time
import csv
import math
import pathlib

class YanEgimTesti(Node):
    def __init__(self):
        super().__init__('s01_yan_egim_testi')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.veriler = []
        self.baslangic_zamani = None
        self.baslangic_x = None
        self.bitti = False
        self.max_roll = 0.0
        self.devrildi = False

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        # Quaternion'dan roll hesapla
        qx = msg.pose.pose.orientation.x
        qy = msg.pose.pose.orientation.y
        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w
        roll = math.atan2(2*(qw*qx + qy*qz), 1 - 2*(qx*qx + qy*qy))
        roll_deg = math.degrees(roll)

        if self.baslangic_x is None:
            self.baslangic_x = x
            self.baslangic_zamani = time.time()

        gecen = time.time() - self.baslangic_zamani
        self.veriler.append((gecen, x, roll_deg))

        if abs(roll_deg) > self.max_roll:
            self.max_roll = abs(roll_deg)

        if abs(roll_deg) > 45.0:
            self.devrildi = True
            self.bitti = True
            self.get_logger().error(f'ARAÇ DEVRİLDİ! roll={roll_deg:.1f}°')

        if 6.0 <= x <= 10.0:
            self.get_logger().info(f'Yan eğimde: x={x:.2f}m, roll={roll_deg:.2f}°')

        if x >= 12.0 and not self.bitti:
            self.bitti = True
            self.get_logger().info(f'Yan eğim geçildi! Max roll: {self.max_roll:.2f}°')
            if self.max_roll < 20.0:
                self.get_logger().info('✓ STABIL — devrilmedi')
            else:
                self.get_logger().warn(f'⚠ Yüksek roll açısı: {self.max_roll:.2f}°')

def main():
    rclpy.init()
    node = YanEgimTesti()
    node.get_logger().info('S-01 Yan Egim Testi basliyor!')

    start = time.time()
    while rclpy.ok() and node.baslangic_x is None:
        rclpy.spin_once(node, timeout_sec=0.1)
        if time.time() - start > 5.0:
            node.get_logger().error('Odom verisi gelmedi!')
            return

    while rclpy.ok() and not node.bitti:
        msg = Twist()
        msg.linear.x = 0.3
        node.cmd_pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.05)

    node.cmd_pub.publish(Twist())

    with open(pathlib.Path(__file__).parent / 's01_yan_egim_verisi.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['zaman', 'konum_x', 'roll_derece'])
        for row in node.veriler:
            w.writerow([f'{row[0]:.3f}', f'{row[1]:.4f}', f'{row[2]:.4f}'])

    node.get_logger().info(f'Veri kaydedildi: {len(node.veriler)} satir')
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
