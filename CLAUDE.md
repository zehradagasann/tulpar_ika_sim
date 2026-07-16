# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a ROS 2 / Gazebo Harmonic simulation package for the **Tulpar IKA** — a 4-wheeled differential-drive ground robot (64 kg, 1200×450×245 mm chassis, Ø400 mm wheels). The package name is `tulpar_description`.

## Build & Run

The colcon workspace root is `~/tulpar_ws`. The repo lives at `~/tulpar_ws/src/tulpar_ika_sim`.

**One-time setup after a fresh clone**: `tulpar_bt/` lives inside the `tulpar_ika_sim` repo (so it's tracked in the same git history/PR flow), but colcon's recursive package discovery stops descending once it finds `tulpar_ika_sim` itself as a package (repo root = `tulpar_description`). It won't see a package nested inside another package's directory. A symlink at the `src/` level works around this:
```bash
ln -s ~/tulpar_ws/src/tulpar_ika_sim/tulpar_bt ~/tulpar_ws/src/tulpar_bt
```
This symlink is workspace-local (not part of the git repo, not committed) — recreate it after every fresh clone/workspace setup. Without it, `colcon build` silently skips `tulpar_bt`.

```bash
# Build
cd ~/tulpar_ws
colcon build --packages-select tulpar_description
colcon build --packages-select tulpar_bt

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

### Robot model (`urdf/robot.urdf.xacro`) — Zehra'nın `feature/zehra-faz1-gun1` branch'i temel alındı (16 Temmuz 2026)
**Strateji değişikliği**: Bizim kendi ürettiğimiz decimation tabanlı mesh pipeline'ımız (`govde_v2/v3.stl`, `teker_v2/v3.stl` — global ve parça-bazlı decimation denemeleri) terk edildi ve o dosyalar silindi. Mekanik ekip orijinal `tulpar_ika_assembly.stl`'i Blender'da inceleyip tam/eksiksiz olduğunu doğruladı; bizim decimation'ımız küçük-orta braketleri kaybediyordu (kök neden bulundu: global quadric decimation küçük parçaları düşük-öncelikli sanıp siliyor, parça-bazlı decimation da tam çözemedi). Bunun yerine Zehra'nın `~/tulpar_ika_sim_incele` (feature/zehra-faz1-gun1 checkout) içindeki `urdf/robot.urdf.xacro` + ham `tulpar_ika_assembly.stl` (149MB, basitleştirilmemiş) bizim dosyalarımızın YERİNE kondu; sadece fiziksel parametreler (boyut/kütle/dingil/iz/tekerlek yarıçapı/inertia) mekanik ekipten gelen güncel değerlerle değiştirildi.
- Frame hierarchy: `base_footprint` → `base_link` → wheels (FL/RL/FR/RR), `lidar_link`(+`laser_frame`), `d435i_link`(+`d435i_color_frame`/`d435i_color_optical_frame`/`d435i_depth_frame`/`d435i_depth_optical_frame`, REP-103 optik frame hiyerarşisi), `rpi_hq_camera_link`(+optical frame), `rear_camera_link`(+optical frame)
- **Sensör link isimleri Zehra'nın adlandırmasıyla birleşti**: `d435i_link` (bizim eski `d435if_link` yerine) ve `rear_camera_link` (bizim eski `sjcam_link` yerine) — Zehra'nınkiler zaten gerçek Gazebo sensor plugin'ine bağlıydı, bizimkiler sadece placeholder'dı. `lidar_link`/`rpi_hq_camera_link` isim olarak zaten aynıydı.
- `base_link` sits 0.200 m above ground (yeni tekerlek yarıçapı); `base_footprint` is at ground level
- Şasi: 1200×450×245mm, 64kg (mekanik ekipten) — collision box + kütle + inertia güncellendi: `ixx=1.4001 iyy=8.0001 izz=8.7600` (analitik kutu, üçgen eşitsizliği doğrulandı; collision origin z=0.187 önceki turdan korunan mesh-türevli tahmin)
- Dingil mesafesi 780mm, teker aralığı 1060mm, tekerlek yarıçapı 200mm (mekanik ekipten). Tekerlek genişliği (`length=0.12`) ve tekerlek kütlesi/inertia'sı (3.5kg/tekerlek) Zehra'nın orijinal değerleri, dokunulmadı.
- Visual mesh: `meshes/tulpar_ika_assembly.stl` (149MB, ham/basitleştirilmemiş), scale 0.001 (mm) — performans etkisi henüz gerçek Gazebo testiyle ölçülmedi (bkz. spawn_entity eksikliği notu, Gazebo şu an bunu zaten kullanmıyor).
- **BİLİNEN KOZMETİK SORUN — "çifte tekerlek" görsel çakışması (16 Temmuz 2026)**: `tulpar_ika_assembly.stl` gövde+tekerlekler tek/birleşik bir mesh — mesh'in kendi içinde 4 köşede gömülü, statik (dönmeyen), ~166mm yarıçaplı (332mm çap) eski/mevcut tekerlek geometrisi var. Bizim ayrı `wheel_fl/rl/fr/rr` primitive silindirlerimiz (r=0.200, DiffDrive'ın döndürebilmesi için gerekli — mesh içindeki statik tekerlek dönemez) neredeyse AYNI konumda (dingil/iz farkı <2mm) ama **%20 daha büyük** yarıçapta duruyor. Sonuç: iki tekerlek üst üste biniyor, büyük olan primitive mesh'in kendi (küçük tekerleğe göre şekillenmiş) çamurluk boşluğundan dışarı taşıyor gibi görünüyor — özellikle ön tekerleklerde belirgin. **Konum hatası değil** (doğrulandı, <2mm fark) — 200mm yarıçap mekanik ekibin doğrulanmış hedef değeri, değiştirilmeyecek. Mekanik ekip gövdeden ayrık/temiz bir tekerlek mesh'i (veya tekerleksiz gövde mesh'i) gönderene kadar bu görsel çakışma kalacak; fiziksel/collision değerler (200mm) doğru ve etkilenmiyor.
- Sensors (hepsi Zehra'nın gerçek Gazebo sensor plugin'leriyle bağlı): YDLIDAR TG30 on `lidar_link` (`gpu_lidar`, topic `/scan`, 720 samples, 30m), RealSense D435i on `d435i_link` (`depth_camera`, topic `/d435i/depth/image_raw`), Pi HQ Camera+16mm (atış/nişan) on `rpi_hq_camera_link` (`camera`, topic `/rpi_hq_camera/image_raw`), SJCAM SJ4000 (arka izleme, 180° geriye dönük) on `rear_camera_link` (`camera`, topic `/rear_camera/image_raw`)
- **BİLİNEN SORUN — AÇIK, AYRI GÖREV**: `launch/gazebo.launch.py`'deki `parameter_bridge` hâlâ eski topic isimlerini bridge'liyor (`/camera/depth`, `/camera/camera_info`, `/camera/depth/points`) — yeni URDF'nin gerçek sensör topic'leriyle (`/d435i/depth/image_raw` vb.) eşleşmiyor. Spawn mimarisi artık düzeltildiği için (aşağıdaki nota bkz.) bu sorun artık **aktif/gerçek** — Gazebo gerçekten canlı URDF'yi simüle ediyor ama bridge eski topic isimlerini bekliyor, yani kamera verisi sessizce akmıyor. RTAB-Map'in kullandığı `/camera/depth/points` şu an çalışmıyor olabilir — henüz test edilmedi, ayrı bir görev olarak ele alınacak.
- IMU/GPS: mekanik ekibin planına göre AKV (Araç Kanıt Videosu, 20 Temmuz) sonrası entegre edilecek, URDF'de henüz yok.

### Launch file (`launch/gazebo.launch.py`)
Starts three nodes:
1. `robot_state_publisher` — processes the xacro and publishes `/robot_description` + TF
2. `gz_sim` — Gazebo Harmonic with `--render-engine ogre`
3. `parameter_bridge` — bridges ROS ↔ Gazebo topics: `/cmd_vel` (ROS→GZ), `/odom`, `/joint_states`, `/scan`, `/camera/depth` (GZ→ROS)

**MİMARİ EKSİKLİK ÇÖZÜLDÜ (16 Temmuz 2026):** Daha önce bu launch dosyasında hiçbir spawn mekanizması yoktu — robot Gazebo'ya sadece `worlds/*.sdf` içine gömülmüş statik bir `<model name='tulpar'>` bloğu olarak giriyordu, `urdf/robot.urdf.xacro`'daki değişiklikler Gazebo'nun simüle ettiği robotu hiç etkilemiyordu. Çözüldü: her 3 world dosyasından (`s01_robotlu_world.sdf`, `s02_hedef_world.sdf`, `e02_duz_world.sdf`) gömülü statik `<model name='tulpar'>` bloğu (içindeki eski `DiffDrive`/`JointStatePublisher` plugin'leriyle birlikte) çıkarıldı; `gazebo.launch.py`'ye `ros_gz_sim create` ile gerçek bir spawn adımı eklendi (`-topic robot_description` üzerinden canlı xacro'dan spawn ediyor, `TimerAction` ile `spawn_delay` argümanı kadar — varsayılan 5sn — Gazebo dünyasının yüklenmesini bekliyor, entity adı `tulpar` sabit tutuluyor çünkü bridge'in `/model/tulpar/tf` remap'i buna bağlı).
- **Test durumu**: sadece **s01 gerçek Gazebo testiyle doğrulandı** (ekran görüntüsü alındı, robot zeminde doğru duruyor, yeni mesh görünüyor, terrain sağlam). **s02 ve e02 aynı model-bloğu-kaldırma düzeltmesini aldı ama test edilmedi** — S02/E02 testlerine dönüldüğünde doğrulanmalı (S01 dünyasındaki gibi).
- **Bilinen kırılganlık — stale process**: Test sırasında gerçek bir sorunla karşılaşıldı: saatler önceki bir launch'tan kalan, hiç kapanmamış bir `robot_state_publisher` süreci hâlâ eski (terk edilmiş) `robot_description`'ı `/robot_description` topic'ine yayınlıyordu; `ros_gz_sim create -topic robot_description` bu ESKİ mesajı yakaladı (ROS2 topic'leri process'e özel değil, global — birden fazla publisher aynı topic'e yayın yapabilir). Sonuç: spawn edilen robot yanlış/eski mesh'lerle görünüyordu. **İleride benzer "spawn edilen robot beklenenden farklı görünüyor" belirtisiyle karşılaşılırsa önce `ps aux | grep robot_state_publisher` ile birden fazla instance çalışıp çalışmadığı kontrol edilmeli** — launch'lar arası eski süreçlerin tam kapatıldığından emin olmadan test tekrarlamak yanıltıcı sonuç verebilir.

### Worlds (`worlds/`)
| File | Purpose |
|------|---------|
| `s01_robotlu_world.sdf` | S-01: düz/boş zemin (`ground_plane` only) — terrain elemanları (rampa/yan eğim/blok/tümsek, 61 model) 16 Temmuz 2026'da kaldırıldı, bkz. Test scripts notu ve "S01 terrain temizliği" ilerleme notu. |
| `s02_hedef_world.sdf` | S-02 target detection: flat ground with A3 target board at 10 m. |
| `e02_duz_world.sdf` | E-02 acceleration: flat 30+ m track with distance markers. |

Hiçbir world dosyası artık robotu gömülü içermiyor — robot canlı `urdf/robot.urdf.xacro`'dan `gazebo.launch.py` tarafından spawn ediliyor (bkz. yukarıdaki "MİMARİ EKSİKLİK ÇÖZÜLDÜ" notu).

### Test scripts (`test_kanit/`)
Each test is a standalone ROS 2 node that publishes `/cmd_vel` and subscribes `/odom`. Pattern:
1. Wait up to 5 s for `/odom` (abort if none received — check Gazebo is running)
2. Execute movement sequence, collecting timestamped data
3. Write results to a CSV next to the script
4. Companion `*_grafik.py` scripts read the CSV and produce matplotlib plots

| Directory | Tests |
|-----------|-------|
| `S01/` | Ramp stop/brake, side slope, 15 cm block, flat ground, full course — **16 Temmuz 2026'dan itibaren GEÇERSİZ**: `s01_robotlu_world.sdf`'den terrain elemanları (rampa/yan eğim/blok/tümsek) kaldırıldı, world artık düz/boş zemin. Bu scriptler artık test ettikleri engelleri bulamaz. Orijinal terrain'li world `worlds/s01_robotlu_world_ORIJINAL_YEDEK.sdf.bak`'ta duruyor, gerekirse geri eklenebilir. |
| `S02/` | Target detection & lock (geometric simulation using camera FoV math) |
| `E02/` | 30 m straight-line acceleration at 0.5 m/s |

### Behavior Tree (`behavior_trees/`)
`ana_tree.xml` — main Behavior Tree draft (BehaviorTree.CPP v4, `BTCPP_format="4"`, Groot2-openable). Bu BT sadece TAM-OTONOM koşuyu (şartname 1.1 - 2. Koşu) modelliyor; Manuel koşu (1. Koşu, RC/kumanda ile) bu ağacın dışında, ELRS/RC override katmanında yönetiliyor. Sequence: wait for system ready → repeat until course end → ReactiveFallback between three branches: (1) sign-detected shoot flow (stop Nav2, lock target, fire laser, resume Nav2), (2) `DikEgimStopAkisi` — rampadaki işaretli stop noktasında (`StopNoktasindaMi`) tam durup en az 2 sn bekleme (`DurVeBekle`, şartname 6.10), (3) default autonomous driving (Nav2 `NavigateToPose` placeholder). Parkurdaki her tabela BT node'u gerektirmiyor — sadece davranış değişikliği gerektirenler (atış, dik eğim stop) burada modellendi; su geçişi, çakıllı yol, yan eğim, dik engel, trafik konileri, kayar engel ve engebeli arazi gibi diğer bölümler Nav2/costmap parametreleriyle sürekli geçiliyor (Zehra'nın parkur algoritmaları kapsamı, ayrı BT node'u gerektirmiyor). All action/condition nodes now have real C++ implementations in `tulpar_bt/` (see below) — no longer placeholders.

### Behavior Tree Executor (`tulpar_bt/`)
Yeni C++ paketi: `tulpar_bt` (ament_cmake). Symlink kurulumu gerekiyor — bkz. Build & Run bölümündeki "One-time setup" notu.

9 BT node'unun C++ implementasyonu tamamlandı (artık placeholder değiller):
- **TAM İMPLEMENTE**: `WaitForSystemReady`, `OtonomSurus`, `ModDegisimiYap`, `DevamEt`, `StopNoktasindaMi`, `DurVeBekle`
- **YAZILIMSAL TAMAMLANDI** (donanım/ekip verisi bekleniyor): `TabelaAlgılandiMi` (Emin'in `/tabela_tespit` yayınını bekliyor), `HedefTespitYap` ve `AtisYap` (lazer donanımını bekliyor — servis yoksa `simulate_mode` ile simüle edilir)

`WaitForSystemReady`, Nav2 lifecycle_manager entegrasyonu yapar: `bt_navigator`/`controller_server`/`planner_server`'ın ACTIVE durumda olduğunu `lifecycle_msgs/GetState` ile kontrol eder.

Çalıştırma: `ros2 run tulpar_bt bt_executor` (ya da `ros2 launch tulpar_bt bt_executor.launch.py`)

**Bilinen davranış**: `ana_tree.xml`'deki `Repeat` düğümü `ForceSuccess` ile sarılı — tek bir dal FAILURE dönse bile döngü kalıcı durmuyor (BT.CPP'de `Repeat`'in doğal davranışı child FAILURE'da kalıcı durmaktır). Parkur bitiş koşulu henüz tanımlı değil — Gün 4'te ele alınacak.

`OtonomSurus`'un hedef kaynağı `/tulpar_bt/hedef_pose` topic'i — Zehra'nın parkur algoritması yayınlayacak, henüz bağlı değil.

Gerçek uçtan uca test sahte/mock Nav2 (fake lifecycle node'lar + fake `navigate_to_pose` action server) ile yapıldı ve doğrulandı. Gerçek Gazebo+Nav2 testi Gün 4'te.

### RTAB-Map SLAM (`launch/rtabmap.launch.py`)

Lidar-öncelikli 2D+3D SLAM: `/scan` ile ICP tabanlı (`Reg/Strategy=1`) occupancy grid, RGB kamera gerektirmiyor. Kurulduğu sırada URDF `camera_link`/RealSense D455/`camera/depth` kullanıyordu; Gün 4'te URDF Zehra'nın branch'i temel alınarak `d435i_link`/RealSense D435i/`/d435i/depth/image_raw`'a geçti ve spawn mimarisi düzeltildiği için Gazebo artık gerçekten bunu simüle ediyor, ama `gazebo.launch.py`'nin bridge'i henüz güncellenmedi (yukarıdaki **BİLİNEN SORUN — AÇIK, AYRI GÖREV** notuna bkz.) — bu yüzden RTAB-Map'in `/camera/depth/points` bağımlılığı şu an muhtemelen çalışmıyor, henüz yeniden test edilmedi.

Çalıştırma: `gazebo.launch.py` + ayrı terminalde `rtabmap.launch.py`.

`/camera/depth/points` ayrı 3D görsel katman olarak mevcut, SLAM grafiğine karışmıyor.

`map_always_update:=true` şart — yoksa harita ilk taramadan sonra donuyor.

Bu görevde 4 gerçek altyapı bug'ı bulunup düzeltildi: `GZ_SIM_RESOURCE_PATH` eksikliği (dünya hiç yüklenmiyordu), 3 world SDF'sinde eksik world-seviyesi Gazebo plugin'leri (sensörler sessizce veri üretmiyordu), `odom`→`base_footprint` TF köprüsü eksikliği, `ros-jazzy-diagnostic-updater` ABI uyumsuzluğu (`apt upgrade` ile çözüldü).

`s02_hedef_world.sdf` ve `e02_duz_world.sdf`'ye aynı plugin düzeltmesi uygulandı ama HENÜZ TEST EDİLMEDİ — S02/E02 testlerine dönüldüğünde doğrulanmalı.

### Yer İstasyonu (`yer_istasyonu/`)
Electron + React + rclnodejs ile yazılmış masaüstü kontrol konsolu. Main process'te rclnodejs.init() ile bir ROS 2 node'u ("yer_istasyonu_node") oluşturuluyor ve DDS ağına katılıyor. Gün 2'de Emin'in KTR madde 3.3.1 görevi olan telemetri paneli ve WebRTC video alıcı eklendi (normalde Emin'in kapsamı, Talha üstlendi):

- **Telemetri paneli**: hız/batarya/sıcaklık/eğim göstergeleri, tek birleşik topic üzerinden besleniyor: `/telemetri/veri` (`std_msgs/String`, JSON payload: `hiz`, `batarya_yuzde`, `sicaklik_c`, `egim_derece`, `zaman_damgasi`).
- **WebRTC video alıcı**: RTCPeerConnection tabanlı, signaling server URL'i `config.js`'ten alınıyor (env: `VITE_SIGNALING_URL`).
- **Durum etiketleri**: UI, IPC köprüsü, rclnodejs subscriber mantığı ve WebRTC peer/negotiation mantığı **TAM İMPLEMENTE**. `/telemetri/veri`'ye yayın yapan gerçek Teensy/Jetson köprüsü (Gün 6'da gelecek) ve WebRTC signaling server (Zehra/Emin'in Gün 4 işi) henüz yok — bu ikisi **YAZILIMSAL TAMAMLANDI - bekleniyor**. Veri/bağlantı gelmezse panel crash etmeden "veri yok/bağlantı bekleniyor" gösterip sürekli yeniden dener.
- **Düzeltilen bug**: preload script'i `package.json`'daki `"type":"module"` yüzünden electron-vite tarafından ESM (`.mjs`) olarak build ediliyordu; Electron'un sandboxed preload yükleyicisi ESM `import` syntax'ını desteklemiyor, bu yüzden preload sessizce yüklenemiyor ve `window.api` hep `undefined` kalıyordu (Gün 1'de fark edilmemişti çünkü preload boştu). `electron.vite.config.mjs`'e preload için CJS çıktı zorunluluğu eklenerek düzeltildi.

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
(`urdf/robot.urdf.xacro`'daki `DiffDrive` plugin'inden doğrulandı, 16 Temmuz 2026 — Zehra'nın orijinal değerleri, henüz mekanik/motor ekibiyle netleştirilmedi)
- Wheel separation: 1.06 m; wheel radius: 0.200 m
- Max linear velocity: 1.0 m/s; max angular velocity: 3.0 rad/s
- Max wheel torque: 25.0 Nm; max linear acceleration: 2.0 m/s²
- Physics: ODE solver, 1 ms step, 1000 Hz update rate, 100 iterations

## Gün Bazlı İlerleme Notları

- Gün 1 (14 Temmuz 2026) tamamlandı: BT taslağı (behavior_trees/), yer istasyonu iskeleti (yer_istasyonu/), repo temizliği ve worlds/ install bug düzeltmesi, PR #1 açıldı ve yazilim_gelistirme'ye merge edildi.
- Gün 2 (14 Temmuz 2026 - devam) BT node implementasyonu tamamlandı: tulpar_bt paketi, 9 node (6 tam implemente, 3 yazılımsal tamamlandı/donanım+ekip bekliyor), 3 gerçek sorun bulunup çözüldü (colcon paket keşfi, Nav2 çökme riski, Repeat kalıcı ölüm riski).
- Gün 2 (devam) Emin'in KTR 3.3.1 görevi (telemetri paneli + WebRTC video alıcı) üstlenildi ve tamamlandı, ayrıca Gün 1'den kalma gizli bir preload ESM/CJS bug'ı bulunup düzeltildi.
- Gün 3 (devam) RTAB-Map SLAM kuruldu ve gerçek Gazebo testiyle doğrulandı (harita oluşumu rviz'de teyit edildi), 4 gerçek altyapı bug'ı bulunup düzeltildi.
- Gün 4 (16 Temmuz 2026) URDF v3.0: yeni CAD assembly'den (`!!tulpar+ika+assembly.stl`, 16.000 parça) gövde+tekerlek mesh'leri çıkarıldı, decimate edildi, kütle/inertia hesaplandı, URDF tamamen güncellendi (yeni boyutlar, 3 yeni sensör linki). RViz ile görsel doğrulama yapıldı, Gazebo fizik testi mimari eksiklik (spawn_entity yok) nedeniyle YAPILAMADI — ayrı görev olarak bekliyor. Süreçte 3 gerçek hesaplama hatası bulunup düzeltildi: negatif eylemsizlik momenti (winding tutarsızlığı), ön/arka işaret hatası (sensör konumları ters çıkıyordu), ve mesh-türevli inertia'nın üçgen eşitsizliğini ihlal etmesi (analitik kutuya geçildi).
- Gün 4 (devam) **Strateji pivotu**: mekanik ekip kendi orijinal `tulpar_ika_assembly.stl`'ini Blender'da inceleyip eksiksiz olduğunu doğruladı — sorun bizim decimation pipeline'ımızdaymış. Kendi mesh yaklaşımımızdan (govde/teker v2/v3, 5 dosya) vazgeçildi, silindi. Onun yerine Zehra'nın `feature/zehra-faz1-gun1` branch'indeki `urdf/robot.urdf.xacro` + ham `tulpar_ika_assembly.stl` (149MB) temel alındı, sadece fiziksel parametreler (1200×450×245mm/64kg/780mm/1060mm/200mm + yeniden hesaplanan inertia) mekanik ekipten gelen değerlerle güncellendi. Sensör link isimleri Zehra'nınkiyle birleşti (`d435i_link`, `rear_camera_link`) — kendi placeholder linklerimizden (`d435if_link`, `sjcam_link`) vazgeçildi çünkü Zehra'nınkiler zaten gerçek Gazebo sensor plugin'lerine bağlıydı. Yeni bilinen sorun: `gazebo.launch.py`'nin bridge'i henüz yeni sensör topic isimleriyle güncellenmedi.
- Gün 4 (devam) **Spawn mimarisi eksikliği kapatıldı**: `worlds/*.sdf`'lerdeki statik gömülü `tulpar` modeli kaldırıldı, `gazebo.launch.py`'ye `ros_gz_sim create` ile canlı-URDF-spawn eklendi. S01 gerçek Gazebo testiyle doğrulandı (ekran görüntüsü alındı); S02/E02 aynı düzeltmeyi aldı ama test edilmedi. Süreçte gerçek bir stale-process bug'ı bulundu ve not düşüldü (birden fazla `robot_state_publisher` aynı `/robot_description` topic'ine yayın yapınca `create` yanlış/eski olanı yakalayabiliyor). Bridge topic uyumsuzluğu artık teorik değil aktif bir sorun — Gazebo gerçekten yeni URDF'yi simüle ettiği için kamera topic'leri muhtemelen akmıyor, ayrı görev olarak açık kaldı.
- Gün 4 (devam) **Kapsamlı denetim + düzeltmeler**: Repo geneli denetlendi, 3 kritik/1 önemli bulgu tespit edilip düzeltildi — CLAUDE.md'nin Worlds bölümü spawn mimarisi notuyla çelişiyordu (eski/statik anlatım silindi), Overview ve Key Physical Parameters bölümleri aylardır güncellenmemiş eski değerler taşıyordu (64kg/1200×450×245mm/Ø400mm ve gerçek DiffDrive değerleriyle güncellendi), `package.xml`'de `xacro` bağımlılığı eksikti (eklendi), `meshes/tulpar_yeni.stl` (61MB, düz git blob) artık hiçbir yerden referans edilmiyordu (silindi).
- Gün 4 (devam) **S01 terrain temizliği**: `worlds/s01_robotlu_world.sdf`'deki 61 terrain modeli (rampa_asc/desc ×20+20, rampa_tepe, yan_giris/cikis/egim ×10, blok_giris/15cm ×4, tumsek ×6) kaldırıldı, world artık sadece `ground_plane` içeriyor. Silmeden önce `worlds/s01_robotlu_world_ORIJINAL_YEDEK.sdf.bak` yedeği alındı (`.gitignore`'a eklendi, repoya commit edilmiyor). **Sonuç: `test_kanit/S01/` scriptleri artık geçersiz** (test ettikleri rampa/blok/tümsek engelleri artık world'de yok) — bkz. Test scripts notu. Gazebo testiyle doğrulandı: araç boş düz zeminde doğru görünüyor.
