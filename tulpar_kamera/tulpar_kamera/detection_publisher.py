#!/usr/bin/env python3
"""
detection_publisher.py -- Tulpar IKA perception -> ROS2 koprusu.

TASARIM KARARI (onemli):
    Bu bir ROS2 *node dosyasi* degil, mevcut kamera_node.py process'inin
    ICINDE calisan bir modul. Sebep: JetPack 7.2'de nvarguscamerasrc boot
    basina yalnizca BIR KEZ acilabiliyor. Ayri bir ROS node'u ikinci bir
    Argus oturumu acmak zorunda kalirdi ve "nvbuf_utils: dmabuf_fd -1"
    hatasiyla patlardi (kurtarma yolu sadece reboot). Dolayisiyla tek
    Argus oturumu -> tee -> [H264/WebRTC] + [BGR/YOLO] mimarisi korunur ve
    YOLO kolunun sonucu buradan ROS2'ye pompalanir.

    rclpy kendi thread'inde spin eder; publish cagrilari GStreamer'in
    appsink callback'inden gelir. rclpy publisher'lari thread-safe'dir,
    ancak callback'i ASLA bloklamayin -- publish() ucuzdur, sorun degil.

KULLANIM (kamera_node.py icinde):

    from detection_publisher import DetectionPublisher

    ros = DetectionPublisher(               # ROS2 yoksa/kapaliysa no-op olur
        enabled=args.ros,
        frame_id="camera_link",
        shooting_zone=(0.25, 0.25),         # normalize yari-genislik/yukseklik
        lock_stable_frames=15,
    )
    ...
    # her YOLO karesinden sonra:
    ros.publish(
        detections=[...],                   # asagidaki Det dataclass listesi
        image_size=(1280, 720),
        capture_time_ns=pts_ns,             # yoksa None -> simdiki zaman
        inference_ms=12.4,
    )
    ...
    ros.shutdown()

--ros-yok modunda hicbir rclpy import'u yapilmaz, eski stdout davranisi surer.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence, Tuple

__all__ = ["Det", "DetectionPublisher"]


# --------------------------------------------------------------------------
# YOLO tarafinin uretecegi notr veri yapisi. ROS'a bagimli degil, boylece
# ROS kapaliyken de ayni kod yolu calisir ve birim testi kolaydir.
# --------------------------------------------------------------------------
@dataclass
class Det:
    class_id: int
    class_name: str
    confidence: float
    # piksel cinsinden kutu, xyxy (YOLO'nun dogal cikisi)
    x1: float
    y1: float
    x2: float
    y2: float
    track_id: int = 0          # DeepSORT gelince doldurulacak
    age: int = 0
    # derinlik gelince doldurulacak (RealSense). None = bilinmiyor.
    position: Optional[Tuple[float, float, float]] = None
    position_stddev: float = 0.0

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) * 0.5, (self.y1 + self.y2) * 0.5)

    @property
    def size(self) -> Tuple[float, float]:
        return (abs(self.x2 - self.x1), abs(self.y2 - self.y1))


class _NullPublisher:
    """ROS kapaliyken kullanilan sessiz taklit."""

    ok = False

    def publish(self, *_a, **_kw) -> None:
        pass

    def shutdown(self) -> None:
        pass


class DetectionPublisher:
    """
    /detections            (tulpar_msgs/DetectionArray, BEST_EFFORT, depth=1)
    /tulpar_bt/atis_event  (tulpar_msgs/AtisEvent, RELIABLE + TRANSIENT_LOCAL)

    QoS gerekcesi:
      - /detections her karede akar; eski kare degersizdir -> BEST_EFFORT,
        KEEP_LAST(1). Yavas bir abone (or. konsol) pipeline'i geriye
        basinclamaz.
      - atis_event nadir ve kritiktir -> RELIABLE. TRANSIENT_LOCAL sayesinde
        BT node'u gec baslasa bile son durumu alir.
    """

    ok = True

    def __new__(cls, enabled: bool = True, **kwargs):
        if not enabled:
            return _NullPublisher()  # type: ignore[return-value]
        return super().__new__(cls)

    def __init__(
        self,
        enabled: bool = True,
        node_name: str = "tulpar_kamera_perception",
        frame_id: str = "camera_link",
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

        # Import'lar burada: ROS kapaliyken rclpy'nin yuklenmesini istemiyoruz.
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import (
            DurabilityPolicy,
            HistoryPolicy,
            QoSProfile,
            ReliabilityPolicy,
        )
        from tulpar_msgs.msg import AtisEvent, Detection, DetectionArray

        self._rclpy = rclpy
        self._AtisEvent = AtisEvent
        self._Detection = Detection
        self._DetectionArray = DetectionArray

        self._frame_id = frame_id
        self._zone_w, self._zone_h = shooting_zone
        self._min_conf_event = min_confidence_for_event
        self._lock_stable_frames = lock_stable_frames
        self._target_lost_frames = target_lost_frames
        self._log = logger

        self._frame_seq = 0
        self._zone_streak = 0          # ust uste kac karedir bolgede
        self._zone_entered_at: Optional[float] = None
        self._in_zone = False
        self._lock_announced = False
        self._empty_streak = 0
        self._had_target = False

        if not rclpy.ok():
            rclpy.init(args=None)
            self._owns_context = True
        else:
            self._owns_context = False

        self._node: "Node" = rclpy.create_node(node_name)

        fast = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        sticky = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        self._pub_det = self._node.create_publisher(DetectionArray, detections_topic, fast)
        self._pub_evt = self._node.create_publisher(AtisEvent, atis_topic, sticky)

        self._executor = rclpy.executors.SingleThreadedExecutor()
        self._executor.add_node(self._node)
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._spin, name="rclpy-spin", daemon=True
        )
        self._thread.start()
        self._info(
            f"ROS2 yayini acik: {detections_topic} (best_effort), "
            f"{atis_topic} (reliable/transient_local)"
        )

    # ------------------------------------------------------------------ util
    def _info(self, msg: str) -> None:
        if self._log is not None:
            self._log.info(msg)
        else:
            print(f"[ros] {msg}", flush=True)

    def _spin(self) -> None:
        while not self._stop.is_set() and self._rclpy.ok():
            self._executor.spin_once(timeout_sec=0.1)

    def _stamp(self, capture_time_ns: Optional[int]):
        if capture_time_ns is None:
            return self._node.get_clock().now().to_msg()
        from builtin_interfaces.msg import Time

        t = Time()
        t.sec = int(capture_time_ns // 1_000_000_000)
        t.nanosec = int(capture_time_ns % 1_000_000_000)
        return t

    # --------------------------------------------------------------- publish
    def publish(
        self,
        detections: Sequence[Det],
        image_size: Tuple[int, int],
        capture_time_ns: Optional[int] = None,
        inference_ms: float = 0.0,
    ) -> Optional[Det]:
        """
        Tespitleri yayinlar ve PID'in izleyecegi BIRINCIL hedefi dondurur
        (yoksa None). Birincil hedef = bolgeye en yakin/en guvenilir olan.
        """
        w, h = image_size
        stamp = self._stamp(capture_time_ns)
        self._frame_seq += 1

        arr = self._DetectionArray()
        arr.header.stamp = stamp
        arr.header.frame_id = self._frame_id
        arr.frame_seq = self._frame_seq
        arr.image_width = int(w)
        arr.image_height = int(h)
        arr.inference_ms = float(inference_ms)

        primary: Optional[Det] = None
        primary_score = -1.0

        for d in detections:
            cx, cy = d.center
            bw, bh = d.size
            ex = (cx - w * 0.5) / (w * 0.5)   # -1 .. +1
            ey = (cy - h * 0.5) / (h * 0.5)
            in_zone = abs(ex) <= self._zone_w and abs(ey) <= self._zone_h

            m = self._Detection()
            m.class_id = int(d.class_id)
            m.class_name = str(d.class_name)
            m.confidence = float(d.confidence)
            m.track_id = int(d.track_id)
            m.age = int(d.age)
            m.center_x, m.center_y = float(cx), float(cy)
            m.width, m.height = float(bw), float(bh)
            m.center_x_norm, m.center_y_norm = float(cx / w), float(cy / h)
            m.width_norm, m.height_norm = float(bw / w), float(bh / h)
            if d.position is not None:
                m.has_position = True
                m.position_x, m.position_y, m.position_z = (float(v) for v in d.position)
                m.position_stddev = float(d.position_stddev)
            else:
                m.has_position = False
            m.error_x, m.error_y = float(ex), float(ey)
            m.in_shooting_zone = bool(in_zone)
            arr.detections.append(m)

            # merkeze yakinlik agirlikli skor
            score = d.confidence * (1.0 - min(1.0, math.hypot(ex, ey) / math.sqrt(2)))
            if score > primary_score:
                primary_score, primary = score, d

        self._pub_det.publish(arr)
        self._update_events(arr, primary, stamp)
        return primary

    # ---------------------------------------------------------------- events
    def _update_events(self, arr, primary: Optional[Det], stamp) -> None:
        A = self._AtisEvent

        if not arr.detections:
            self._empty_streak += 1
            self._zone_streak = 0
            if self._in_zone:
                self._emit(A.ACTION_EXIT_SHOOTING_ZONE, None, stamp)
                self._in_zone = False
                self._lock_announced = False
            if self._had_target and self._empty_streak >= self._target_lost_frames:
                self._emit(A.ACTION_TARGET_LOST, None, stamp)
                self._had_target = False
            return

        self._empty_streak = 0
        self._had_target = True

        best = None
        for m in arr.detections:
            if m.in_shooting_zone and m.confidence >= self._min_conf_event:
                if best is None or m.confidence > best.confidence:
                    best = m

        if best is not None:
            self._zone_streak += 1
            if not self._in_zone:
                self._in_zone = True
                self._zone_entered_at = time.monotonic()
                self._lock_announced = False
                self._emit(A.ACTION_ENTER_SHOOTING_ZONE, best, stamp)
            elif (
                not self._lock_announced
                and self._zone_streak >= self._lock_stable_frames
            ):
                self._lock_announced = True
                self._emit(A.ACTION_LOCK_STABLE, best, stamp)
        else:
            self._zone_streak = 0
            if self._in_zone:
                self._in_zone = False
                self._lock_announced = False
                self._emit(A.ACTION_EXIT_SHOOTING_ZONE, None, stamp)

    def _emit(self, action: int, m, stamp) -> None:
        e = self._AtisEvent()
        e.header.stamp = stamp
        e.header.frame_id = self._frame_id
        e.action = int(action)
        if m is not None:
            e.track_id = int(m.track_id)
            e.class_id = int(m.class_id)
            e.class_name = str(m.class_name)
            e.confidence = float(m.confidence)
        if self._zone_entered_at is not None:
            e.dwell_seconds = float(time.monotonic() - self._zone_entered_at)
        self._pub_evt.publish(e)
        self._info(f"atis_event action={action} class={e.class_name} conf={e.confidence:.2f}")

    # -------------------------------------------------------------- shutdown
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
