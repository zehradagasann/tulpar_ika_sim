"""/tulpar_kamera/taret_pid + /tulpar_kamera/atis_event -> Teensy seri komutlari.

Emin'in kamera_node.py'sindeki PID (pan/tilt, hedef pikselinin hatasindan
hesaplaniyor) su an SADECE log'a yaziyordu, hicbir yere yayinlanmiyordu -
bu node onun disariya vermesi planlanan TaretPid.msg'i (taslak, 22 Temmuz
2026) dinleyip Teensy firmware'inin (firmware/tulpar_teensy) serial komut
arayuzune (TP/TT/S1/S0/L1/L0) cevirir.

Guvenlik: ates etme SADECE /tulpar_kamera/atis_event'in ACTION_LOCK_STABLE
event'iyle tetiklenir (Emin'in dwell_seconds ile zaten "N kare boyunca
kilitli kaldi" dogrulamasi yapilmis event'i) - /tulpar_kamera/taret_pid
tek basina asla ates etmez, sadece pan/tilt konumlandirir. Ates dizisi
S1 (silahlandir) -> L1 (ates) -> atis_puls_sure_sn bekle -> L0+S0 (guvenli
kapat). ACTION_EXIT_SHOOTING_ZONE / ACTION_TARGET_LOST geldiginde, bekleyen
bir ates dizisi olsa bile ANINDA L0+S0 gonderilir (abort) - bkz.
firmware/tulpar_teensy/src/LazerKatmani.h'deki ara kilit notu, bu node o
ara kilidin Jetson tarafindaki tek gecerli tetikleyicisidir.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from tulpar_ika_msgs.msg import AtisEvent, TaretPid

from tulpar_turret_bridge.seri_port import GercekSeriPort


def _kirp(deger: float, sinir: float) -> float:
    return max(-sinir, min(sinir, deger))


class TurretBridge(Node):

    def __init__(self, seri_port=None):
        super().__init__('turret_bridge')

        self.declare_parameter('seri_port_adi', '/dev/ttyACM0')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('pan_limit_derece', 90.0)
        self.declare_parameter('tilt_limit_derece', 90.0)
        self.declare_parameter('atis_puls_sure_sn', 0.2)
        self.declare_parameter('taret_pid_topic', '/tulpar_kamera/taret_pid')
        self.declare_parameter('atis_event_topic', '/tulpar_kamera/atis_event')

        self.pan_limit = self.get_parameter('pan_limit_derece').value
        self.tilt_limit = self.get_parameter('tilt_limit_derece').value
        self.atis_puls_sure_sn = self.get_parameter('atis_puls_sure_sn').value

        self.pan_acisi = 0.0
        self.tilt_acisi = 0.0
        self._ates_zamanlayici = None

        if seri_port is not None:
            self.seri = seri_port
        else:
            self.seri = GercekSeriPort(
                self.get_parameter('seri_port_adi').value,
                self.get_parameter('baud').value,
            )

        pid_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.create_subscription(
            TaretPid, self.get_parameter('taret_pid_topic').value,
            self._pid_callback, pid_qos,
        )

        atis_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )
        self.create_subscription(
            AtisEvent, self.get_parameter('atis_event_topic').value,
            self._atis_event_callback, atis_qos,
        )

        self.get_logger().info(
            f"turret_bridge basladi: pan/tilt limit=±{self.pan_limit}°, "
            f"atis pulse={self.atis_puls_sure_sn}s"
        )

    def _pid_callback(self, msg: TaretPid) -> None:
        if not msg.hedef_var:
            return  # PID Emin tarafinda resetlendi, delta anlamsiz - konumu koru

        self.pan_acisi = _kirp(self.pan_acisi + msg.pan_derece, self.pan_limit)
        self.tilt_acisi = _kirp(self.tilt_acisi + msg.tilt_derece, self.tilt_limit)

        self.seri.yaz(f"TP {self.pan_acisi:.2f}")
        self.seri.yaz(f"TT {self.tilt_acisi:.2f}")

    def _atis_event_callback(self, msg: AtisEvent) -> None:
        if msg.action == AtisEvent.ACTION_LOCK_STABLE:
            self._ates_baslat()
        elif msg.action in (AtisEvent.ACTION_EXIT_SHOOTING_ZONE,
                             AtisEvent.ACTION_TARGET_LOST):
            self._acil_guvenli_kapat()

    def _ates_baslat(self) -> None:
        if self._ates_zamanlayici is not None:
            return  # zaten devam eden bir ates dizisi var, tekrar tetikleme
        self.seri.yaz("S1")
        self.seri.yaz("L1")
        self._ates_zamanlayici = self.create_timer(
            self.atis_puls_sure_sn, self._ates_bitir)

    def _ates_bitir(self) -> None:
        self.seri.yaz("L0")
        self.seri.yaz("S0")
        if self._ates_zamanlayici is not None:
            self._ates_zamanlayici.cancel()
            self._ates_zamanlayici = None

    def _acil_guvenli_kapat(self) -> None:
        self.seri.yaz("L0")
        self.seri.yaz("S0")
        if self._ates_zamanlayici is not None:
            self._ates_zamanlayici.cancel()
            self._ates_zamanlayici = None


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TurretBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
