#!/usr/bin/env python3
"""
S-02: Otonom Hedef Tespiti ve Kilitlenme Simülasyonu
Hedef: 10m mesafede A3 tahta (merkez 6cm, orta halka 12cm)
Kamera: RealSense D455, FoV=90°
Yöntem: Geometrik hesap ile açısal sapma ve kilit simülasyonu
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math, time, csv

HEDEF_X = 10.0
HEDEF_Y = 0.0
HEDEF_Z = 0.365
KAMERA_OFSET_X = 0.62
KAMERA_FOV_RAD = 1.5708        # 90 derece
MERKEZ_TOLERANS_DEG = 2.0      # ±2° merkez toleransı
KILIT_SURESI = 1.0             # saniye
VERI_DOSYA = '/home/talha/tulpar_ika_sim/test_kanit/S02/s02_hedef_verisi.csv'


class HedefTespitTesti(Node):
    def __init__(self):
        super().__init__('s02_hedef_tespit')
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.odom_alindi = False

    def odom_cb(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        self.robot_yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )
        self.odom_alindi = True

    def hedef_hesapla(self):
        cam_x = self.robot_x + KAMERA_OFSET_X * math.cos(self.robot_yaw)
        cam_y = self.robot_y + KAMERA_OFSET_X * math.sin(self.robot_yaw)
        dx = HEDEF_X - cam_x
        dy = HEDEF_Y - cam_y
        mesafe = math.sqrt(dx * dx + dy * dy)
        hedef_aci = math.atan2(dy, dx)
        sapma = hedef_aci - self.robot_yaw
        while sapma > math.pi:
            sapma -= 2 * math.pi
        while sapma < -math.pi:
            sapma += 2 * math.pi
        fov_icinde = abs(sapma) < KAMERA_FOV_RAD / 2
        merkez_hizali = abs(math.degrees(sapma)) < MERKEZ_TOLERANS_DEG
        return mesafe, math.degrees(sapma), fov_icinde, merkez_hizali


def main():
    rclpy.init()
    node = HedefTespitTesti()

    print('=' * 60)
    print('S-02: HEDEF TESPİT VE KİLİTLEME TESTİ')
    print('=' * 60)
    print(f'Hedef pozisyon : ({HEDEF_X}, {HEDEF_Y}, {HEDEF_Z}) m')
    print(f'Hedef boyutu   : A3 (420x297mm), merkez=6cm, halka=12cm')
    print(f'Kamera FoV     : {math.degrees(KAMERA_FOV_RAD):.0f}°')
    print(f'Merkez tolerans: ±{MERKEZ_TOLERANS_DEG}°')
    print(f'Kilit süresi   : {KILIT_SURESI} saniye')
    print('=' * 60)

    # Odom bekle
    print('\nOdom verisi bekleniyor...')
    t_start = time.time()
    while rclpy.ok() and not node.odom_alindi:
        rclpy.spin_once(node, timeout_sec=0.1)
        if time.time() - t_start > 5.0:
            print('HATA: Odom verisi gelmedi! Gazebo çalışıyor mu?')
            node.destroy_node()
            rclpy.shutdown()
            return

    print(f'Robot pozisyon: ({node.robot_x:.3f}, {node.robot_y:.3f}), '
          f'Yaw: {math.degrees(node.robot_yaw):.1f}°\n')

    veriler = []
    test_baslangic = time.time()

    # --- AŞAMA 1: Hedef Algılama (Lazer Kapalı) ---
    print('[ AŞAMA 1 ] Hedef algılama — Lazer KAPALI')
    mesafe, sapma, fov_icinde, merkez = node.hedef_hesapla()
    t = time.time() - test_baslangic
    veriler.append((t, mesafe, sapma, False, False))

    if not fov_icinde:
        print(f'  UYARI: Hedef kamera FoV dışında! Sapma={sapma:.1f}°')
    else:
        print(f'  Hedef mesafe    : {mesafe:.2f} m')
        print(f'  Açısal sapma    : {sapma:.2f}°')
        print(f'  FoV içinde      : ✓')
    rclpy.spin_once(node, timeout_sec=0.1)

    # --- AŞAMA 2: Merkezleme ---
    print('\n[ AŞAMA 2 ] Hedef merkezleme değerlendirmesi')
    mesafe, sapma, fov_icinde, merkez = node.hedef_hesapla()
    t = time.time() - test_baslangic
    veriler.append((t, mesafe, sapma, False, False))

    if merkez:
        print(f'  Hedef MERKEZLENDİ ✓  (sapma={sapma:.2f}°, tolerans ±{MERKEZ_TOLERANS_DEG}°)')
    else:
        print(f'  UYARI: Hedef merkez dışı. Sapma={sapma:.2f}° (tolerans ±{MERKEZ_TOLERANS_DEG}°)')
    rclpy.spin_once(node, timeout_sec=0.1)

    # --- AŞAMA 3: Lazer Aktif + Kilit ---
    print('\n[ AŞAMA 3 ] Sanal lazer AKTİF edildi — Kilit bekleniyor...')
    robot_x_baslangic = node.robot_x
    robot_y_baslangic = node.robot_y
    kilit_baslangic = time.time()
    kilit_tamamlandi = False
    kilit_suresi_gercek = 0.0

    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.05)
        t = time.time() - test_baslangic
        mesafe, sapma, fov_icinde, merkez = node.hedef_hesapla()
        kilit_gecen = time.time() - kilit_baslangic
        veriler.append((t, mesafe, sapma, True, merkez))

        hareket = math.sqrt(
            (node.robot_x - robot_x_baslangic) ** 2 +
            (node.robot_y - robot_y_baslangic) ** 2
        )

        if kilit_gecen >= KILIT_SURESI:
            kilit_tamamlandi = True
            kilit_suresi_gercek = kilit_gecen
            break

        if kilit_gecen > 0.2:
            print(f'  Kilit: {kilit_gecen:.1f}/{KILIT_SURESI:.1f}s  '
                  f'sapma={sapma:.2f}°  hareket={hareket:.4f}m')

        if hareket > 0.05:
            print(f'  HATA: Araç {hareket:.3f}m hareket etti! Kilit bozuldu.')
            break

    # --- SONUÇ ---
    t_toplam = time.time() - test_baslangic
    robot_hareket = math.sqrt(
        (node.robot_x - robot_x_baslangic) ** 2 +
        (node.robot_y - robot_y_baslangic) ** 2
    )
    mesafe_son, sapma_son, _, _ = node.hedef_hesapla()

    print('\n' + '=' * 60)
    print('S-02 TEST SONUÇLARI')
    print('=' * 60)
    print(f'Hedef tespit        : {"✓ BAŞARILI" if fov_icinde else "✗ BAŞARISIZ"}')
    print(f'Merkez hizalama     : {"✓ BAŞARILI" if merkez else "✗ BAŞARISIZ"} '
          f'(sapma={sapma_son:.2f}°)')
    print(f'Kilit süresi        : {kilit_suresi_gercek:.2f} / {KILIT_SURESI:.1f} s  '
          f'→ {"✓ BAŞARILI" if kilit_tamamlandi else "✗ BAŞARISIZ"}')
    print(f'Araç hareketi       : {robot_hareket:.4f} m  '
          f'→ {"✓ Hareketsiz" if robot_hareket < 0.05 else "✗ Hareket tespit edildi"}')
    print(f'Toplam test süresi  : {t_toplam:.2f} s')
    print(f'Hedef mesafe (son)  : {mesafe_son:.2f} m')

    basari = fov_icinde and kilit_tamamlandi and robot_hareket < 0.05
    print(f'\nGENEL SONUÇ: {"S-02 TESTİ BAŞARILI ✓" if basari else "S-02 TESTİ BAŞARISIZ ✗"}')
    print('=' * 60)

    with open(VERI_DOSYA, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['zaman', 'mesafe', 'sapma_derece', 'lazer_aktif', 'merkez_hizali'])
        for row in veriler:
            w.writerow([f'{v:.4f}' if isinstance(v, float) else int(v) for v in row])
    print(f'Veri kaydedildi: {VERI_DOSYA}')

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
