#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import time

class HizlanmaTesti(Node):
    def __init__(self):
        super().__init__('e02_hizlanma_testi')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.veriler = []
        self.baslangic_zamani = None
        self.baslangic_x = None
        self.bitti = False

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        hiz = msg.twist.twist.linear.x
        if self.baslangic_x is None:
            self.baslangic_x = x
            self.baslangic_zamani = time.time()
            self.get_logger().info(f'Baslangic pozisyonu: {x:.3f} m')
        gecen = time.time() - self.baslangic_zamani
        mesafe = x - self.baslangic_x
        self.veriler.append((gecen, mesafe, hiz))
        if mesafe >= 30.0 and not self.bitti:
            self.bitti = True
            self.get_logger().info(f'30 metre tamamlandi! Sure: {gecen:.2f} s')

    def komut_gonder(self):
        msg = Twist()
        msg.linear.x = 0.5
        self.cmd_pub.publish(msg)

def main():
    rclpy.init()
    node = HizlanmaTesti()
    node.get_logger().info('E-02 Hizlanma testi basladi - Hedef: 30m @ 0.5 m/s')
    start = time.time()
    while rclpy.ok() and node.baslangic_x is None:
        rclpy.spin_once(node, timeout_sec=0.1)
        if time.time() - start > 5.0:
            node.get_logger().error('Odom verisi gelmedi!')
            return
    node.get_logger().info('Odom alindi, test basliyor...')
    while rclpy.ok() and not node.bitti:
        node.komut_gonder()
        rclpy.spin_once(node, timeout_sec=0.05)
    dur = Twist()
    node.cmd_pub.publish(dur)
    node.get_logger().info('Arac durduruldu.')
    with open('/home/talha/tulpar_ika_sim/test_kanit/E02/hizlanma_verisi.csv', 'w') as f:
        f.write('zaman,mesafe,hiz\n')
        for t, m, v in node.veriler:
            f.write(f'{t:.3f},{m:.4f},{v:.4f}\n')
    node.get_logger().info(f'Veri kaydedildi: {len(node.veriler)} satir')
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()