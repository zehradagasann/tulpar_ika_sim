#!/usr/bin/env python3
"""
Tulpar IKA - Birlesik kamera node'u.

NEDEN BU DOSYA VAR:
JetPack 7.2'de Argus daemon'u, boot sonrasi ikinci nvarguscamerasrc oturumunu
servis edemiyor (nvbuf_utils: dmabuf_fd -1 / NvBufSurfaceFromFd Failed) ve
`systemctl restart nvargus-daemon` bunu kurtarmiyor - sadece reboot kurtariyor.
21 Tem testlerinde bu davranis tekrar tekrar dogrulandi (ilk oturum her zaman
temiz, ikincisi her zaman bozuk; birinci oturum temiz EOS ile kapansa bile).

Bu yuzden kamerayi ACAN TEK BIR SUREC var: bu node. Argus bir kez acilir,
gorev boyunca acik kalir. MIMARI (22 Tem itibariyle iki bagimsiz kamera):

    nvarguscamerasrc (Pi HQ, 1920x1080@30, tek Argus oturumu)
        |
        +-- nvvidconv -> nvv4l2h264enc (DONANIM) -> rtph264pay -> webrtcbin
            Konsola giden ATIS kamerasi akisi. Overlay YOK - dusuk CPU,
            dusuk gecikme. Nisan artisi/kutu konsol tarafinda cizilir.
            Argus'un TEK tuketicisi bu - tee/appsink YOK artik (asagi bak).

    RealSense D435if (pyrealsense2, 1280x720@30, ayri thread)
        |
        +-- renk karesi -> YOLO -> find_shooting_target -> PID (pan/tilt)
        +-- hizalanmis derinlik karesi -> bbox merkezinde derinlik -> Det.depth_m
        +-- ROS2 /detections + /tulpar_kamera/atis_event (DetectionPublisher)

RealSense kendi USB3 baglantisini kullandigi icin Argus'tan tamamen
bagimsiz - YOLO/PID/ROS artik Pi HQ'nun tek-Argus-oturumu kisitina hic
tabi degil. (Eskiden ikisi ayni Argus oturumunu paylasan bir GStreamer
`tee` ile bagliydi; D435if entegrasyonuyla bu ayrim gereksizlesti ve
kaldirildi.)

ESKI UDP AKISI KALDIRILDI:
pid_target_tracking_jetson.py'deki cv2.VideoWriter + x264enc + udpsink yolu
bu mimaride gereksiz (WebRTC onun yerini aliyor). Zaten x264enc
gstreamer1.0-plugins-ugly paketinde ve Jetson'da kurulu olmadigi icin
"[UYARI] UDP cikis pipeline'i acilamadi" hatasinin sebebi buydu.

KULLANIM:
    # Terminal 1
    python3 signaling_server.py
    # Terminal 2 (konsol/test sayfasi baglandiktan SONRA)
    python3 tulpar_kamera_node.py --signaling ws://127.0.0.1:8080/yer-istasyonu-video

    # Sadece video, YOLO olmadan (hizli test icin):
    python3 tulpar_kamera_node.py --signaling ws://... --tespit-yok
"""
import argparse
import asyncio
import json
import logging
import threading
import time

import numpy as np

import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
gi.require_version("GstWebRTC", "1.0")
gi.require_version("GstSdp", "1.0")
from gi.repository import GLib, Gst, GstSdp, GstWebRTC  # noqa: E402,F401

import websockets  # noqa: E402

# ROS2 koprusu. rclpy SADECE enabled=True iken import edilir,
# yani --ros-yok ile calisirken ROS kurulu olmasa bile sorun cikmaz.
from detection_publisher import Det, DetectionPublisher  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [kamera-node] %(message)s")
log = logging.getLogger("kamera-node")

# ---------------- AYARLAR ----------------
MODEL_PATH = "/home/tulpar/best.engine"
SHOOTING_TARGET_CLASS_ID = 13   # dataset_combined/data.yaml sirasi ile ayni
CONF_THRESHOLD = 0.5
LOCK_THRESHOLD_PX = 15

# Yayin (Pi HQ / Argus) cozunurlugu - konsola giden ATIS kamerasi goruntusu
YAYIN_W, YAYIN_H, YAYIN_FPS = 1920, 1080, 30
# Tespit (RealSense D435if) cozunurlugu - YOLO'ya giren renk karesi
TESPIT_W, TESPIT_H, TESPIT_FPS = 1280, 720, 30

