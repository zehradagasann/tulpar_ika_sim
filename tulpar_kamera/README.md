# tulpar_kamera

Jetson Orin NX uzerinde calisan kamera node'u. Tek bir Argus oturumu acar,
goruntuyu GStreamer `tee` ile iki kola ayirir:

- **Kol A — WebRTC yayini:** donanim H.264 encoder (`nvv4l2h264enc`) ile
  1920x1080@30, ~5.8 Mbps. Yer istasyonuna canli video.
- **Kol B — Hedef tespiti:** 1280x720 BGR kare -> YOLOv11 (TensorRT) -> PID
  taret komutu hesabi.

Ikisi ayni anda calisir. Onceki durumda `pid_target_tracking_jetson.py` ve
WebRTC gonderici kamerayi ayri ayri acmaya calisiyordu ve bu mumkun degildi
(asagidaki Argus notuna bakin).

## Kurulum (Jetson)

```bash
sudo apt install -y gstreamer1.0-nice v4l-utils
pip3 install websockets --break-system-packages
```

**DeepSORT (`deep-sort-realtime`) kurulumu — DIKKAT, kor kore `pip3 install
deep-sort-realtime --break-system-packages` calistirmayin:**
paket varsayilan olarak numpy'i 1.26.4'ten 2.x'e yukseltiyor ve ayri bir
`opencv-python` (pip) paketi getiriyor — bu ikisi birlikte `ultralytics`'i
(matplotlib uzerinden, numpy 1.x'e derlenmis bir uzanti importunda) KIRIYOR
ve Jetson'in CUDA/GStreamer destekli sistem `cv2`'sini golgeliyor (27 Tem
2026'da canli test sirasinda bulundu, `ultralytics` import hatasi verdi).
Doğru sıra:

```bash
pip3 install deep-sort-realtime --break-system-packages
pip3 install 'numpy<2' 'scipy==1.11.4' --break-system-packages   # deep-sort-realtime'in yukselttigi surumleri geri al
pip3 uninstall -y opencv-python --break-system-packages          # sistem cv2'sini (JetPack/CUDA) golgelemesin
```

Kurulumdan sonra dogrulama (hepsi hatasiz import etmeli):
```bash
python3 -c "from ultralytics import YOLO; import pyrealsense2, cv2; from deep_sort_realtime.deepsort_tracker import DeepSort; print(cv2.__file__)"
# cv2.__file__ /usr/lib/... altinda olmali (pip .local/site-packages'ta DEGIL)
```

**Arka kamera port sabitleme (bir kez):** arka kamera (Sjcam) USB capture
card'i ham `/dev/videoN` yerine kararli bir isimle acilsin diye udev kurali
kurulmali - kurulmazsa birden fazla USB kamera varken numaralandirma
baglanti sirasina gore kayabilir ve node yanlis/olmayan bir aygiti acmaya
calisir:

```bash
sudo cp udev/99-tulpar-arka-kamera.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -l /dev/tulpar_arka_kamera   # gercek /dev/videoN'e isaret etmeli
```

`gstreamer1.0-nice` **zorunlu**. Eksikse `webrtcbin` yuklenir ama sink pad
uretemez ve node "request pad alinamadi" diye hata verir; log'da
`libnice elements are not available` gorunur.

Bu bagimliliklar `package.xml`'e yazilmadi: rosdep bazi apt anahtarlarini
cozemiyor ve `rosdep install --from-paths src` calistiran herkesin kurulumunu
bozuyordu. Paket derlenmek icin bunlara ihtiyac duymaz, sadece calisma aninda
gerekir - yani bu paket depoda dursa da kimsenin `colcon build`'ini bozmaz.

**Port notu:** signaling sunucusu 8080'i dinler. Konsolun `config.js`
varsayilani da ayni port oldugu icin uyumlular; ayni makinede 8080'i tutan
baska bir servis varsa `--port` ile degistirilebilir.

## Calistirma

Sira onemli: once signaling sunucusu, sonra izleyici (konsol), en son node.

```bash
# 1) Signaling sunucusu
ros2 run tulpar_kamera signaling_server        # veya: python3 signaling_server.py

# 2) Izleyici: konsolu ac, ya da tools/test_receiver.html'i tarayicida ac

# 3) Kamera node'u  (boot sonrasi ILK kamera sureci olmali!)
ros2 run tulpar_kamera kamera_node --signaling ws://127.0.0.1:8080/yer-istasyonu-video
```

Node once acilirsa da sorun degil: offer ve ICE adaylari saklanir, izleyici
baglandiginda otomatik tekrar gonderilir.

### Lidar fuzyon node'u (`lidar_fuzyon_node.py`)

Kamera + YDLidar TG30 nokta bulutu dogrulamasi icin ONCE TF agacinin
(robot_state_publisher) ve lidar driver'inin ayakta olmasi sart:

```bash
# 1) TF agaci + YDLidar TG30 (tulpar_description paketinden)
ros2 launch tulpar_description bringup.launch.py

# 2) Kamera node'u (yukaridaki gibi, ayni anda)
ros2 run tulpar_kamera kamera_node --signaling ws://127.0.0.1:8080/yer-istasyonu-video

# 3) Fuzyon node'u
ros2 run tulpar_kamera lidar_fuzyon_node
```

`bringup.launch.py` calismiyorsa (TF yoksa) node crash ETMEZ - sadece
"TF donusumu basarisiz" uyarisini throttle'layarak basar ve o karedeki
dogrulamayi atlar. `ros2 topic echo /tulpar_kamera/fuzyon_engelleri` ile
cikti PointCloud2'yi, log'daki 5 saniyelik "[ozet] X/Y dogrulandi"
satirlariyla dogrulama oranini izleyebilirsiniz.

### Yer istasyonu tarafi

`yer_istasyonu/.env` dosyasina Jetson'in adresi yazilmali (kod degisikligi
gerekmez, `config.js` bu degiskeni okuyor):

```
VITE_SIGNALING_URL=ws://192.168.100.10:8080/yer-istasyonu-video
```

USB-RNDIS uzerinden calisiyorsan `192.168.55.1`, Ethernet'te `192.168.100.10`.

Signaling protokolu Talha'nin `yer_istasyonu/src/renderer/src/components/VideoAlici.jsx`
bileseniyle birebir uyumludur:
`izleyici-merhaba` -> `offer` -> `answer` -> karsilikli `ice-candidate`.

## BILINEN SORUN: Argus daemon, boot basina tek oturum

JetPack 7.2'de `nvarguscamerasrc` boot sonrasi **yalnizca bir kez** acilabiliyor.
Ikinci acilis su hatayi veriyor:

```
nvbuf_utils: dmabuf_fd -1 mapped entry NOT found
NvBufSurfaceFromFd Failed
```

21 Tem 2026 testlerinde defalarca dogrulandi:

- Ilk oturum her zaman temiz calisiyor, ikincisi her zaman bozuluyor.
- Birinci oturum duzgun EOS ile kapansa bile ikincisi yine bozuluyor.
- `sudo systemctl restart nvargus-daemon` **kurtarmiyor**; sadece reboot kurtariyor.
- `wbmode` gibi ozellikleri pipeline calisirken degistirmek de daemon'u dusuruyor
  (PLAYING oncesi verilmeli).

Bu node'un tek-oturum mimarisi bu sorunu **pratikte ortadan kaldirir**: kamera
bir kez acilir ve gorev boyunca acik kalir. Gelistirme sirasinda node'u her
yeniden baslattiginda reboot gerekir.

Kalici cozum arastirilacak (Argus baypasi + kendi debayer'imiz bir secenek).

## ACIK ISLER

- ~~ROS2 yayini~~ **TAMAMLANDI** — `/detections` (`Detection2DArray`, Zehra'nin
  semasi) ve `/tulpar_kamera/atis_event` yayinlaniyor (bkz. `detection_publisher.py`).
- ~~RealSense D435if kolu~~ **TAMAMLANDI** — kablo geldi, D435if artik asil
  tespit kamerasi (renk+derinlik, `tespit_dongusu`), Pi HQ sadece atis yayini.
- ~~Kamera port sabitleme (udev)~~ **TAMAMLANDI** — `udev/99-tulpar-arka-kamera.rules`,
  bkz. yukaridaki Kurulum bolumu. D435if/Pi HQ'nun udev'e ihtiyaci yok (RealSense
  kendi USB enumerasyonunu kullaniyor, Pi HQ sabit CSI baglantisi).
- ~~DeepSORT nesne takibi~~ **TAMAMLANDI ve DONANIMDA DOGRULANDI (27 Tem 2026)**
  — `tespit_dongusu` artik YOLO kutularini `DeepSort` (Kalman + MobileNetv2
  embedder, KTR 3.3.2) ile takip ediyor; `/detections`'taki
  `track_id`/`track_id_valid` artik gercek (sadece `is_confirmed()` VE o
  karede gercek tespitle eslesmis track'ler yayinlanir). PID/atis mantigi
  (`find_shooting_target`) BILEREK ham YOLO kutularini kullanmaya devam
  ediyor — takip gecikmesi atis kilitlenmesini yavaslatmasin diye. Jetson'da
  gercek D435if + TensorRT engine ile uctan uca test edildi: iki
  `shooting_target` tespiti 14 saniye boyunca `track_id=1`/`track_id=2`
  olarak hic degismeden (ID switch yok) takip edildi.
  **Kurulum uyarisi**: `deep-sort-realtime`'i kurarken yukaridaki
  numpy/scipy/opencv-python notuna MUTLAKA uyun — kurulum sirasinda bu
  bulundu, atlanirsa `ultralytics` sessizce kirilir.
- ~~D435if + YDLidar TG30 nokta bulutu fuzyonu~~ **TAMAMLANDI ve DONANIMDA
  DOGRULANDI (27 Tem 2026)** — `lidar_fuzyon_node.py` (KTR/roadmap Gun 6-7).
  RPLIDAR degil, gercek donanim YDLidar TG30 (bkz. `tulpar_description/config/
  ydlidar_TG30.yaml`). Bagimsiz bir ROS2 node: `/detections` + `/d435if/depth/
  camera_info` (piksel->3D pinhole geri izdusumu) + `/scan`'i dinler, tf2 ile
  kamera noktasini `laser_frame`'e tasiyip LaserScan'in ayni bearing'indeki
  okumayla karsilastirir (varsayilan tolerans 0.35m); SADECE iki sensorun de
  ANLASTIGI noktalari `target_frame` (varsayilan odom) icinde PointCloud2
  olarak `/tulpar_kamera/fuzyon_engelleri`'e yayinlar - bilerek bir dogrulama
  FILTRESI, kamera-only tespitlerin yerini almaz (onlar zaten obstacle_injector
  uzerinden geciyor). Gercek robot_state_publisher (bringup.launch.py) + gercek
  YDLidar TG30 + gercek D435if ile uctan uca test edildi: 5 saniyelik pencerede
  29 tespitten 6'si lidar tarafindan bagimsiz dogrulandi.
  **Not**: kamera_node.py artik `/d435if/depth/camera_info` de yayinliyor
  (asagida) - bu olmadan ne bu node ne de obstacle_injector gercek robotta
  calisabilir, daha once hic yayinlanmiyordu.
- **Renk kaymasi:** ISP ciktisinda magenta ton var. Ham bayer analizi
  (`tools/ham_bayer_analiz.py`) sensor ve optigin SAGLAM oldugunu gosterdi
  (yesil kanal normal, R/G=0.43 B/G=0.47 — ham veri icin beklenen tablo).
  Kayma Argus ISP katmaninda ekleniyor. `wbmode=2` magenta'yi maviye ceviriyor,
  yani mod degistirmek etkili ama tam oturmuyor. Gun isiginda test edilmeli;
  yarisma acik havada oldugu icin sorun sahada konusuz kalabilir.
- **Odak:** Pi HQ + 16 mm telefoto lens manuel odakli ve su an belirgin sekilde
  odak disi. Hedef tespiti icin ayarlanmali.
- **Uctan uca gecikme** olculmedi. Bant genisligi dogrulandi (5.76 Mbps).
- **Taret ±90° yazilimsal sinir + endstop**: Talha'nin firmware'i
  (`TaretEksenKatmani`) derece_basina_adim/limit_derece degerlerini bekliyor —
  elektronik ekipten deger gelince Talha'ya iletilecek.

## tools/

Tanilama scriptleri, uretimde kullanilmaz:

- `test_receiver.html` — tarayicida calisan WebRTC alici. Electron/ROS2 kurmadan
  gonderici tarafini dogrulamak icin. Bit hizi, FPS, jitter, paket kaybi gosterir.
- `ham_bayer_analiz.py` — v4l2'den alinan ham bayer kareyi analiz eder, renk
  sorununun ISP'den mi optikten mi geldigini ayirt eder. Argus kullanmaz.
- `renk_testi.py` — ISP ciktisini belirli bir `wbmode` ile yakalar.
