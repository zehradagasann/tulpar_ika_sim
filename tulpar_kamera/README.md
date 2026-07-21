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

- **ROS2 yayini:** tespit sonuclari su an stdout'a basiliyor. `/detections` ve
  `/tulpar_bt/atis_event` topic'lerine baglanmasi lazim (Talha ile field yapisi
  netlestirilecek — X/Y/Z var mi).
- **Renk kaymasi:** ISP ciktisinda magenta ton var. Ham bayer analizi
  (`tools/ham_bayer_analiz.py`) sensor ve optigin SAGLAM oldugunu gosterdi
  (yesil kanal normal, R/G=0.43 B/G=0.47 — ham veri icin beklenen tablo).
  Kayma Argus ISP katmaninda ekleniyor. `wbmode=2` magenta'yi maviye ceviriyor,
  yani mod degistirmek etkili ama tam oturmuyor. Gun isiginda test edilmeli;
  yarisma acik havada oldugu icin sorun sahada konusuz kalabilir.
- **Odak:** Pi HQ + 16 mm telefoto lens manuel odakli ve su an belirgin sekilde
  odak disi. Hedef tespiti icin ayarlanmali.
- **Uctan uca gecikme** olculmedi. Bant genisligi dogrulandi (5.76 Mbps).
- **RealSense D435if** kolu eklenecek (kablo bekleniyor). `--source realsense`
  altyapisi hazir.

## tools/

Tanilama scriptleri, uretimde kullanilmaz:

- `test_receiver.html` — tarayicida calisan WebRTC alici. Electron/ROS2 kurmadan
  gonderici tarafini dogrulamak icin. Bit hizi, FPS, jitter, paket kaybi gosterir.
- `ham_bayer_analiz.py` — v4l2'den alinan ham bayer kareyi analiz eder, renk
  sorununun ISP'den mi optikten mi geldigini ayirt eder. Argus kullanmaz.
- `renk_testi.py` — ISP ciktisini belirli bir `wbmode` ile yakalar.