# KTR / Gun4: 7.5 Mbps sinirinin altinda kalinacak. Guvenlik payiyla 6 Mbps.
BITRATE_KBPS = 6000

# --- RealSense derinlik ---
# bbox merkezi etrafinda (2*yarim+1)^2 piksellik pencerede medyan alinir -
# tek piksele guvenmek specular yansima/no-return karelerinde yanlis derinlik verir.
REALSENSE_DERINLIK_YARIM_PENCERE = 2
REALSENSE_MIN_DERINLIK_M = 0.2
REALSENSE_MAX_DERINLIK_M = 8.0   # D435 spec: ~10m ama pratikte 8m sonrasi gurultu artiyor

# --- ROS2 ---
# D435if artik GERCEKTEN tespit kamerasi (bkz. yukaridaki mimari notu) -
# /detections koordinatlari ve derinligi bu kameradan geliyor, frame_id ile
# tutarli.
ROS_FRAME_ID = "d435if_color_optical_frame"
# Atis bolgesi: goruntu merkezine gore normalize yari-genislik/yukseklik.
# LOCK_THRESHOLD_PX ile ayni fikir, ama cozunurlukten bagimsiz.
ATIS_BOLGESI = (0.25, 0.25)
# Hedef bu kadar ardisik kare bolgede kalirsa ACTION_LOCK_STABLE yayilir.
LOCK_STABLE_FRAMES = 15
STUN_SERVER = "stun://stun.l.google.com:19302"

PIPELINE_DESC = (
    "nvarguscamerasrc sensor-id=0 ! "
    "video/x-raw(memory:NVMM),width={yw},height={yh},framerate={fps}/1 ! "
    "queue max-size-buffers=4 leaky=downstream ! "
    "nvvidconv ! video/x-raw(memory:NVMM),format=NV12 ! "
    "nvv4l2h264enc bitrate={bitrate} insert-sps-pps=true idrinterval=30 maxperf-enable=true ! "
    "h264parse config-interval=-1 ! "
    "rtph264pay config-interval=1 pt=96 ! "
    # leaky: izleyici bagli degilken webrtcbin paketleri bosaltmaz, bu queue
    # dolup encoder'a geri basinc yapabilir. Sahada yer istasyonu koparsa
    # atis kamerasi akisi donmasin diye eski kareler dusuruluyor. (Eskiden
    # bu ayrica tee uzerinden YOLO kolunu da bloke ediyordu - artik YOLO
    # RealSense'te, bagimsiz, bu queue'dan etkilenmiyor.)
    "queue leaky=downstream max-size-buffers=60 ! "
    'capsfilter caps="application/x-rtp,media=video,encoding-name=H264,payload=96"'
)


class PID:
    """pid_target_tracking_jetson.py'den oldugu gibi tasindi."""

    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0.0
        self.prev_error = 0.0

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0

    def update(self, error, dt):
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        self.prev_error = error
        return self.kp * error + self.ki * self.integral + self.kd * derivative


def find_shooting_target(results, conf_threshold=CONF_THRESHOLD):
    """Sadece class_id==SHOOTING_TARGET_CLASS_ID tespitlerini filtreler,
    en yuksek confidence'liyi doner. Donen: (x_c, y_c, conf) veya None."""
    if len(results.boxes) == 0:
        return None
    best_box = None
    best_conf = 0.0
    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        if cls_id != SHOOTING_TARGET_CLASS_ID:
            continue
        if conf < conf_threshold:
            continue
        if conf > best_conf:
            best_conf = conf
            best_box = box
    if best_box is None:
        return None
    x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()
    return (x1 + x2) / 2, (y1 + y2) / 2, best_conf


