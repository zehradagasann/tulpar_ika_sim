#!/usr/bin/env python3
"""
tulpar_kamera - D435if + YDLidar TG30 nokta bulutu fuzyon/dogrulama node'u.

NEDEN VAR (roadmap Gun 6-7, KTR 3.3.2): kamera tabanli derinlik tespiti
(YOLO bbox + RealSense derinlik) tek basina guvenilmez olabilir (specular
yansima, dusuk isik, YOLO yanlis pozitifi, RealSense'in IR golgesi). Bu
node ayni nesnenin YDLidar TG30 tarafindan da BAGIMSIZ olarak gorulup
gorulmedigini kontrol eder - iki farkli sensor ayni yon+mesafede ayni
seyi dogruluyorsa, obstacle Nav2 costmap'ine YUKSEK GUVENLE beslenir.
Sadece dogrulanan noktalar yayinlanir (bu bilerek bir FILTREdir, tek
sensorluk tum tespitlerin yerini almaz - kamera-only tespitler zaten
tulpar_obstacle_injector'in koni_tespitleri hattindan geciyor).

MIMARI: kamera_node.py'nin RealSense pipeline'ina hic DOKUNMAZ - tamamen
ayri, bagimsiz bir ROS2 node/process. Sadece ROS topic'leri dinler:
  /detections               (Detection2DArray, kamera_node.py'den)
  /d435if/depth/camera_info (CameraInfo, kamera_node.py'den - piksel->3D
                              geri izdusumu icin fx/fy/ppx/ppy lazim)
  /scan                     (LaserScan, ydlidar_ros2_driver_node'dan)

TF: kamera noktasi once kendi frame'inden (Detection2DArray.header.frame_id,
normalde d435if_color_optical_frame) dogrudan lidar'in kendi frame'ine
(scan.header.frame_id, normalde laser_frame) tasinir - boylece lidar
karsilastirmasi LaserScan'in KENDI acisal indeksleme sistemiyle (angle_min
+ i*angle_increment) direkt yapilabilir, ikinci bir donusume gerek kalmaz.
Bu TF zincirinin var olmasi icin robot_state_publisher calisiyor olmali -
gercek robotta bunu tulpar_description/launch/bringup.launch.py saglar
(robot_state_publisher + ydlidar_ros2_driver_node birlikte). O launch
calismiyorsa TF lookup timeout ile basarisiz olur; bu node crash ETMEZ,
sadece o karedeki dogrulamayi atlar (bkz. asagidaki try/except + throttled
uyari logu).

Dogrulanan noktalar --target-frame'e (varsayilan odom - Zehra/Talha'nin
tulpar_obstacle_injector'iyla AYNI hedef frame, Nav2 costmap'in zaten
bekledigi) tasinip PointCloud2 olarak yayinlanir.
"""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from rclpy.duration import Duration
from rclpy.time import Time

from sensor_msgs.msg import CameraInfo, LaserScan, PointCloud2
from sensor_msgs_py import point_cloud2
from geometry_msgs.msg import PointStamped
from tulpar_ika_msgs.msg import Detection2DArray

import tf2_ros
import tf2_geometry_msgs  # noqa: F401 - PointStamped icin tf2 donusum kaydini aktive eder


