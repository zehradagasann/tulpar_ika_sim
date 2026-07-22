"""/cmd_vel_yon_duzeltmeli + /imu -> /cmd_vel_final (geometry_msgs/Twist).

KTR 3.3.3: "dik engelde TEB dik yaklasim rotasi uretir ve pitch feedforward
ile yuksek tork uygular." Ileri gidilirken (linear.x > 0) IMU pitch acisi bir
esigi asarsa (tirmanis), linear.x'e egimle orantili kucuk bir takviye
eklenir - sadece feedforward, kapali-cevrim tork/akim geri beslemesi yok
(gercek motor katmaninda [Teensy/gaz karti] boyle bir geri besleme zaten
mevcut degil, bkz. firmware/tulpar_teensy).

** ONEMLI - ISARET YONU HENUZ CANLI DOGRULANMADI **
Standart quaternion->pitch formulu kullanildi (asin(2*(w*y - z*x))) ama
"tirmanirken pitch pozitif mi negatif mi cikiyor" sim'de gercek rampada
(worlds/sim_world.sdf 'dik_egim') suruculerek DOGRULANMADI - Gazebo GUI'nin
render sorunu yuzunden bu oturumda canli test ertelendi (bkz. sohbet).
Roadmap'in kendi notu da ayni riski isaret ediyor: "Zehra'ya pitch isaret
konvansiyonunu sor, ters isaret hatasi riski var." PITCH_YONU_TERS
parametresi bu yuzden eklendi - test_kanit/duz_hat_testi.py ile rampaya
surulup CSV'deki pitch_rad sutunu izlenerek dogru yon netlesince (ya da
Zehra/gercek WT901C surucusunden gelen isaretle karsilastirilinca)
gerekirse True yapilsin. Bu dogrulama TAMAMLANMADAN gercek donanimda/AKV'de
guvenilmemeli.
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu


def _pitch_from_quaternion(q) -> float:
    sinp = 2.0 * (q.w * q.y - q.z * q.x)
    sinp = max(-1.0, min(1.0, sinp))
    return math.asin(sinp)


class EgimFeedforwardNode(Node):

    def __init__(self):
        super().__init__('egim_feedforward_node')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel_yon_duzeltmeli')
        self.declare_parameter('output_topic', '/cmd_vel_final')
        self.declare_parameter('imu_topic', '/imu')
        self.declare_parameter('egim_esik_rad', 0.08)  # ~4.6 derece altinda tetiklenmez
        self.declare_parameter('kp_egim_takviye', 0.6)
        self.declare_parameter('max_takviye_m_s', 0.3)
        self.declare_parameter('max_linear_velocity', 1.0)  # DiffDrive plugin ile senkron
        self.declare_parameter('pitch_yonu_ters', False)  # bkz. modul dokstring'i

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.output_topic = self.get_parameter('output_topic').value
        self.imu_topic = self.get_parameter('imu_topic').value
        self.egim_esik = self.get_parameter('egim_esik_rad').value
        self.kp = self.get_parameter('kp_egim_takviye').value
        self.max_takviye = self.get_parameter('max_takviye_m_s').value
        self.max_linear = self.get_parameter('max_linear_velocity').value
        self.ters = self.get_parameter('pitch_yonu_ters').value

        self._son_pitch = 0.0
        self._imu_geldi = False

        qos = QoSProfile(depth=10)
        self.create_subscription(Imu, self.imu_topic, self._imu_cb, qos)
        self.create_subscription(Twist, self.cmd_vel_topic, self._cmd_vel_cb, qos)
        self.pub = self.create_publisher(Twist, self.output_topic, qos)

        self.get_logger().info(
            f'egim_feedforward_node basladi: {self.cmd_vel_topic} + {self.imu_topic} '
            f'-> {self.output_topic} (esik={self.egim_esik} rad, kp={self.kp}, '
            f'pitch_yonu_ters={self.ters})'
        )

    def _imu_cb(self, msg: Imu):
        pitch = _pitch_from_quaternion(msg.orientation)
        self._son_pitch = -pitch if self.ters else pitch
        self._imu_geldi = True

    def _cmd_vel_cb(self, msg: Twist):
        out = Twist()
        out.linear.y = msg.linear.y
        out.linear.z = msg.linear.z
        out.angular = msg.angular

        linear_x = msg.linear.x
        if linear_x > 0.0 and self._imu_geldi and self._son_pitch > self.egim_esik:
            takviye = self.kp * self._son_pitch
            takviye = min(takviye, self.max_takviye)
            linear_x = min(linear_x + takviye, self.max_linear)

        out.linear.x = linear_x
        self.pub.publish(out)


def main():
    rclpy.init()
    node = EgimFeedforwardNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
