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
        self.baslangic = None
        self.bitti = False

    def odom_callback(self, msg):
        if self.baslangic is None:
            self.baslangic = time.time()
        gecen = time.time() - self.baslangic
        x = msg.pose.pose.position.x
        hiz = msg.twist.twist.linear.x
        self.veriler.append((gecen, x, hiz))
        # 30 metreyi geçince dur
        if x >= 30.0 and not self.bitti:
            self.bitti = True
            self.get_logger().info(f'30 metre tamamlandı! Süre: {gecen:.2f} s')

    def komut_gonder(self):
        msg = Twist()
        msg.linear.x = 0.5
        self.cmd_pub.publish(msg)

def main():
    rclpy.init()
    node = HizlanmaTesti()
    node.get_logger().info('E-02 Hızlanma testi başladı - 0.5 m/s')

    while rclpy.ok() and not node.bitti:
        node.komut_gonder()
        rclpy.spin_once(node, timeout_sec=0.05)

    # Aracı durdur
    dur = Twist()
    node.cmd_pub.publish(dur)
    node.get_logger().info('Test tamamlandı, araç durduruldu')

    # Verileri dosyaya yaz
    with open('/home/talha/tulpar_ika_sim/test_kanit/E02/hizlanma_verisi.csv', 'w') as f:
        f.write('zaman,konum_x,hiz\n')
        for t, x, v in node.veriler:
            f.write(f'{t:.3f},{x:.4f},{v:.4f}\n')

    node.get_logger().info(f'Veri kaydedildi: {len(node.veriler)} satır')
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()