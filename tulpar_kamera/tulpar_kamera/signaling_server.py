#!/usr/bin/env python3
"""
Tulpar IKA - Yer istasyonu WebRTC signaling sunucusu.

Talha'nin yer_istasyonu/src/renderer/src/components/VideoAlici.jsx dosyasindaki
protokolle bire bir uyumludur:

    konsol (izleyici) baglanir -> {"type": "izleyici-merhaba"}
    sunucu, yayinciya (Jetson) bildirir -> {"type": "izleyici-baglandi"}
    yayinci offer olusturur ve gonderir -> {"type": "offer", "sdp": ...}
    sunucu offer'i izleyiciye iletir (oldugu gibi)
    izleyici cevap gonderir -> {"type": "answer", "sdp": ...}
    sunucu answer'i yayinciya iletir
    iki taraf da ICE adaylarini gonderir -> {"type": "ice-candidate", "candidate": {...}}
    sunucu bu mesajlari karsi tarafa oldugu gibi iletir (relay)

COKLU KANAL (22 Tem itibariyle): Her WebSocket baglanti yolu (path) kendi
bagimsiz yayinci/izleyici cifti olan ayri bir "kanal". Ayni process/port
uzerinden birden fazla kamera akisi (orn. /yer-istasyonu-video = Pi HQ atis,
/yer-istasyonu-arka-kamera = Sjcam arka) es zamanli calisabilir; bir
kanaldaki yayinci/izleyici digerini gormez. Yeni bir kamera eklerken bu
dosyaya dokunmaya gerek yok - sadece yayinci ve konsol tarafi ayni yeni path
uzerinde anlassin yeter.

Calistirma:
    pip3 install websockets
    python3 signaling_server.py [--host 0.0.0.0] [--port 8080]

Jetson'da video gonderici (jetson_webrtc_sender.py) ile ayni makinede
calistirilmasi onerilir (bkz. sohbet notlari - Jetson sabit IP: 192.168.100.10).
Konsol tarafinda .env dosyasina eklenmesi gereken satir:

    VITE_SIGNALING_URL=ws://192.168.100.10:8080/yer-istasyonu-video
"""
import argparse
import asyncio
import json
import logging

import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s [signaling] %(message)s")
log = logging.getLogger("signaling")

VARSAYILAN_YOL = "/yer-istasyonu-video"


class KanalDurumu:
    def __init__(self):
        self.broadcaster = None  # Jetson gonderici baglantisi
        self.viewer = None       # Konsol (Electron) baglantisi


kanallar: dict[str, KanalDurumu] = {}


def kanal_al(path: str) -> KanalDurumu:
    """Path basina bir KanalDurumu - yoksa olusturur. Boylece her kamera
    kendi yayinci/izleyici ciftine sahip olur, birbirine karismaz."""
    if path not in kanallar:
        kanallar[path] = KanalDurumu()
    return kanallar[path]


async def safe_send(ws, payload: dict):
    if ws is None:
        return
    try:
        await ws.send(json.dumps(payload))
    except websockets.exceptions.ConnectionClosed:
        pass


async def handler(websocket):
    path = websocket.request.path if websocket.request is not None else VARSAYILAN_YOL
    state = kanal_al(path)
    role = None
    peer = getattr(websocket, "remote_address", "?")
    log.info("Yeni baglanti: %s (kanal=%s)", peer, path)

    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                log.warning("JSON parse edilemedi, mesaj atlandi: %r", raw[:200])
                continue

            mtype = msg.get("type")

            if mtype == "yayinci-merhaba":
                role = "broadcaster"
                state.broadcaster = websocket
                log.info("Yayinci (Jetson) baglandi (kanal=%s): %s", path, peer)
                if state.viewer is not None:
                    await safe_send(state.broadcaster, {"type": "izleyici-baglandi"})
                continue

            if mtype == "izleyici-merhaba":
                role = "viewer"
                state.viewer = websocket
                log.info("Izleyici (konsol) baglandi (kanal=%s): %s", path, peer)
                if state.broadcaster is not None:
                    await safe_send(state.broadcaster, {"type": "izleyici-baglandi"})
                continue

            # offer / answer / ice-candidate - oldugu gibi karsi tarafa ilet
            if role == "broadcaster":
                if state.viewer is not None:
                    await safe_send(state.viewer, msg)
                else:
                    log.warning("Izleyici henuz bagli degil (kanal=%s), '%s' mesaji dusuruldu", path, mtype)
            elif role == "viewer":
                if state.broadcaster is not None:
                    await safe_send(state.broadcaster, msg)
                else:
                    log.warning("Yayinci henuz bagli degil (kanal=%s), '%s' mesaji dusuruldu", path, mtype)
            else:
                log.warning("Kimligini bildirmemis baglantidan mesaj geldi (kanal=%s, %s), yok sayildi", path, mtype)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if role == "broadcaster" and state.broadcaster is websocket:
            state.broadcaster = None
            log.info("Yayinci baglantisi kapandi (kanal=%s): %s", path, peer)
        elif role == "viewer" and state.viewer is websocket:
            state.viewer = None
            log.info("Izleyici baglantisi kapandi (kanal=%s): %s", path, peer)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    log.info("Signaling sunucusu baslatiliyor: ws://%s:%d (yol bazli coklu kanal)", args.host, args.port)
    async with websockets.serve(handler, args.host, args.port):
        await asyncio.Future()  # sonsuza kadar calis


def cli():
    """Senkron giris noktasi.

    `main` bir coroutine oldugu icin setup.py'deki console_scripts girdisi
    dogrudan onu cagiramaz (coroutine dondurur, calistirmaz). ros2 run bu
    sarmalayiciyi cagirir.
    """
    asyncio.run(main())


if __name__ == "__main__":
    cli()
