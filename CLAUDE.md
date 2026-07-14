# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a ROS 2 / Gazebo Harmonic simulation package for the **Tulpar IKA** — a 4-wheeled differential-drive ground robot (62 kg, 1200×600×240 mm chassis, Ø330 mm wheels). The package name is `tulpar_description`.

## Build & Run

The colcon workspace root is `~/tulpar_ws`. The repo lives at `~/tulpar_ws/src/tulpar_ika_sim`.

```bash
# Build
cd ~/tulpar_ws
colcon build --packages-select tulpar_description

# Source the workspace (required before ros2 commands)
source ~/tulpar_ws/install/setup.bash

# Launch Gazebo with the default world (S-01 terrain course)
ros2 launch tulpar_description gazebo.launch.py

# Launch with a specific world
ros2 launch tulpar_description gazebo.launch.py world:=/path/to/world.sdf

# Send velocity commands manually (while simulation runs)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3}}" --once

# Run a test script (Gazebo must be running first)
python3 test_kanit/S01/s01_rampa_testi.py
python3 test_kanit/E02/hizlanma_testi.py
python3 test_kanit/S02/s02_hedef_testi.py
```

## Architecture

### Robot model (`urdf/robot.urdf.xacro`)
- Frame hierarchy: `base_footprint` → `base_link` → wheels (FL/RL/FR/RR), `lidar_link`, `camera_link`
- `base_link` sits 0.165 m above ground (wheel radius); `base_footprint` is at ground level
- Visual mesh: `meshes/tulpar_yeni.stl` (scaled 0.001 — file is in mm)
- Gazebo plugins embedded in URDF: `DiffDrive` (subscribes `/cmd_vel`, publishes `/odom`), `JointStatePublisher` (publishes `/joint_states`)
- Sensors: RPLidar S2 on `lidar_link` (topic `scan`, 800 samples, 30 m range), RealSense D455 on `camera_link` (topic `camera/depth`, 848×480, 0.4–6 m)

### Launch file (`launch/gazebo.launch.py`)
Starts three nodes:
1. `robot_state_publisher` — processes the xacro and publishes `/robot_description` + TF
2. `gz_sim` — Gazebo Harmonic with `--render-engine ogre`
3. `parameter_bridge` — bridges ROS ↔ Gazebo topics: `/cmd_vel` (ROS→GZ), `/odom`, `/joint_states`, `/scan`, `/camera/depth` (GZ→ROS)

### Worlds (`worlds/`)
| File | Purpose |
|------|---------|
| `s01_robotlu_world.sdf` | S-01 terrain course: 10-step staircase ramp (~45% grade), 20% side-slope platform, 15 cm block, 5 cm speed bumps. **Includes robot spawn.** |
| `s02_hedef_world.sdf` | S-02 target detection: flat ground with A3 target board at 10 m |
| `e02_duz_world.sdf` | E-02 acceleration: flat 30+ m track with distance markers |

`s01_robotlu_world.sdf` embeds the full robot model (converted from URDF) so the robot spawns automatically. The other worlds require the robot to be spawned separately via the launch file.

### Test scripts (`test_kanit/`)
Each test is a standalone ROS 2 node that publishes `/cmd_vel` and subscribes `/odom`. Pattern:
1. Wait up to 5 s for `/odom` (abort if none received — check Gazebo is running)
2. Execute movement sequence, collecting timestamped data
3. Write results to a CSV next to the script
4. Companion `*_grafik.py` scripts read the CSV and produce matplotlib plots

| Directory | Tests |
|-----------|-------|
| `S01/` | Ramp stop/brake, side slope, 15 cm block, flat ground, full course |
| `S02/` | Target detection & lock (geometric simulation using camera FoV math) |
| `E02/` | 30 m straight-line acceleration at 0.5 m/s |

### Behavior Tree (`behavior_trees/`)
`ana_tree.xml` — main Behavior Tree draft (BehaviorTree.CPP v4, `BTCPP_format="4"`, Groot2-openable). Sequence: wait for system ready → repeat until course end → ReactiveFallback between (sign-detected shoot flow: stop Nav2, lock target, fire laser, resume Nav2) and default autonomous driving (Nav2 `NavigateToPose` placeholder). All action/condition nodes (`TabelaAlgılandiMi`, `HedefTespitYap`, `AtisYap`, etc.) are unimplemented placeholders — real C++ node registrations land on Day 2.

### Yer İstasyonu (`yer_istasyonu/`)
Electron + React + rclnodejs ile yazılmış masaüstü kontrol konsolu iskeleti. Şu an sadece "TULPAR İKA Yer İstasyonu" başlığı gösteren boş bir pencere - main process'te rclnodejs.init() ile bir ROS 2 node'u ("yer_istasyonu_node") oluşturuluyor ve DDS ağına katılıyor (ros2 node list ile doğrulandı). Telemetri, heartbeat yayını, olay günlüğü paneli gibi gerçek işlevler henüz implemente edilmedi - Gün 3'te eklenecek.

Çalıştırma: `cd yer_istasyonu && npm start`
Bilinen sorun: bazı Linux ortamlarında Electron sandbox izin hatası çıkabilir (`SUID sandbox helper binary...`) - çözüm: `node_modules/electron/dist/chrome-sandbox` dosyasını root:root/4755 yap, veya `npm start -- --noSandbox` kullan.

## Proje Bağlamı

