"""Konsol icin 5Hz heartbeat + olay gunlugu (SQLite).

Sozlesme (19 Temmuz 2026, Emin'in onayladigi filtre kurallari + kendi
onerisi):
  - /sign_detected (tulpar_ika_msgs/SignDetectionArray): action !=
    ACTION_UNKNOWN olan tespitler loglanir (BT'nin de dinledigi anlamli
    tabela event'leriyle ayni kume). Ayni class_id icin ardisik frame'lerde
    tekrar tekrar loglamayi engellemek icin class_id basina debounce_sec
    (varsayilan 2.0s) uygulanir.
  - /detections (tulpar_ika_msgs/Detection2DArray): sadece shooting_target/
    traffic_cone siniflari, "ilk gorulme" mantigiyla (track_id_valid ise
    track_id bazinda, degilse class_name bazinda zaman-debounce ile).
  - /tulpar_bt/atis_event (std_msgs/Header, tulpar_bt/AtisYap SUCCESS
    olduguna - simulate_mode dahil - yayinlar): Emin'in onerisi uzerine
    "atis ani" ayri bir event olarak loglanir (Gun 13'teki reaksiyon suresi
    metrikleri icin, bkz. talha_yol_haritasi).

BEKLENEN, HENUZ GERCEK OLMAYAN VERI: Emin'in TensorRT export'u ve
pid_target_tracking.py duzeltmesi bitene kadar /detections//sign_detected
gercekte akmiyor - bu node sahte (ros2 topic pub) veriyle test edildi,
gercek kamera/model entegrasyonu ayri bir dogrulama adimi olarak kalir.
"""

import os
import sqlite3
import time
from datetime import datetime, timezone

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from std_msgs.msg import Header
from tulpar_ika_msgs.msg import Detection2DArray, SignDetectionArray, SignDetection

CONE_TARGET_CLASSES = ('shooting_target', 'traffic_cone')


class OlayGunlugu(Node):

    def __init__(self):
        super().__init__('olay_gunlugu')

        self.declare_parameter('db_path', os.path.expanduser('~/.tulpar_ika/olay_gunlugu.db'))
        self.declare_parameter('heartbeat_hz', 5.0)
        self.declare_parameter('sign_topic', '/sign_detected')
        self.declare_parameter('detections_topic', '/detections')
        self.declare_parameter('atis_event_topic', '/tulpar_bt/atis_event')
        self.declare_parameter('heartbeat_topic', '/konsol/heartbeat')
        self.declare_parameter('sign_debounce_sec', 2.0)
        self.declare_parameter('detection_debounce_sec', 2.0)

        self.sign_debounce_sec = self.get_parameter('sign_debounce_sec').value
        self.detection_debounce_sec = self.get_parameter('detection_debounce_sec').value

        self._son_sign_log = {}       # class_id -> son loglanma zamani (monotonic)
        self._son_detection_log = {}  # track_id ya da class_name -> son loglanma zamani
        self._gorulen_track_id = set()

        db_path = self.get_parameter('db_path').value
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS olaylar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zaman_damgasi TEXT NOT NULL,
                kaynak_topic TEXT NOT NULL,
                class_id INTEGER,
                class_name TEXT,
                action INTEGER,
                confidence REAL,
                mesafe_m REAL
            )
            """
        )
        self.db.commit()

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.create_subscription(
            SignDetectionArray,
            self.get_parameter('sign_topic').value,
            self._sign_callback,
            qos,
        )
        self.create_subscription(
            Detection2DArray,
            self.get_parameter('detections_topic').value,
            self._detections_callback,
            qos,
        )
        self.create_subscription(
            Header,
            self.get_parameter('atis_event_topic').value,
            self._atis_event_callback,
            qos,
        )

        self.heartbeat_pub = self.create_publisher(
            Header, self.get_parameter('heartbeat_topic').value, qos)
        heartbeat_hz = self.get_parameter('heartbeat_hz').value
        self.create_timer(1.0 / heartbeat_hz, self._heartbeat_tick)

        self.get_logger().info(
            f"olay_gunlugu basladi: db={db_path}, "
            f"heartbeat {heartbeat_hz}Hz ({self.get_parameter('heartbeat_topic').value})"
        )

    def _heartbeat_tick(self):
        msg = Header()
        msg.stamp = self.get_clock().now().to_msg()
        self.heartbeat_pub.publish(msg)

    def _kaydet(self, kaynak_topic, class_id=None, class_name=None,
                action=None, confidence=None, mesafe_m=None):
        self.db.execute(
            "INSERT INTO olaylar "
            "(zaman_damgasi, kaynak_topic, class_id, class_name, action, "
            "confidence, mesafe_m) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                kaynak_topic, class_id, class_name, action, confidence, mesafe_m,
            ),
        )
        self.db.commit()
        self.get_logger().info(
            f"olay kaydedildi: {kaynak_topic} class_name={class_name} action={action}"
        )

    def _sign_callback(self, msg: SignDetectionArray):
        now = time.monotonic()
        for det in msg.detections:
            if det.action == SignDetection.ACTION_UNKNOWN:
                continue
            son = self._son_sign_log.get(det.class_id)
            if son is not None and (now - son) < self.sign_debounce_sec:
                continue
            self._son_sign_log[det.class_id] = now
            self._kaydet(
                '/sign_detected',
                class_id=det.class_id,
                class_name=det.class_name,
                action=det.action,
                confidence=det.confidence,
                mesafe_m=det.distance_m if det.distance_valid else None,
            )

    def _detections_callback(self, msg: Detection2DArray):
        now = time.monotonic()
        for det in msg.detections:
            if det.class_name not in CONE_TARGET_CLASSES:
                continue

            if det.track_id_valid:
                key = ('track', det.track_id)
                if key in self._gorulen_track_id:
                    continue
                self._gorulen_track_id.add(key)
            else:
                key = ('class', det.class_name)
                son = self._son_detection_log.get(key)
                if son is not None and (now - son) < self.detection_debounce_sec:
                    continue
                self._son_detection_log[key] = now

            self._kaydet(
                '/detections',
                class_id=det.class_id,
                class_name=det.class_name,
                confidence=det.confidence,
                mesafe_m=det.depth_m if det.depth_valid else None,
            )

    def _atis_event_callback(self, msg: Header):
        self._kaydet('/tulpar_bt/atis_event', class_name='ATIS_ANI')


def main(args=None):
    rclpy.init(args=args)
    node = OlayGunlugu()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
