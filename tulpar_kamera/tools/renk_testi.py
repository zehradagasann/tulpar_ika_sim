#!/usr/bin/env python3
"""
Tulpar IKA - Kamera renk (beyaz dengesi) teshis scripti.

SORUN: Pi HQ IMX477 goruntusunde belirgin magenta/pembe renk kaymasi var.
Magenta = yesil kanal eksikligi. Iki ana suphe:
  1) Bayer sirasi uyusmazligi (device tree overlay) -> ISP renkleri yanlis cozuyor
  2) Beyaz dengesi (AWB) ayari

Bu script (2)'yi test eder: TEK Argus oturumu icinde wbmode degerlerini
0'dan 9'a kadar dolasir ve her biri icin bir JPEG kaydeder.

NEDEN TEK OTURUM: JetPack 7.2'de Argus, boot sonrasi ikinci kamera oturumunu
acamiyor. Her wbmode icin ayri gst-launch calistirmak 10 reboot demek olurdu.
Bunun yerine kamera bir kez acilir, wbmode calisma aninda degistirilir.

KULLANIM (boot sonrasi ILK kamera sureci olarak calistir):
    python3 renk_testi.py
    # sonuclar: /home/tulpar/renk_testi/wb_<n>_<isim>.jpg

Sonra JPEG'leri incelemek icin laptop'a kopyala:
    scp tulpar@192.168.55.1:~/renk_testi/*.jpg C:\\Users\\emink\\OneDrive\\Desktop\\renk_testi\\

IPUCU: Test sirasinda kameranin onune beyaz bir kagit veya bilinen renkte bir
nesne koy - hangi ayarin dogru oldugunu anlamak cok daha kolay olur.
"""
import os
import time

import cv2
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

# nvarguscamerasrc wbmode degerleri (gst-inspect-1.0 nvarguscamerasrc ciktisindan)
WB_MODLARI = {
    0: "off",
    1: "auto",
    2: "incandescent",
    3: "fluorescent",
    4: "warm-fluorescent",
    5: "daylight",
    6: "cloudy-daylight",
    7: "twilight",
    8: "shade",
    9: "manual",
}

CIKTI_DIZINI = "/home/tulpar/renk_testi"
BEKLEME_SN = 2.0   # AWB'nin yeni moda oturmasi icin beklenen sure

PIPELINE = (
    "nvarguscamerasrc name=cam sensor-id=0 ! "
    "video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1 ! "
    "nvvidconv ! video/x-raw,format=BGRx ! "
    "videoconvert ! video/x-raw,format=BGR ! "
    "appsink name=sink drop=true max-buffers=2 sync=false"
)


def sample_to_frame(sample):
    import numpy as np

    buf = sample.get_buffer()
    yapi = sample.get_caps().get_structure(0)
    w, h = yapi.get_value("width"), yapi.get_value("height")
    ok, harita = buf.map(Gst.MapFlags.READ)
    if not ok:
        return None
    try:
        return np.ndarray((h, w, 3), buffer=harita.data, dtype=np.uint8).copy()
    finally:
        buf.unmap(harita)


def kanal_ortalamalari(frame):
    """BGR kanal ortalamalari - magenta kaymasi varsa yesil (G) belirgin dusuk cikar."""
    b, g, r = frame[:, :, 0].mean(), frame[:, :, 1].mean(), frame[:, :, 2].mean()
    return b, g, r


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--wbmode", type=int, default=1, choices=list(WB_MODLARI),
                        help="Beyaz dengesi modu (varsayilan 1=auto)")
    args = parser.parse_args()
    isim = WB_MODLARI[args.wbmode]

    os.makedirs(CIKTI_DIZINI, exist_ok=True)
    Gst.init(None)

    # ONEMLI: wbmode PLAYING'e gecmeden ONCE verilmeli. Calisma aninda
    # set_property ile degistirmek Argus'u dusuruyor (21 Tem'de dogrulandi:
    # "wbmode=0 ayarlandi" satirinin hemen ardindan dmabuf_fd -1 hatasi geldi
    # ve daemon coktu). Bu yuzden her calistirmada tek bir mod test edilir.
    pipeline_desc = PIPELINE.replace("nvarguscamerasrc name=cam",
                                     f"nvarguscamerasrc name=cam wbmode={args.wbmode}")
    print(f"[BILGI] wbmode={args.wbmode} ({isim}) ile pipeline aciliyor")
    pipeline = Gst.parse_launch(pipeline_desc)
    sink = pipeline.get_by_name("sink")

    pipeline.set_state(Gst.State.PLAYING)
    print("[BILGI] Kamera acildi, AWB'nin oturmasi bekleniyor...")
    time.sleep(4)

    try:
        sample = None
        for _ in range(5):  # taze kare al
            sample = sink.emit("pull-sample")
        if sample is None:
            print("[HATA] Kare alinamadi - Argus bu boot'ta zaten kullanilmis olabilir.")
            return

        frame = sample_to_frame(sample)
        if frame is None:
            print("[HATA] Kare cozulemedi")
            return

        yol = f"{CIKTI_DIZINI}/wb_{args.wbmode}_{isim}.jpg"
        cv2.imwrite(yol, frame)
        b, g, r = kanal_ortalamalari(frame)
        ort = (b + g + r) / 3
        oran = g / ort if ort > 0 else 0

        print(f"\n=== SONUC: wbmode={args.wbmode} ({isim}) ===")
        print(f"Kaydedildi: {yol}")
        print(f"Kanal ortalamalari:  B={b:.0f}  G={g:.0f}  R={r:.0f}")
        print(f"G/ortalama orani: {oran:.2f}")
        if oran < 0.8:
            print("\n-> Yesil kanal belirgin dusuk. Sorun beyaz dengesi DEGIL;")
            print("   bayer sirasi (device tree overlay) veya ISP tuning kaynakli.")
        else:
            print("\n-> Kanal dengesi makul gorunuyor.")

    finally:
        pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    main()