class LidarFuzyonNode(Node):
    def __init__(self):
        super().__init__("tulpar_lidar_fuzyon")

        self.declare_parameter("detections_topic", "/detections")
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("camera_info_topic", "/d435if/depth/camera_info")
        self.declare_parameter("output_topic", "/tulpar_kamera/fuzyon_engelleri")
        self.declare_parameter("target_frame", "odom")
        self.declare_parameter("range_tolerance_m", 0.35)
        self.declare_parameter("tf_timeout_sec", 0.1)
        self.declare_parameter("min_confidence", 0.5)

        self._detections_topic = self.get_parameter("detections_topic").value
        self._scan_topic = self.get_parameter("scan_topic").value
        self._camera_info_topic = self.get_parameter("camera_info_topic").value
        self._output_topic = self.get_parameter("output_topic").value
        self._target_frame = self.get_parameter("target_frame").value
        self._range_tol = float(self.get_parameter("range_tolerance_m").value)
        self._tf_timeout = Duration(seconds=float(self.get_parameter("tf_timeout_sec").value))
        self._min_conf = float(self.get_parameter("min_confidence").value)

        fast = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=1,
                          reliability=ReliabilityPolicy.BEST_EFFORT,
                          durability=DurabilityPolicy.VOLATILE)

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        self._latest_scan: LaserScan | None = None
        self._latest_cam_info: CameraInfo | None = None
        self._cam_info_warned = False
        self._scan_warned = False
        self._tf_warn_count = 0

        self._sub_scan = self.create_subscription(
            LaserScan, self._scan_topic, self._on_scan, fast)
        self._sub_cam_info = self.create_subscription(
            CameraInfo, self._camera_info_topic, self._on_cam_info, fast)
        self._sub_det = self.create_subscription(
            Detection2DArray, self._detections_topic, self._on_detections, fast)
        self._pub_cloud = self.create_publisher(PointCloud2, self._output_topic, fast)

        self._toplam = 0
        self._dogrulanan = 0
        self._log_timer = self.create_timer(5.0, self._log_ozet)

        self.get_logger().info(
            f"tulpar_lidar_fuzyon hazir: {self._detections_topic} + {self._scan_topic} "
            f"-> {self._output_topic} (frame={self._target_frame}, "
            f"range_tolerance={self._range_tol}m)")

    def _on_scan(self, msg: LaserScan) -> None:
        self._latest_scan = msg

    def _on_cam_info(self, msg: CameraInfo) -> None:
        self._latest_cam_info = msg

    def _log_ozet(self) -> None:
        if self._toplam == 0:
            return
        self.get_logger().info(
            f"[ozet] {self._dogrulanan}/{self._toplam} tespit lidar tarafindan dogrulandi "
            f"(son 5sn)")
        self._toplam = 0
        self._dogrulanan = 0

    def _lidar_range_at_bearing(self, scan: LaserScan, bearing_rad: float) -> float | None:
        """scan.angle_min/angle_increment kullanarak en yakin isindaki mesafeyi doner.

        Aci scan'in kapsama araligi disindaysa ya da o indeksteki okuma
        gecersizse (inf/nan/range_min altinda) None doner.
        """
        if scan.angle_increment == 0.0:
            return None
        if bearing_rad < scan.angle_min or bearing_rad > scan.angle_max:
            return None
        idx = int(round((bearing_rad - scan.angle_min) / scan.angle_increment))
        if idx < 0 or idx >= len(scan.ranges):
            return None
        r = scan.ranges[idx]
        if not math.isfinite(r) or r < scan.range_min or r > scan.range_max:
            return None
        return float(r)

    def _on_detections(self, msg: Detection2DArray) -> None:
        if self._latest_cam_info is None:
            if not self._cam_info_warned:
                self.get_logger().warning(
                    f"{self._camera_info_topic} henuz alinmadi, fuzyon bekletiliyor "
                    "(kamera_node.py calisiyor mu?)")
                self._cam_info_warned = True
            return
        if self._latest_scan is None:
            if not self._scan_warned:
                self.get_logger().warning(
                    f"{self._scan_topic} henuz alinmadi, fuzyon bekletiliyor "
                    "(ydlidar_ros2_driver_node calisiyor mu?)")
                self._scan_warned = True
            return

        info = self._latest_cam_info
        scan = self._latest_scan
        fx, fy = info.k[0], info.k[4]
        ppx, ppy = info.k[2], info.k[5]
        if fx == 0.0 or fy == 0.0:
            return

        dogrulanan_noktalar = []

        for d in msg.detections:
            if not d.depth_valid or d.depth_m <= 0.0:
                continue
            if d.confidence < self._min_conf:
                continue
            self._toplam += 1

            # Piksel -> kamera optik cercevesinde 3D nokta (pinhole ters izdusum,
            # REP-103: x-sag, y-asagi, z-ileri).
            z = float(d.depth_m)
            x = (d.center_px.x - ppx) * z / fx
            y = (d.center_px.y - ppy) * z / fy

            kam_nokta = PointStamped()
            kam_nokta.header.frame_id = msg.header.frame_id
            kam_nokta.header.stamp = msg.header.stamp
            kam_nokta.point.x = x
            kam_nokta.point.y = y
            kam_nokta.point.z = z

            # Once lidar'in KENDI cercevesine tasi - LaserScan'in acisal
            # indekslemesiyle dogrudan karsilastirma icin.
            try:
                lidar_cercevesinde = self._tf_buffer.transform(
                    kam_nokta, scan.header.frame_id, timeout=self._tf_timeout)
            except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                    tf2_ros.ExtrapolationException) as e:
                self._tf_warn_count += 1
                if self._tf_warn_count % 30 == 1:
                    self.get_logger().warning(
                        f"TF donusumu basarisiz ({msg.header.frame_id} -> "
                        f"{scan.header.frame_id}): {e}. robot_state_publisher "
                        "(bringup.launch.py) calisiyor mu kontrol edin.")
                continue

            lx, ly = lidar_cercevesinde.point.x, lidar_cercevesinde.point.y
            bearing = math.atan2(ly, lx)
            kam_mesafe = math.hypot(lx, ly)
            lidar_mesafe = self._lidar_range_at_bearing(scan, bearing)

            if lidar_mesafe is None:
                continue  # lidar bu yonde veri vermiyor - dogrulama yok, karsilastirma yok
            if abs(lidar_mesafe - kam_mesafe) > self._range_tol:
                continue  # iki sensor anlasmiyor - supheli, filtrelendi

            self._dogrulanan += 1

            # Dogrulandi - hedef cerceveye tasiyip cikti bulutuna ekle.
            try:
                hedef_cercevesinde = self._tf_buffer.transform(
                    kam_nokta, self._target_frame, timeout=self._tf_timeout)
            except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                    tf2_ros.ExtrapolationException):
                continue
            p = hedef_cercevesinde.point
            dogrulanan_noktalar.append((p.x, p.y, p.z))

        cloud = point_cloud2.create_cloud_xyz32(
            header=self._make_header(msg.header.stamp), points=dogrulanan_noktalar)
        self._pub_cloud.publish(cloud)

    def _make_header(self, stamp):
        from std_msgs.msg import Header
        h = Header()
        h.stamp = stamp
        h.frame_id = self._target_frame
        return h


def main():
    rclpy.init()
    node = LidarFuzyonNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
