#!/usr/bin/env python3
"""
detection_publisher.py -- Tulpar IKA perception -> ROS2 koprusu.

/detections           tulpar_ika_msgs/Detection2DArray  (BEST_EFFORT, depth 1)
/tulpar_bt/atis_event tulpar_ika_msgs/AtisEvent          (RELIABLE + TRANSIENT_LOCAL)

MIMARI: Bu bir ROS2 node dosyasi DEGIL, tulpar_kamera_node.py process'inin
icinde calisan modul. Argus boot basina bir kez aciliyor; ayri node ikinci
oturum acip dmabuf_fd -1 ile patlardi. rclpy kendi thread'inde spin eder.

SEMA: Zehra'nin mevcut tulpar_ika_msgs/Detection2D semasi kullaniliyor
(ekip standardi). Atisa ozel turetilmis alanlar (merkez hatasi, atis-bolgesi
bayragi) Detection2D'de YOK; tuketici center_px'ten kendi hesaplar. Atis
mantigi /tulpar_bt/atis_event'te.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

__all__ = ["Det", "DetectionPublisher"]


@dataclass
class Det:
    """YOLO tarafinin urettigi notr yapi. ROS'a bagimli degil."""
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    track_id: int = 0
    depth_m: float = 0.0          # RealSense derinligi; 0 => gecersiz
    depth_valid: bool = False

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) * 0.5, (self.y1 + self.y2) * 0.5)

    @property
    def size(self) -> Tuple[float, float]:
        return (abs(self.x2 - self.x1), abs(self.y2 - self.y1))


class _NullPublisher:
    ok = False
    def publish(self, *_a, **_kw): return None
    def shutdown(self): pass


