"""/cmd_vel_final + /imu -> /cmd_vel_guvenli + /guvenlik/asiri_egim.

KTR 3.3.3: "egim acisi asimetrik tork komutlarini yonetir, EKF yanal kaymayi
engeller, esik asilirsa BT araci durdurur."

Bu node roadmap'teki gorev ikiye ayrildi:
  - "esik-asimi sinyali" + "BT'yi durdurma" TARAFI: burada, kendi basina.
    Zehra'nin ayri bir imu_motion_monitor.py / tilt_critical sinyali
    yazmasi planlanmisti (bkz. talha_yol_haritasi_v2.md Gun 7, madde 8) ama
    bu repoda hic yok (21 Temmuz 2026 itibariyle kontrol edildi) - bu yuzden
    kendi IMU'sunu dogrudan okuyan bir taslak yazildi (bu projede daha once
    de yapilan pattern: bkz. slalom_hedef_bridge_node.py). Zehra'nin gercek
    modulu gelince, ya bu node onun sinyaline abone olacak sekilde
    guncellenir ya da ikisi birlestirilir.
  - "asimetrik tork" TARAFI: BUNU YAPMIYORUZ. Gazebo'nun DiffDrive plugin'i
    komut-bazli per-teker tork kontrolu desteklemiyor (sadece topluca bir
    max_wheel_torque limiti var, SDF'de sabit) - bu yuzden sim'de anlamli
    simule edilemez. Gercek asimetrik tork, gercek Teensy/gaz karti motor
    katmani (setGaz per kanal) gelmeden yazilamaz/test edilemez. Bu, bu
    dosyanin bilerek KAPSAM DISI biraktigi kisim.

Guvenlik davranisi: |roll| kritik esigi asarsa /cmd_vel_final oldugu gibi
gecirilmez, sifirlanir (collision_checker_node'daki "hizi sifirla" deseniyle
ayni) - araç fiziksel olarak durur, BT'nin kendi ic durumu ne olursa olsun.
Ayrica /guvenlik/asiri_egim (std_msgs/Bool) yayinlanir - ileride tulpar_bt
tarafindan bir Condition node ile dinlenip agaci da resmi olarak durdurmak
icin kullanilabilir (bu oturumda BT.CPP tarafina dokunulmadi).
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from std_msgs.msg import Bool


def _roll_from_quaternion(q) -> float:
    sinr_cosp = 2.0 * (q.w * q.x + q.y * q.z)
    cosr_cosp = 1.0 - 2.0 * (q.x * q.x + q.y * q.y)
    return math.atan2(sinr_cosp, cosr_cosp)


class YanEgimIzlemeNode(Node):

    def __init__(self):
        super().__init__('yan_egim_izleme_node')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel_final')
        self.declare_parameter('output_topic', '/cmd_vel_guvenli')
        self.declare_parameter('imu_topic', '/imu')
        self.declare_parameter('asiri_egim_topic', '/guvenlik/asiri_egim')
        self.declare_parameter('kritik_roll_rad', 0.35)  # ~20 derece, devrilme riski
        self.declare_parameter('kritik_roll_kapanma_rad', 0.26)  # ~15 derece, hysteresis

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.output_topic = self.get_parameter('output_topic').value
        self.imu_topic = self.get_parameter('imu_topic').value
        self.asiri_egim_topic = self.get_parameter('asiri_egim_topic').value
        self.kritik_roll = self.get_parameter('kritik_roll_rad').value
        self.kapanma_roll = self.get_parameter('kritik_roll_kapanma_rad').value

        self._asiri_egim = False

        qos = QoSProfile(depth=10)
        self.create_subscription(Imu, self.imu_topic, self._imu_cb, qos)
        self.create_subscription(Twist, self.cmd_vel_topic, self._cmd_vel_cb, qos)
        self.pub_cmd = self.create_publisher(Twist, self.output_topic, qos)
        self.pub_flag = self.create_publisher(Bool, self.asiri_egim_topic, qos)

        self.get_logger().info(
            f'yan_egim_izleme_node basladi: kritik_roll={self.kritik_roll} rad '
            f'(~{math.degrees(self.kritik_roll):.1f} derece)'
        )

    def _imu_cb(self, msg: Imu):
        roll = _roll_from_quaternion(msg.orientation)
        onceki = self._asiri_egim
        # hysteresis: kritik esikte tetiklenir, daha dusuk bir esikte kapanir -
        # esik sinirinda titremeyi (flapping) onlemek icin
        if not self._asiri_egim and abs(roll) > self.kritik_roll:
            self._asiri_egim = True
        elif self._asiri_egim and abs(roll) < self.kapanma_roll:
            self._asiri_egim = False

        if self._asiri_egim != onceki:
            self.pub_flag.publish(Bool(data=self._asiri_egim))
            if self._asiri_egim:
                self.get_logger().warn(
                    f'ASIRI YAN EGIM: roll={math.degrees(roll):.1f} derece - '
                    f'cmd_vel_guvenli sifirlaniyor'
                )
            else:
                self.get_logger().info('Yan egim normale dondu, komutlar tekrar geciyor')

    def _cmd_vel_cb(self, msg: Twist):
        out = Twist() if self._asiri_egim else msg
        self.pub_cmd.publish(out)


def main():
    rclpy.init()
    node = YanEgimIzlemeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
