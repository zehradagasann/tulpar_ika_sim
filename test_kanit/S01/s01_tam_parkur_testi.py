#!/usr/bin/env python3
"""S-01 Tam Parkur Testi — Gazebo gerçek pose verisiyle doğrulama"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import subprocess, threading, time, csv, math, re

class TamParkurTesti(Node):
    def __init__(self):
        super().__init__('s01_tam_parkur')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.veriler = []
        self.x = 0.0
        self.z = 0.0
        self.roll = 0.0
        self.pitch = 0.0
        self.calisior = True
        self.lock = threading.Lock()

    def pose_dinle(self):
        """Gazebo dynamic_pose topic'ini sürekli dinle"""
        cmd = ['gz', 'topic', '-e', '-t',
               '/world/s01_zemin_testi/dynamic_pose/info']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
        tulpar_blok = False
        buf = []
        for line in proc.stdout:
            if not self.calisior:
                proc.terminate()
                break
            if 'name: "tulpar"' in line:
                tulpar_blok = True
                buf = []
            elif tulpar_blok:
                buf.append(line)
                if line.strip() == '}' and len(buf) > 10:
                    self._parse(buf)
                    tulpar_blok = False

    def _parse(self, buf):
        text = ''.join(buf)
        try:
            pos = re.search(r'position\s*{([^}]*)}', text).group(1)
            ori = re.search(r'orientation\s*{([^}]*)}', text).group(1)
            x = float(re.search(r'x:\s*([-\d.e]+)', pos).group(1))
            z = float(re.search(r'z:\s*([-\d.e]+)', pos).group(1))
            qx = float(re.search(r'x:\s*([-\d.e]+)', ori).group(1))
            qy = float(re.search(r'y:\s*([-\d.e]+)', ori).group(1))
            qz = float(re.search(r'z:\s*([-\d.e]+)', ori).group(1))
            qw = float(re.search(r'w:\s*([-\d.e]+)', ori).group(1))
            roll = math.degrees(math.atan2(2*(qw*qx+qy*qz), 1-2*(qx*qx+qy*qy)))
            pitch = math.degrees(math.asin(max(-1,min(1,2*(qw*qy-qz*qx)))))
            with self.lock:
                self.x, self.z, self.roll, self.pitch = x, z, roll, pitch
        except Exception:
            pass

