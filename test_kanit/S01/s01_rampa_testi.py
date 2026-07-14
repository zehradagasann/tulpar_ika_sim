#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import time
import csv
import pathlib

class RampaTesti(Node):
    def __init__(self):
        super().__init__('s01_rampa_testi')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.veriler = []
        self.baslangic_zamani = None
        self.baslangic_x = None
        self.faz = "ilerleme"  # ilerleme -> dur -> devam -> bitti
        self.dur_baslangic = None
        self.stop_x = 3.5  # rampa ortası
        self.bitti = False

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        z = msg.pose.pose.position.z
        roll = msg.pose.pose.orientation.x
        hiz = msg.twist.twist.linear.x
        if self.baslangic_x is None:
            self.baslangic_x = x
            self.baslangic_zamani = time.time()
        gecen = time.time() - self.baslangic_zamani
        self.veriler.append((gecen, x, z, hiz, self.faz))

        if self.faz == "ilerleme" and x >= self.stop_x:
            self.faz = "dur"
            self.dur_baslangic = time.time()
            self.get_logger().info(f'RAMPA STOP: x={x:.3f}m, z={z:.3f}m — 2 saniye bekleniyor')

        elif self.faz == "dur":
            bekleme = time.time() - self.dur_baslangic
            kayma = abs(x - self.stop_x)
            if bekleme >= 2.0:
                self.get_logger().info(f'2 saniye tamamlandi! Kayma: {kayma:.4f}m')
                if kayma < 0.05:
                    self.get_logger().info('✓ FREN TUTTU — kayma < 5cm')
                else:
                    self.get_logger().warn(f'✗ KAYMA VAR — {kayma:.4f}m')
                self.faz = "devam"
                self.get_logger().info('Rampaya devam ediliyor...')

        elif self.faz == "devam" and x >= 6.0:
            self.faz = "bitti"
            self.bitti = True
            self.get_logger().info(f'Rampa tamamlandi! Toplam sure: {gecen:.2f}s')

def main():
    rclpy.init()
    node = RampaTesti()
    node.get_logger().info('S-01 Rampa Stop Testi basliyor!')

    start = time.time()
    while rclpy.ok() and node.baslangic_x is None:
        rclpy.spin_once(node, timeout_sec=0.1)
        if time.time() - start > 5.0:
            node.get_logger().error('Odom verisi gelmedi!')
            return

    while rclpy.ok() and not node.bitti:
        msg = Twist()
        if node.faz == "dur":
            msg.linear.x = 0.0  # dur
        else:
            msg.linear.x = 0.3  # yavaş git
        node.cmd_pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.05)

    # Durdur
    node.cmd_pub.publish(Twist())

    # CSV kaydet
    with open(pathlib.Path(__file__).parent / 's01_rampa_verisi.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['zaman', 'konum_x', 'konum_z', 'hiz', 'faz'])
        for row in node.veriler:
            w.writerow([f'{row[0]:.3f}', f'{row[1]:.4f}', f'{row[2]:.4f}', f'{row[3]:.4f}', row[4]])
    node.get_logger().info(f'Veri kaydedildi: {len(node.veriler)} satir')
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
