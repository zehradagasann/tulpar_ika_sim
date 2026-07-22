#!/usr/bin/env python3
"""
Tulpar IKA - Arka kamera (Sjcam SJ4000) WebRTC yayin node'u.

Sjcam'in HDMI cikisi bir USB capture card (MacroSilicon 534d:2109, UVC
MJPEG, /dev/video0) uzerinden Jetson'a bagli. Bu node SADECE video
yayinlar - YOLO/PID/ROS yok; yol haritasinda arka kamera sadece
operatorun geri gorus alani icin (KTR 3.3.1), tespit gerekmiyor.

Pi HQ (kamera_node.py) ve RealSense pipeline'larindan tamamen bagimsiz:
ayri process, ayri GStreamer pipeline, ayri sinyalleme kanali
(/yer-istasyonu-arka-kamera - bkz. signaling_server.py'nin path-bazli
coklu kanal destegi). Capture card USB2 hub'da, D435 ayri USB3 hub'da -
bant genisligi cakismasi yok (lsusb ile dogrulandi).

DONANIM TESTI (22 Tem): Pi HQ'nun kendi NVENC oturumu acikken ikinci bir
nvv4l2h264enc oturumu hatasiz acildi; ~65sn yuk testinde sicaklik
platoya oturdu (tj 61.9C -> 62.2C), termal risk gorulmedi. RAM/CPU/GPU
yukunde de belirgin bir sikinti yok (bkz. proje notlari).

BANT GENISLIGI: KTR/Gun4 toplam 7.5 Mbps siniri Pi HQ (6 Mbps, atis
kamerasi, oncelikli) ile paylasiliyor. Bu yuzden dusuk cozunurluk/bitrate
secildi: 640x480 @ 1.2 Mbps -> toplam 7.2 Mbps, sinirin altinda. Ihtiyaca
gore REAR_BITRATE_KBPS ayarlanabilir ama toplamin (Pi HQ + bu) 7.5 Mbps'i
asmamasina dikkat edilmeli.

KULLANIM:
    python3 arka_kamera_node.py --signaling ws://127.0.0.1:8080/yer-istasyonu-arka-kamera
"""
import argparse
import asyncio
import json
import logging
import threading

import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstWebRTC", "1.0")
gi.require_version("GstSdp", "1.0")
from gi.repository import GLib, Gst, GstSdp, GstWebRTC  # noqa: E402,F401

import websockets  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [arka-kamera] %(message)s")
log = logging.getLogger("arka-kamera")

# ---------------- AYARLAR ----------------
CAPTURE_DEVICE = "/dev/video0"
REAR_W, REAR_H, REAR_FPS = 640, 480, 30
REAR_BITRATE_KBPS = 1200
STUN_SERVER = "stun://stun.l.google.com:19302"

PIPELINE_DESC = (
    "v4l2src device={device} ! "
    "image/jpeg,width={w},height={h},framerate={fps}/1 ! "
    "jpegdec ! videoconvert ! nvvidconv ! "
    "video/x-raw(memory:NVMM),format=NV12 ! "
    "nvv4l2h264enc bitrate={bitrate} insert-sps-pps=true idrinterval=30 maxperf-enable=true ! "
    "h264parse config-interval=-1 ! "
    "rtph264pay config-interval=1 pt=96 ! "
    "queue leaky=downstream max-size-buffers=60 ! "
    'capsfilter caps="application/x-rtp,media=video,encoding-name=H264,payload=96"'
)


class ArkaKameraNode:
    def __init__(self, signaling_url, loop):
        self.signaling_url = signaling_url
        self.loop = loop
        self.ws = None

        # Yayinci genelde konsoldan once ayaga kalkar; bkz. kamera_node.py'deki
        # ayni gerekce - offer/ICE'lar izleyici baglandiginda tekrar gonderilir.
        self.local_offer_sdp = None
        self.local_ice_candidates = []
        self.webrtc_sink_pad = None
        self._offer_denemesi = 0

        Gst.init(None)
        self._build_pipeline()

    # ---------------- pipeline kurulumu ----------------

    def _build_pipeline(self):
        desc = PIPELINE_DESC.format(
            device=CAPTURE_DEVICE, w=REAR_W, h=REAR_H, fps=REAR_FPS,
            bitrate=REAR_BITRATE_KBPS * 1000,
        )
        log.info("Kaynak pipeline:\n%s", desc)

        self.pipeline = Gst.Pipeline.new("tulpar-arka-kamera")
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
        log.info("Arka kamera -> webrtcbin baglantisi kuruldu")

        self.webrtc.connect("on-negotiation-needed", self._on_negotiation_needed)
        self.webrtc.connect("on-ice-candidate", self._on_ice_candidate)

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_bus_message)

    def _bin_src_pad(self, src_bin):
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

    # ---------------- yasam dongusu ----------------

    def start(self):
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Pipeline PLAYING durumuna gecirilemedi")
        log.info("Pipeline PLAYING - arka kamera yayini basladi")

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)
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
    parser.add_argument("--signaling", required=True, help="ws://<ip>:8080/yer-istasyonu-arka-kamera")
    args = parser.parse_args()

    glib_loop = GLib.MainLoop()
    threading.Thread(target=glib_loop.run, daemon=True).start()

    asyncio_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(asyncio_loop)

    node = ArkaKameraNode(args.signaling, asyncio_loop)
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