class DetectionPublisher:
    ok = True

    def __new__(cls, enabled: bool = True, **kwargs):
        if not enabled:
            return _NullPublisher()
        return super().__new__(cls)

    def __init__(
        self,
        enabled: bool = True,
        node_name: str = "tulpar_kamera_perception",
        frame_id: str = "d435if_color_optical_frame",
        detections_topic: str = "/detections",
        atis_topic: str = "/tulpar_bt/atis_event",
        shooting_zone: Tuple[float, float] = (0.25, 0.25),
        min_confidence_for_event: float = 0.55,
        lock_stable_frames: int = 15,
        target_lost_frames: int = 10,
        logger=None,
    ) -> None:
        if not enabled:
            return

        import rclpy
        from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                               ReliabilityPolicy)
        from tulpar_ika_msgs.msg import AtisEvent, Detection2D, Detection2DArray

        self._rclpy = rclpy
        self._AtisEvent = AtisEvent
        self._Detection2D = Detection2D
        self._Detection2DArray = Detection2DArray

        self._frame_id = frame_id
        self._zone_w, self._zone_h = shooting_zone
        self._min_conf_event = min_confidence_for_event
        self._lock_stable_frames = lock_stable_frames
        self._target_lost_frames = target_lost_frames
        self._log = logger

        self._zone_streak = 0
        self._zone_entered_at = None
        self._lock_announced = False
        self._empty_streak = 0
        self._had_target = False
        self._in_zone_state = False

        if not rclpy.ok():
            rclpy.init(args=None)
            self._owns_context = True
        else:
            self._owns_context = False

        self._node = rclpy.create_node(node_name)

        fast = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=1,
                          reliability=ReliabilityPolicy.BEST_EFFORT,
                          durability=DurabilityPolicy.VOLATILE)
        sticky = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=5,
                            reliability=ReliabilityPolicy.RELIABLE,
                            durability=DurabilityPolicy.TRANSIENT_LOCAL)

        self._pub_det = self._node.create_publisher(Detection2DArray, detections_topic, fast)
        self._pub_evt = self._node.create_publisher(AtisEvent, atis_topic, sticky)

        # Detection2D.source = SOURCE_YOLO. Sabit runtime'da okunur ki
        # Zehra sema degeri degistirirse burasi otomatik uyumlu kalsin.
        self._SOURCE_YOLO = getattr(Detection2D, "SOURCE_YOLO", 2)

        self._executor = rclpy.executors.SingleThreadedExecutor()
        self._executor.add_node(self._node)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, name="rclpy-spin", daemon=True)
        self._thread.start()
        self._info(f"ROS2 yayini acik: {detections_topic} (Detection2DArray/best_effort), "
                   f"{atis_topic} (AtisEvent/reliable)")

    def _info(self, msg: str) -> None:
        if self._log is not None:
            self._log.info(msg)
        else:
            print(f"[ros] {msg}", flush=True)

    def _spin(self) -> None:
        try:
            while not self._stop.is_set() and self._rclpy.ok():
                self._executor.spin_once(timeout_sec=0.1)
        except Exception:   # ExternalShutdownException dahil - kapanista sessiz
            pass

    def _stamp(self, capture_time_ns):
        if capture_time_ns is None:
            return self._node.get_clock().now().to_msg()
        from builtin_interfaces.msg import Time
        t = Time()
        t.sec = int(capture_time_ns // 1_000_000_000)
        t.nanosec = int(capture_time_ns % 1_000_000_000)
        return t

    def publish(self, detections: Sequence[Det], image_size: Tuple[int, int],
                capture_time_ns: Optional[int] = None,
                inference_ms: float = 0.0) -> Optional[Det]:
        """Detection2DArray yayinlar, merkeze en yakin/guvenilir Det'i dondurur."""
        w, h = image_size
        stamp = self._stamp(capture_time_ns)

        arr = self._Detection2DArray()
        arr.header.stamp = stamp
        arr.header.frame_id = self._frame_id
        arr.image_width = int(w)
        arr.image_height = int(h)

        primary = None
        primary_score = -1.0

        for d in detections:
            cx, cy = d.center
            bw, bh = d.size
            ex = (cx - w * 0.5) / (w * 0.5)
            ey = (cy - h * 0.5) / (h * 0.5)

            m = self._Detection2D()
            m.class_id = int(d.class_id)
            m.class_name = str(d.class_name)
            m.confidence = float(d.confidence)
            # sensor_msgs/RegionOfInterest: piksel, tam sayi
            m.bbox.x_offset = max(0, int(round(d.x1)))
            m.bbox.y_offset = max(0, int(round(d.y1)))
            m.bbox.width = int(round(bw))
            m.bbox.height = int(round(bh))
            m.bbox.do_rectify = False
            m.center_px.x = float(cx)
            m.center_px.y = float(cy)
            m.center_px.z = 0.0
            m.depth_m = float(d.depth_m)
            m.depth_valid = bool(d.depth_valid)
            m.track_id = int(d.track_id)
            m.track_id_valid = bool(d.track_id > 0)
            m.source = self._SOURCE_YOLO
            arr.detections.append(m)

            score = d.confidence * (1.0 - min(1.0, math.hypot(ex, ey) / math.sqrt(2)))
            if score > primary_score:
                primary_score, primary = score, d

        self._pub_det.publish(arr)
        self._update_events(detections, image_size, stamp)
        return primary

    def _in_zone(self, d: Det, image_size) -> bool:
        w, h = image_size
        cx, cy = d.center
        ex = (cx - w * 0.5) / (w * 0.5)
        ey = (cy - h * 0.5) / (h * 0.5)
        return abs(ex) <= self._zone_w and abs(ey) <= self._zone_h

    def _update_events(self, detections, image_size, stamp) -> None:
        A = self._AtisEvent

        if not detections:
            self._empty_streak += 1
            self._zone_streak = 0
            if self._in_zone_state:
                self._emit(A.ACTION_EXIT_SHOOTING_ZONE, None, stamp)
                self._in_zone_state = False
                self._lock_announced = False
            if self._had_target and self._empty_streak >= self._target_lost_frames:
                self._emit(A.ACTION_TARGET_LOST, None, stamp)
                self._had_target = False
            return

        self._empty_streak = 0
        self._had_target = True

        best = None
        for d in detections:
            if self._in_zone(d, image_size) and d.confidence >= self._min_conf_event:
                if best is None or d.confidence > best.confidence:
                    best = d

        if best is not None:
            self._zone_streak += 1
            if not self._in_zone_state:
                self._in_zone_state = True
                self._zone_entered_at = time.monotonic()
                self._lock_announced = False
                self._emit(A.ACTION_ENTER_SHOOTING_ZONE, best, stamp)
            elif not self._lock_announced and self._zone_streak >= self._lock_stable_frames:
                self._lock_announced = True
                self._emit(A.ACTION_LOCK_STABLE, best, stamp)
        else:
            self._zone_streak = 0
            if self._in_zone_state:
                self._in_zone_state = False
                self._lock_announced = False
                self._emit(A.ACTION_EXIT_SHOOTING_ZONE, None, stamp)

    def _emit(self, action: int, d, stamp) -> None:
        e = self._AtisEvent()
        e.header.stamp = stamp
        e.header.frame_id = self._frame_id
        e.action = int(action)
        if d is not None:
            e.track_id = int(d.track_id)
            e.class_id = int(d.class_id)
            e.class_name = str(d.class_name)
            e.confidence = float(d.confidence)
        if self._zone_entered_at is not None:
            e.dwell_seconds = float(time.monotonic() - self._zone_entered_at)
        self._pub_evt.publish(e)
        self._info(f"atis_event action={action} class={e.class_name} conf={e.confidence:.2f}")

    def shutdown(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)
        try:
            self._executor.remove_node(self._node)
            self._node.destroy_node()
        except Exception:
            pass
        if self._owns_context and self._rclpy.ok():
            self._rclpy.shutdown()