def _derinlik_olc(depth_frame, cx, cy,
                   yarim=REALSENSE_DERINLIK_YARIM_PENCERE,
                   min_m=REALSENSE_MIN_DERINLIK_M, max_m=REALSENSE_MAX_DERINLIK_M):
    """bbox merkezi etrafindaki kucuk pencerede medyan derinlik (metre).

    Tek piksele guvenmek yerine pencere almamizin sebebi: specular yansima
    veya IR golgesi tek pikselde 0/gurultulu derinlik dondurebilir, medyan
    bu tur tekil hatalara karsi dayanikli. Donen: (derinlik_m, gecerli_mi).
    """
    w, h = depth_frame.get_width(), depth_frame.get_height()
    xi, yi = int(round(cx)), int(round(cy))
    degerler = []
    for dy in range(-yarim, yarim + 1):
        for dx in range(-yarim, yarim + 1):
            x, y = xi + dx, yi + dy
            if 0 <= x < w and 0 <= y < h:
                d = depth_frame.get_distance(x, y)
                if d > 0:
                    degerler.append(d)
    if not degerler:
        return 0.0, False
    degerler.sort()
    medyan = degerler[len(degerler) // 2]
    return medyan, (min_m <= medyan <= max_m)


class KameraNode:
    def __init__(self, signaling_url, loop, tespit_aktif=True, ros_aktif=True):
        self.signaling_url = signaling_url
        self.loop = loop
        self.tespit_aktif = tespit_aktif
        # ros_aktif=False iken _NullPublisher doner; publish() no-op olur.
        self.ros = DetectionPublisher(
            enabled=ros_aktif,
            frame_id=ROS_FRAME_ID,
            shooting_zone=ATIS_BOLGESI,
            lock_stable_frames=LOCK_STABLE_FRAMES,
            logger=log,
        )
        self.ws = None
        self.calisiyor = True

        # Yayinci genelde konsoldan once ayaga kalkar; o sirada uretilen offer ve
        # ICE adaylari karsi taraf olmadigi icin duser. Saklanip izleyici
        # baglandiginda tekrar gonderilir.
        self.local_offer_sdp = None
        self.local_ice_candidates = []
        self.webrtc_sink_pad = None
        self._offer_denemesi = 0

        Gst.init(None)
        self._build_pipeline()

    # ---------------- pipeline kurulumu ----------------

    def _build_pipeline(self):
        desc = PIPELINE_DESC.format(
            yw=YAYIN_W, yh=YAYIN_H, fps=YAYIN_FPS,
            tw=TESPIT_W, th=TESPIT_H,
            bitrate=BITRATE_KBPS * 1000,
        )
        log.info("Kaynak pipeline:\n%s", desc)

        self.pipeline = Gst.Pipeline.new("tulpar-kamera")
        src_bin = Gst.parse_bin_from_description(desc, True)
        if src_bin is None:
            raise RuntimeError("Kaynak bin olusturulamadi")

        self.webrtc = Gst.ElementFactory.make("webrtcbin", "webrtcbin")
        if self.webrtc is None:
            raise RuntimeError("webrtcbin olusturulamadi - gstreamer1.0-plugins-bad kurulu mu?")
        self.webrtc.set_property("bundle-policy", GstWebRTC.WebRTCBundlePolicy.MAX_BUNDLE)
        self.webrtc.set_property("stun-server", STUN_SERVER)

        self.pipeline.add(src_bin)
        self.pipeline.add(self.webrtc)

        src_pad = self._bin_src_pad(src_bin)
        sink_pad = self._request_webrtc_sink_pad()
        if sink_pad is None:
            raise RuntimeError("webrtcbin sink_%u request pad alinamadi")

        ret = src_pad.link(sink_pad)
        if ret != Gst.PadLinkReturn.OK:
            raise RuntimeError(f"Kaynak bin -> webrtcbin link basarisiz: {ret.value_nick}")
        self.webrtc_sink_pad = sink_pad
        log.info("Pi HQ (atis yayini) -> webrtcbin baglantisi kuruldu")

        self.webrtc.connect("on-negotiation-needed", self._on_negotiation_needed)
        self.webrtc.connect("on-ice-candidate", self._on_ice_candidate)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_bus_message)

    def _bin_src_pad(self, src_bin):
        """Bin'in disariya acilan (ghost) src pad'ini bulur.

        parse_bin_from_description ghost pad'i genelde 'src' olarak adlandirir
        ama surume gore 'src_0' da olabiliyor - ikisini de karsiliyoruz.
        """
        pad = src_bin.get_static_pad("src")
        if pad is not None:
            return pad
        it = src_bin.iterate_src_pads()
        while True:
            sonuc, pad = it.next()
            if sonuc != Gst.IteratorResult.OK:
                break
            log.info("Ghost src pad bulundu: %s", pad.get_name())
            return pad
        raise RuntimeError("Kaynak bin'in src pad'i bulunamadi")

    def _request_webrtc_sink_pad(self):
        """webrtcbin sink_%u request pad'i. GStreamer/PyGObject surumlerine gore
        API davranisi degistigi icin birkac yontem sirayla denenir.

        NOT: Bu pad'in None donmesinin en sik sebebi eksik libnice paketidir
        (`sudo apt install gstreamer1.0-nice`). Log'da
        "libnice elements are not available" gorursen sebep budur.
        """
        rtp_caps = Gst.Caps.from_string(
            "application/x-rtp,media=video,encoding-name=H264,payload=96,clock-rate=90000"
        )
        templ = self.webrtc.get_pad_template("sink_%u")

        denemeler = []
        if templ is not None:
            denemeler += [
                ("request_pad(templ, None, caps)", lambda: self.webrtc.request_pad(templ, None, rtp_caps)),
                ("request_pad(templ, 'sink_0', caps)", lambda: self.webrtc.request_pad(templ, "sink_0", rtp_caps)),
                ("request_pad(templ, None, None)", lambda: self.webrtc.request_pad(templ, None, None)),
            ]
        if hasattr(self.webrtc, "request_pad_simple"):
            denemeler.append(("request_pad_simple('sink_%u')", lambda: self.webrtc.request_pad_simple("sink_%u")))

        for isim, fn in denemeler:
            try:
                pad = fn()
            except Exception as e:  # noqa: BLE001
                log.warning("Pad denemesi basarisiz (%s): %s", isim, e)
                continue
            if pad is not None:
                log.info("Pad alindi -> %s (%s)", isim, pad.get_name())
                return pad
        return None

    # ---------------- WebRTC / signaling ----------------

    def _on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            log.error("GStreamer HATA: %s (%s)", err, debug)
            if "dmabuf_fd" in str(debug) or "NvBufSurfaceFromFd" in str(debug):
                log.error(
                    "ARGUS BUG: Kamera bu boot'ta zaten bir kez acilmis olabilir. "
                    "Cozum: Jetson'i reboot et ve bu node'u boot sonrasi ILK kamera "
                    "sureci olarak baslat."
                )
        elif t == Gst.MessageType.WARNING:
            warn, debug = message.parse_warning()
            log.warning("GStreamer uyari: %s (%s)", warn, debug)
        elif t == Gst.MessageType.EOS:
            log.warning("GStreamer akisi bitti (EOS)")

    def _on_negotiation_needed(self, webrtc):
        log.info("Negotiation gerekli")
        self._offer_denemesi = 0
        self._offer_dene()

    def _offer_dene(self):
        """create-offer cagrisi. GLib.timeout_add ile tekrar cagrilabilsin diye
        her zaman False doner (tek seferlik timeout).

        NEDEN TEKRAR DENEME VAR: pipeline PLAYING olduktan sonra caps'in
        webrtcbin'in sink pad'ine ulasmasi gecikebiliyor. Caps hazir degilken
        create-offer bos (sdp=NULL) bir cevap donuyor ve "should not be
        reached" CRITICAL'i aliniyor. Bu yuzden once caps bekleniyor, olmazsa
        offer tekrar deneniyor.
        """
        self._offer_denemesi += 1
        if self._offer_denemesi > 20:
            log.error("Offer 20 denemede uretilemedi, pes edildi")
            return False

        caps = self.webrtc_sink_pad.get_current_caps()
        if caps is None:
            log.info("Sink pad caps'i henuz hazir degil (deneme %d), 300ms sonra tekrar",
                     self._offer_denemesi)
            GLib.timeout_add(300, self._offer_dene)
            return False

        log.info("Offer olusturuluyor (caps: %s)", caps.to_string()[:60])
        promise = Gst.Promise.new_with_change_func(self._on_offer_created, self.webrtc, None)
        self.webrtc.emit("create-offer", None, promise)
        return False

    def _on_offer_created(self, promise, webrtc, _):
        promise.wait()
        reply = promise.get_reply()
        offer = reply.get_value("offer") if reply is not None else None

        if offer is None or offer.sdp is None:
            log.warning("create-offer bos dondu (deneme %d), 300ms sonra tekrar denenecek",
                        self._offer_denemesi)
            GLib.timeout_add(300, self._offer_dene)
            return

        webrtc.emit("set-local-description", offer, Gst.Promise.new())
        self.local_offer_sdp = offer.sdp.as_text()
        log.info("Offer olusturuldu, gonderiliyor")
        self._send_signal({"type": "offer", "sdp": self.local_offer_sdp})

    def _on_ice_candidate(self, webrtc, mline_index, candidate):
        payload = {
            "type": "ice-candidate",
            "candidate": {"candidate": candidate, "sdpMLineIndex": mline_index},
        }
        self.local_ice_candidates.append(payload)
        self._send_signal(payload)

    def _replay_local_state(self):
        if self.local_offer_sdp is None:
            log.info("Henuz offer uretilmemis, tekrar gonderilecek bir sey yok")
            return
        log.info("Offer + %d ICE adayi tekrar gonderiliyor", len(self.local_ice_candidates))
        self._send_signal({"type": "offer", "sdp": self.local_offer_sdp})
        for cand in self.local_ice_candidates:
            self._send_signal(cand)

    def _send_signal(self, payload):
        if self.ws is None:
            return
        asyncio.run_coroutine_threadsafe(self.ws.send(json.dumps(payload)), self.loop)

    def handle_signal(self, msg):
        mtype = msg.get("type")

        if mtype == "izleyici-baglandi":
            log.info("Izleyici baglandi bildirimi alindi")
            self._replay_local_state()

        elif mtype == "answer":
            log.info("Answer alindi, remote description ayarlaniyor")
            _, sdpmsg = GstSdp.SDPMessage.new()
            GstSdp.sdp_message_parse_buffer(bytes(msg["sdp"].encode()), sdpmsg)
            answer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg)
            self.webrtc.emit("set-remote-description", answer, Gst.Promise.new())

        elif mtype == "ice-candidate" and msg.get("candidate"):
            cand = msg["candidate"]
            self.webrtc.emit("add-ice-candidate", cand.get("sdpMLineIndex", 0), cand.get("candidate", ""))

    # ---------------- tespit dongusu (RealSense D435if) ----------------

    def tespit_dongusu(self):
        """Ayri thread: RealSense D435if renk+derinlik akisindan YOLO + PID calistirir.

        Argus/GStreamer pipeline'indan tamamen bagimsiz - kendi USB3
        baglantisini kullanir. RealSense donmezse/USB2 kabloya duserse bu
        thread etkilenir, Pi HQ atis yayini calismaya devam eder.
        """
        log.info("Model yukleniyor: %s", MODEL_PATH)
        from ultralytics import YOLO  # agir import - sadece gerekince
        import pyrealsense2 as rs  # agir/donanima bagimli - sadece gerekince

        model = YOLO(MODEL_PATH, task="detect")
        log.info("Model hazir, RealSense pipeline baslatiliyor")

        rs_pipeline = rs.pipeline()
        rs_config = rs.config()
        rs_config.enable_stream(rs.stream.color, TESPIT_W, TESPIT_H, rs.format.bgr8, TESPIT_FPS)
        rs_config.enable_stream(rs.stream.depth, TESPIT_W, TESPIT_H, rs.format.z16, TESPIT_FPS)
        try:
            rs_pipeline.start(rs_config)
        except RuntimeError as e:
            log.error(
                "RealSense pipeline baslatilamadi (%s). USB3 (SuperSpeed) "
                "kabloda mi baglisin? 3 kablodan sadece 1'i USB3 veriyordu, "
                "digerleri USB2 - derinlik/renk akisi acilmayabilir.", e)
            raise
        align = rs.align(rs.stream.color)
        log.info("RealSense pipeline hazir, tespit dongusu basliyor")

        merkez_x, merkez_y = TESPIT_W / 2, TESPIT_H / 2
        # Sinif adlari modelden. class_registry.yaml gelince buradan okunacak.
        sinif_adlari = getattr(model, "names", {}) or {}
        pid_pan = PID(kp=0.05, ki=0.001, kd=0.01)
        pid_tilt = PID(kp=0.05, ki=0.001, kd=0.01)

        onceki = GLib.get_monotonic_time()
        sayac = 0

        try:
            while self.calisiyor:
                try:
                    frames = rs_pipeline.wait_for_frames(timeout_ms=1000)
                except RuntimeError:
                    log.warning("RealSense kare bekleme zaman asimi (USB baglantisi kopmus olabilir)")
                    continue

                frames = align.process(frames)
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
                if not color_frame or not depth_frame:
                    continue

                # capture_time_ns'i inference'tan ONCE aliyoruz ki YOLO'nun
                # harcadigi sure damgaya karismasin (Pi HQ kolundaki 'yas'
                # duzeltmesiyle ayni gerekce).
                capture_time_ns = time.time_ns()
                frame = np.asanyarray(color_frame.get_data())

                simdi = GLib.get_monotonic_time()
                dt = (simdi - onceki) / 1_000_000.0  # mikrosaniye -> saniye
                onceki = simdi

                t_infer = time.perf_counter()
                results = model.predict(source=frame, verbose=False)[0]
                infer_ms = (time.perf_counter() - t_infer) * 1000.0

                # --- ROS2 /detections: TUM tespitler ---
                # PID sadece SHOOTING_TARGET_CLASS_ID ile ilgileniyor, ama
                # Zehra'nin costmap'i ve Talha'nin konsolu her sinifi istiyor.
                dets = []
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].cpu().numpy())
                    cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                    derinlik_m, derinlik_ok = _derinlik_olc(depth_frame, cx, cy)
                    dets.append(
                        Det(
                            class_id=cls_id,
                            class_name=str(sinif_adlari.get(cls_id, cls_id)),
                            confidence=float(box.conf[0]),
                            x1=x1, y1=y1, x2=x2, y2=y2,
                            depth_m=derinlik_m,
                            depth_valid=derinlik_ok,
                        )
                    )
                # Donen 'birincil' merkeze en yakin tespit -- PID'in istedigi
                # bu DEGIL (PID sinif 13'e kilitli), o yuzden kullanmiyoruz.
                self.ros.publish(
                    detections=dets,
                    image_size=(TESPIT_W, TESPIT_H),
                    capture_time_ns=capture_time_ns,
                    inference_ms=infer_ms,
                )

                hedef = find_shooting_target(results)

                if hedef is not None:
                    x_c, y_c, conf = hedef
                    hata_x = x_c - merkez_x
                    hata_y = y_c - merkez_y
                    pan = pid_pan.update(hata_x, dt)
                    tilt = pid_tilt.update(hata_y, dt)
                    buyukluk = (hata_x ** 2 + hata_y ** 2) ** 0.5
                    durum = "LOCKED" if buyukluk < LOCK_THRESHOLD_PX else "TRACKING"

                    # /detections ve /tulpar_kamera/atis_event yukarida yayinlandi.
                    # Konsol nisan artisini kendi ciziyor, o yuzden videoya overlay
                    # basmiyoruz - sadece koordinat/durum verisi yayiliyor.
                    if sayac % 15 == 0:
                        log.info(
                            "[%s] hata=(%+.0f,%+.0f)px pan=%+.2f tilt=%+.2f conf=%.2f",
                            durum, hata_x, hata_y, pan, tilt, conf,
                        )
                else:
                    pid_pan.reset()
                    pid_tilt.reset()
                    if sayac % 30 == 0:
                        log.info("[NO TARGET] shooting_target tespit edilmedi")

                sayac += 1
        finally:
            rs_pipeline.stop()
            log.info("RealSense pipeline durduruldu")

    # ---------------- yasam dongusu ----------------

    def start(self):
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Pipeline PLAYING durumuna gecirilemedi")
        log.info("Pipeline PLAYING - Argus oturumu acildi (gorev boyunca acik kalacak)")

        if self.tespit_aktif:
            threading.Thread(target=self.tespit_dongusu, daemon=True).start()
        else:
            log.info("Tespit devre disi (--tespit-yok), sadece video yayini var")

    def stop(self):
        self.calisiyor = False
        self.pipeline.set_state(Gst.State.NULL)
        self.ros.shutdown()
        log.info("Pipeline durduruldu")


