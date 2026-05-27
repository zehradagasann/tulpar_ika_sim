#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import time, csv

class BlokTesti(Node):
    def __init__(self):
        super().__init__('s01_blok_testi')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.veriler = []
        self.baslangic_zamani = None
        self.baslangic_x = None
        self.bitti = False
        self.max_z = 0.0
        self.blok_gecildi = False

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        z = msg.pose.pose.position.z
        hiz = msg.twist.twist.linear.x

        if self.baslangic_x is None:
            self.baslangic_x = x
            self.baslangic_zamani = time.time()

        gecen = time.time() - self.baslangic_zamani
        self.veriler.append((gecen, x, z, hiz))

        if z > self.max_z:
            self.max_z = z

        if 10.0 <= x <= 13.0:
            self.get_logger().info(f'Blok bölgesi: x={x:.2f}m, z={z:.3f}m')

        if x >= 10.5 and not self.blok_gecildi and z > 0.05:
            self.blok_gecildi = True
            self.get_logger().info(f'✓ BLOK AŞILDI: z={z:.3f}m (beklenen >0.05m)')

        if x >= 13.0 and not self.bitti:
            self.bitti = True
            self.get_logger().info(f'Blok testi tamamlandi! Max z: {self.max_z:.3f}m')
            if self.max_z > 0.05:
                self.get_logger().info('✓ BLOK GEÇİLDİ')
            else:
                self.get_logger().warn('⚠ Blok geçilemedi veya z değişmedi')

def main():
    rclpy.init()
    node = BlokTesti()
    node.get_logger().info('S-01 15cm Blok Testi basliyor!')

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

    with open('/home/talha/tulpar_ika_sim/test_kanit/S01/s01_blok_verisi.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['zaman', 'konum_x', 'konum_z', 'hiz'])
        for row in node.veriler:
            w.writerow([f'{row[0]:.3f}', f'{row[1]:.4f}', f'{row[2]:.4f}', f'{row[3]:.4f}'])

    node.get_logger().info(f'Veri kaydedildi: {len(node.veriler)} satir')
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