def main():
    rclpy.init()
    node = TamParkurTesti()
    node.get_logger().info('S-01 TAM PARKUR TESTİ — Gazebo gerçek pose ile')

    # Pose dinleyici thread başlat
    t = threading.Thread(target=node.pose_dinle, daemon=True)
    t.start()
    time.sleep(2.0)

    baslangic = time.time()
    rapor = {
        'rampa': {'gecti': False, 'max_pitch': 0, 'fren_kayma': None},
        'yan_egim': {'gecti': False, 'max_roll': 0},
        'blok': {'gecti': False, 'max_z': 0},
        'tumsek': {'gecti': False, 'max_z': 0},
    }
    son_log = 0
    # Rampa fren testi durumu
    fren_bekleniyor = False
    fren_baslangic = None
    fren_x_baslangic = None
    FREN_X = 2.7   # rampa üzerinde dur noktası (çıkışın ortası)
    FREN_SURE = 2.0

    while rclpy.ok():
        with node.lock:
            x, z, roll, pitch = node.x, node.z, node.roll, node.pitch
        t_gecen = time.time() - baslangic
        node.veriler.append((t_gecen, x, z, roll, pitch))

        # Bölge takibi
        if 2.0 <= x <= 5.0:
            rapor['rampa']['max_pitch'] = max(rapor['rampa']['max_pitch'], abs(pitch))
        if 6.0 <= x <= 10.0:
            rapor['yan_egim']['max_roll'] = max(rapor['yan_egim']['max_roll'], abs(roll))
        if 10.5 <= x <= 12.0:
            rapor['blok']['max_z'] = max(rapor['blok']['max_z'], z)
        if 13.5 <= x <= 16.0:
            rapor['tumsek']['max_z'] = max(rapor['tumsek']['max_z'], z)

        # Her 1 saniyede log
        if t_gecen - son_log >= 1.0:
            node.get_logger().info(f't={t_gecen:.0f}s x={x:.2f}m z={z:.3f}m roll={roll:.1f}° pitch={pitch:.1f}°')
            son_log = t_gecen

        # Devrilme kontrolü
        if abs(roll) > 45 or abs(pitch) > 50:
            node.get_logger().error(f'DEVRİLDİ! roll={roll:.1f}° pitch={pitch:.1f}°')
            break

        # Bitiş
        if x >= 16.5:
            node.get_logger().info('Parkur tamamlandı!')
            break

        # 150 saniye timeout
        if t_gecen > 150:
            node.get_logger().warn(f'Timeout — x={x:.2f}m de kaldı')
            break

        # --- RAMPA FREN TESTİ ---
        if not fren_bekleniyor and x >= FREN_X and x <= 3.2:
            # Rampa ortasına geldi — dur ve fren testi yap
            node.cmd_pub.publish(Twist())
            fren_bekleniyor = True
            fren_baslangic = time.time()
            fren_x_baslangic = x
            node.get_logger().info(f'RAMPA FREN TESTİ: x={x:.2f}m de motor kesildi — 2 sn bekleniyor...')
            rclpy.spin_once(node, timeout_sec=0.05)
            continue

        if fren_bekleniyor:
            sure_gecti = time.time() - fren_baslangic
            with node.lock:
                x_sim = node.x
            kayma = abs(x_sim - fren_x_baslangic)
            if sure_gecti >= FREN_SURE:
                rapor['rampa']['fren_kayma'] = kayma
                node.get_logger().info(
                    f'FREN TESTİ TAMAMLANDI: {sure_gecti:.1f}s beklendi, kayma={kayma:.4f}m '
                    f'→ {"TUTTU ✓" if kayma < 0.05 else "KAYDI ✗"}'
                )
                fren_bekleniyor = False
            else:
                node.get_logger().info(f'  Fren bekliyor {sure_gecti:.1f}/{FREN_SURE:.1f}s — kayma={kayma:.4f}m')
                rclpy.spin_once(node, timeout_sec=0.1)
                continue

        # Hareket komutu
        msg = Twist()
        msg.linear.x = 0.5
        node.cmd_pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.05)

    node.cmd_pub.publish(Twist())
    node.calisior = False

    # Sonuç raporu
    son_x = node.veriler[-1][1] if node.veriler else 0
    rapor['rampa']['gecti'] = son_x > 5.0
    rapor['yan_egim']['gecti'] = son_x > 10.0
    rapor['blok']['gecti'] = son_x > 12.0
    rapor['tumsek']['gecti'] = son_x > 16.0

    print('\n' + '='*50)
    print('S-01 TAM PARKUR TEST RAPORU')
    print('='*50)
    print(f"Son konum: x={son_x:.2f}m")
    fren_k = rapor['rampa']['fren_kayma']
    fren_str = f"kayma={fren_k:.4f}m {'✓' if fren_k is not None and fren_k < 0.05 else '✗'}" if fren_k is not None else "test yapılmadı"
    print(f"Rampa (%45):    {'✓ GEÇTİ' if rapor['rampa']['gecti'] else '✗ GEÇEMEDİ'}  max_pitch={rapor['rampa']['max_pitch']:.1f}°  fren={fren_str}")
    print(f"Yan eğim (%20): {'✓ GEÇTİ' if rapor['yan_egim']['gecti'] else '✗ GEÇEMEDİ'}  max_roll={rapor['yan_egim']['max_roll']:.1f}°")
    print(f"15cm blok:      {'✓ GEÇTİ' if rapor['blok']['gecti'] else '✗ GEÇEMEDİ'}  max_z={rapor['blok']['max_z']:.3f}m")
    print(f"Tümsekler:      {'✓ GEÇTİ' if rapor['tumsek']['gecti'] else '✗ GEÇEMEDİ'}  max_z={rapor['tumsek']['max_z']:.3f}m")
    print('='*50)

    with open('/home/talha/tulpar_ika_sim/test_kanit/S01/s01_tam_parkur_verisi.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['zaman', 'konum_x', 'konum_z', 'roll', 'pitch'])
        for row in node.veriler:
            w.writerow([f'{v:.4f}' if isinstance(v, float) else v for v in row])
    print(f"Veri kaydedildi: {len(node.veriler)} satir")

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