- **Yarışma**: TEKNOFEST 2026 İnsansız Kara Aracı (İKA) — Araç: TULPAR
- **Kullanıcı**: Talha Dağ — Otonom Akış & Entegrasyon Sorumlusu; yazılım ekibi: Emin (görüntü işleme), Zehra (parkur algoritmaları / haberleşme)
- **Sprint**: 13–27 Temmuz 2026 (15 günlük yoğun uygulama sprinti)
- **KRİTİK DEADLINE**: Araç Kanıt Videosu (AKV) teslimi **20 Temmuz 2026 17:00** (şartname §4.4) — bu tarihe yaklaşan görevlerde uyar
- **Talha'nın görev alanları**: BT (Behavior Tree) mimarisi, Nav2 entegrasyonu, yer istasyonu (Electron + React + rclnodejs), EKF / sensör füzyonu, Watchdog/Failsafe, ELRS RC override, ağ altyapısı (Bullet M5)
- **Git kuralı**: Her zaman `talha_gelistirme` branch'inde çalış; `main` ve `yazilim_gelistirme`'ye direkt commit atma. Gün sonunda commit + push + PR'ı hatırlat.
- **Test kodları ↔ parkur eşleşmesi**: S-01 (arazi), S-02 (hedef tespit), S-03 (su geçişi), S-04 (slalom/kayar engel), S-05 (tam parkur), E-02 (hızlanma), E-03 (BMS), E-04 (failsafe), B-04 (boyut kontrolü)
- **Donanım**: Jetson Orin NX + Teensy 4.1 (I2C → 4× Lityumsan e-bike controller, bkz. Motor Sürücü Mimarisi v2), RPLidar S2, RealSense D435if (**tedarikte yok** — takip edilmesi gereken açık risk), WT901C-RS485 IMU, ZED-F9P RTK GNSS

### Motor Sürücü Mimarisi (v2 - 14 Temmuz güncellemesi)

- **Motor sürücü değişikliği**: Dual VESC 75100 + CAN bus planı terk edildi. Yerine: 4x Lityumsan 48V 22A e-bike controller (analog gaz girişi, dijital/CAN arayüzü yok, tork kontrolü yok, telemetri yok)
- **Yeni kontrol zinciri**: Teensy 4.1 → I2C → TCA9548A mux (0x70) → 4x PCF8591 DAC (0x48) → OP291 yükseltici → sürücü gaz teli. I2C bus hızı 100 kHz sabit (PCF8591 400 kHz desteklemiyor)
- **Gaz hattı kalibrasyon referansı**: DAC=0 → <0.1V, DAC=255 → 4.1–4.2V (multimetre/osiloskopla doğrulanır)
- **Kritik güvenlik riski**: PCF8591'in watchdog'u yok — Teensy donarsa DAC son değerde asılı kalır; bu yüzden Teensy'nin donanım WDT'si açılmalı, WDT reset'inde `setup()` gazları otomatik sıfırlamalı
- **Kanal eşlemesi**: 0=Ön-Sol, 1=Ön-Sağ, 2=Arka-Sol, 3=Arka-Sağ
- `/odom` hâlâ sadece enkoder+IMU'dan geliyor (VESC'ten hiç veri alınmıyordu zaten, bu değişmedi)
- Geri hareket ve nokta dönüş artık ayrı röle + durum makinesi gerektiriyor (motor tam durmadan röle değiştirilemez)
- **Yön değişim prosedürü (zorunlu sıra)**: `DAC=0` yaz → enkoderden hız ≈0 doğrula (yoksa 300ms bekle) → geri rölesini değiştir → 50ms bekle → gaz ver
- **Kademeli fren**: DAC değişim hızı sınırlanır (maks 5 birim/10ms) + fren teli rölesi — VESC regen fren artık yok
- **Pin haritası**: geri vites röleleri pin4 (sol) / pin5 (sağ), kilit rölesi pin2 (PC817+BC337); ELRS alıcı Serial7 (RX=pin28, TX=pin29, CRSF, 420000 baud)
- **Failsafe zamanlaması**: CRSF'den 400ms paket gelmezse → 4 kanala DAC=0 + kilit rölesi LOW
- Sürücüden telemetri yok — teşhis için Teensy, DAC+enkoder verisini 10Hz'de Jetson'a loglamalı
- Anti-windup PID ayarı şart (sürücünün iç rampası nedeniyle entegral birikir)
- `setup()`'ta İLK İŞ her zaman 4 kanala DAC=0 yazmak (güvenlik kuralı)
- **Etkilenen günler**: Gün 2 (I2C/DAC bring-up, VESC Tool artık yok), Gün 6 (CAN kısmı kalktı, PID/enkoder/EKF aynı), Gün 7 (yeni: geri vites/nokta dönüş durum makinesi), Gün 8 (kademeli fren artık yazılımsal DAC azaltma), Gün 11 (kalibrasyon süreci farklı)
- Güncel detaylı plan: `talha_yol_haritasi_v2.md` (repo dışında, Talha'da duruyor — gerekirse içeriğini iste)

## Key Physical Parameters
- Wheel separation: 1.04 m; wheel radius: 0.165 m
- Max linear velocity: 0.785 m/s; max angular velocity: 7.854 rad/s
- Max wheel torque: 50 Nm (in SDF world); 21.6 Nm (in URDF plugin — SDF takes precedence when robot is embedded in world)
- Physics: ODE solver, 1 ms step, 1000 Hz update rate, 100 iterations

## Gün Bazlı İlerleme Notları

- Gün 1 (14 Temmuz 2026) tamamlandı: BT taslağı (behavior_trees/), yer istasyonu iskeleti (yer_istasyonu/), repo temizliği ve worlds/ install bug düzeltmesi, PR #1 açıldı ve yazilim_gelistirme'ye merge edildi.