async def signaling_loop(node, signaling_url):
    while True:
        try:
            log.info("Signaling sunucusuna baglaniliyor: %s", signaling_url)
            async with websockets.connect(signaling_url) as ws:
                node.ws = ws
                await ws.send(json.dumps({"type": "yayinci-merhaba"}))
                log.info("Signaling baglantisi kuruldu")
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    node.handle_signal(msg)
        except (websockets.exceptions.ConnectionClosed, OSError) as e:
            log.warning("Signaling koptu/kurulamadi (%s), 3sn sonra tekrar", e)
            node.ws = None
            await asyncio.sleep(3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--signaling", required=True, help="ws://<ip>:8080/yer-istasyonu-video")
    parser.add_argument("--tespit-yok", action="store_true", help="YOLO/PID'i calistirma, sadece video yayinla")
    parser.add_argument("--ros-yok", action="store_true",
                        help="ROS2 yayinini kapat (rclpy hic import edilmez)")
    args = parser.parse_args()

    glib_loop = GLib.MainLoop()
    threading.Thread(target=glib_loop.run, daemon=True).start()

    asyncio_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio_loop)

    node = KameraNode(args.signaling, asyncio_loop,
                      tespit_aktif=not args.tespit_yok,
                      ros_aktif=not args.ros_yok)
    node.start()

    try:
        asyncio_loop.run_until_complete(signaling_loop(node, args.signaling))
    except KeyboardInterrupt:
        log.info("Durduruluyor...")
    finally:
        node.stop()
        glib_loop.quit()


if __name__ == "__main__":
    main()
