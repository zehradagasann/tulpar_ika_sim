"""/cmd_vel_safe + /imu -> /cmd_vel_compensated (geometry_msgs/Twist).

KTR 3.3.3: "WT901B IMU feedforward girisi yon sapmasini ve patinaji bastirir."
Duz-hat surusu komutlanmisken (angular.z komut degeri ~0, orn. hizlanma
parkuru E-02) IMU'nun olcumledigi gercek yaw-rate sifirdan sapiyorsa (patinaj/
yon sapmasi), bu sapmayi sifirlamaya calisan kucuk bir duzeltici acisal hiz
terimi komuta eklenir. Donus komutlanmisken (angular.z buyukse) duzeltme
devreye girmez - kasitli donusu "hata" sanip bastirmamak icin.

Bu bir P-kontrolcu (sadece oransal, integral yok - surekli sifir olmayan bir
IMU bias'i varsa kucuk bir kalici sapma birakabilir, bu bilerek boyle -
entegral terimi patinaj gibi ani/degisken bir bozucu icin windup riski tasir).
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu


class YonDuzeltmeNode(Node):

    def __init__(self):
        super().__init__('yon_duzeltme_node')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel_safe')
        self.declare_parameter('output_topic', '/cmd_vel_yon_duzeltmeli')
        self.declare_parameter('imu_topic', '/imu')
        self.declare_parameter('duz_hat_esik_rad_s', 0.05)  # bunun altindaki
        # komutlanan angular.z "duz git" sayilir, duzeltme devreye girer
        self.declare_parameter('kp_yon_duzeltme', 0.5)
        self.declare_parameter('max_duzeltme_rad_s', 0.3)

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.output_topic = self.get_parameter('output_topic').value
        self.imu_topic = self.get_parameter('imu_topic').value
        self.duz_hat_esik = self.get_parameter('duz_hat_esik_rad_s').value
        self.kp = self.get_parameter('kp_yon_duzeltme').value
        self.max_duzeltme = self.get_parameter('max_duzeltme_rad_s').value

        self._son_yaw_rate = 0.0
        self._imu_geldi = False

        qos = QoSProfile(depth=10)
        self.create_subscription(Imu, self.imu_topic, self._imu_cb, qos)
        self.create_subscription(Twist, self.cmd_vel_topic, self._cmd_vel_cb, qos)
        self.pub = self.create_publisher(Twist, self.output_topic, qos)

        self.get_logger().info(
            f'yon_duzeltme_node basladi: {self.cmd_vel_topic} + {self.imu_topic} '
            f'-> {self.output_topic} (esik={self.duz_hat_esik} rad/s, kp={self.kp})'
        )

    def _imu_cb(self, msg: Imu):
        self._son_yaw_rate = msg.angular_velocity.z
        self._imu_geldi = True

    def _cmd_vel_cb(self, msg: Twist):
        out = Twist()
        out.linear = msg.linear
        out.angular.x = msg.angular.x
        out.angular.y = msg.angular.y

        duz_gidiyor = abs(msg.angular.z) < self.duz_hat_esik
        if duz_gidiyor and self._imu_geldi:
            # Gercek yaw-rate sifirdan sapmissa (patinaj/surukleme), onu
            # sifirlamaya calisan zit yonlu bir duzeltme ekle.
            duzeltme = -self.kp * self._son_yaw_rate
            duzeltme = max(-self.max_duzeltme, min(self.max_duzeltme, duzeltme))
            out.angular.z = msg.angular.z + duzeltme
        else:
            out.angular.z = msg.angular.z

        self.pub.publish(out)


def main():
    rclpy.init()
    node = YonDuzeltmeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
