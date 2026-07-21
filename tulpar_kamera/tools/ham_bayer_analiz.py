#!/usr/bin/env python3
"""
Tulpar IKA - Ham bayer kare analizi (magenta renk sorunu teshisi).

AMAC: Goruntudeki magenta kaymasinin kaynagini ayirt etmek.
Magenta = yesil kanal eksikligi. Iki ihtimal var:

  A) ISP / tuning sorunu  -> HAM veride yesil saglikli, ISP ciktisinda bozuk
  B) Optik / fiziksel     -> HAM veride de yesil dusuk (IR-cut filtresi yok,
                             lens, aydinlatma vb.)

Bu script Argus'u HIC kullanmaz - dogrudan v4l2'nin verdigi ham bayer kareyi
okur. Yani calistirmak icin reboot gerekmez ve Argus oturumu harcamaz.

HAM KARE NASIL ALINIR (Jetson'da):
    v4l2-ctl -d /dev/video0 --set-fmt-video=width=1920,height=1080,pixelformat=RG10 \\
      --stream-mmap --stream-count=1 --stream-to=/home/tulpar/ham_kare.raw

KULLANIM:
    python3 ham_bayer_analiz.py /home/tulpar/ham_kare.raw

BAYER DESENI (RG10 = RGGB):
    satir 0:  R  G  R  G ...
    satir 1:  G  B  G  B ...
Yani 2x2 blokta: sol-ust=R, sag-ust=Gr, sol-alt=Gb, sag-alt=B
"""
import sys

import numpy as np

VARSAYILAN_W = 1920
VARSAYILAN_H = 1080


def oku(yol, w=VARSAYILAN_W, h=VARSAYILAN_H):
    ham = np.fromfile(yol, dtype=np.uint16)
    beklenen = w * h
    print(f"Dosya: {yol}")
    print(f"Okunan 16-bit deger sayisi: {len(ham)}  (beklenen {beklenen})")

    # Bos/eksik dosyada sessizce devam etmek yaniltici teshise yol acar -
    # burada acikca durduruyoruz.
    if len(ham) == 0:
        raise SystemExit(
            "\nHATA: Dosya BOS. Ham kare alinamamis.\n"
            "Jetson'da dogrudan v4l2 yakalamasi icin ISP bypass kapatilmali:\n"
            "  v4l2-ctl -d /dev/video0 --set-ctrl bypass_mode=0 \\\n"
            "    --set-fmt-video=width=1920,height=1080,pixelformat=RG10 \\\n"
            "    --stream-mmap --stream-count=1 --stream-to=/home/tulpar/ham_kare.raw\n"
            "Ayrica desteklenen formati kontrol et:\n"
            "  v4l2-ctl -d /dev/video0 --list-formats-ext"
        )

    if len(ham) < beklenen // 2:
        raise SystemExit(
            f"\nHATA: Dosya beklenenden cok kucuk ({len(ham)} deger). "
            f"Yakalama yarida kesilmis olabilir."
        )

    # Cok kareli dosya (--stream-count>1): SON kareyi al. Ilk kareler sensor/
    # pozlama oturmadan geldigi icin guvenilmez.
    if len(ham) > beklenen and len(ham) % beklenen == 0:
        kare_sayisi = len(ham) // beklenen
        print(f"Dosyada {kare_sayisi} kare var - sonuncusu analiz ediliyor.")
        return ham[-beklenen:].reshape(h, w)

    if len(ham) == beklenen:
        return ham.reshape(h, w)

    # Satir sonu dolgusu (stride padding) olabilir - satir basina deger sayisini
    # dosya boyutundan geri hesapla.
    if len(ham) % h == 0:
        stride = len(ham) // h
        print(f"Stride dolgusu tespit edildi: satir basina {stride} deger "
              f"({stride - w} dolgu). Dolgu kirpiliyor.")
        return ham.reshape(h, stride)[:, :w]

    raise SystemExit(
        f"HATA: Dosya boyutu beklenen sekle uymuyor. "
        f"Cozunurlugu --w/--h ile duzeltmen gerekebilir."
    )


def analiz(bayer):
    # RGGB deseni: 2x2 blok koseleri
    R = bayer[0::2, 0::2].astype(np.float64)
    Gr = bayer[0::2, 1::2].astype(np.float64)
    Gb = bayer[1::2, 0::2].astype(np.float64)
    B = bayer[1::2, 1::2].astype(np.float64)

    G = (Gr.mean() + Gb.mean()) / 2
    r, b = R.mean(), B.mean()
    ort = (r + G + b) / 3

    # Bit derinligini veriden cikar - RG10 "10-bit" dese de veri sola kaydirilmis
    # olabiliyor. Sabit 0-1023 varsaymak yaniltici sonuc veriyor.
    tepe = int(bayer.max())
    for bit in (8, 10, 12, 14, 16):
        if tepe <= (1 << bit) - 1:
            tahmini_bit = bit
            break
    else:
        tahmini_bit = 16
    tavan = (1 << tahmini_bit) - 1

    print("\n=== VERI ARALIGI ===")
    print(f"  min={int(bayer.min())}  max={tepe}  ortalama={bayer.mean():.1f}")
    print(f"  medyan={np.median(bayer):.0f}  %1={np.percentile(bayer,1):.0f}  "
          f"%99={np.percentile(bayer,99):.0f}")
    print(f"  Tahmini bit derinligi: {tahmini_bit}-bit (tavan {tavan})")

    print("\n=== HAM KANAL ORTALAMALARI (pedestal DAHIL - yaniltici) ===")
    print(f"  R={r:.0f}  Gr={Gr.mean():.0f}  Gb={Gb.mean():.0f}  G={G:.0f}  B={b:.0f}")

    # SIYAH SEVIYESI (PEDESTAL) DUZELTMESI - KRITIK
    # Sensor cikisinda sifir isik bile ~pedestal degerini verir (IMX477'de bu
    # deger olcumlerimizde ~4035 cikti). Pedestal cikarilmadan hesaplanan
    # oranlar tamamen yaniltici olur: 4331 vs 4716 sadece %8 fark gibi gorunur
    # ama pedestal cikinca 296 vs 681, yani 2.3 KAT fark oldugu ortaya cikar.
    pedestal = float(bayer.min())
    rc, Gc, bc = r - pedestal, G - pedestal, b - pedestal
    ortc = (rc + Gc + bc) / 3

    print(f"\n=== PEDESTAL DUZELTILMIS (pedestal={pedestal:.0f} olarak alindi) ===")
    print(f"  R  = {rc:8.1f}")
    print(f"  G  = {Gc:8.1f}")
    print(f"  B  = {bc:8.1f}")
    if Gc > 0:
        print(f"\n  R/G = {rc / Gc:.3f}   B/G = {bc / Gc:.3f}   G/ortalama = {Gc / ortc:.3f}")

    r, G, b, ort = rc, Gc, bc, ortc

    # Once pozlama gecerli mi diye bak - gecersizse renk yorumu anlamsiz.
    doygun_oran = (bayer >= tavan * 0.98).mean() * 100
    karanlik_oran = (bayer <= tavan * 0.02).mean() * 100

    # Kontrast kontrolu: sahne detayi yoksa renk oranlari anlamsizdir.
    # Mutlak esik yerine ORANSAL kontrast kullaniyoruz - siyah seviyesi (pedestal)
    # kaymasi yuzunden mutlak esik yaniltiyordu (21 Tem: min=4035 max=4356 olan
    # tamamen siyah bir kare "makul" diye gecmisti).
    p1, p99 = np.percentile(bayer, 1), np.percentile(bayer, 99)
    oransal_kontrast = (p99 - p1) / max(bayer.mean(), 1)
    if oransal_kontrast < 0.10:
        print(f"\n[GECERSIZ] Karede sahne detayi yok "
              f"(oransal kontrast %{oransal_kontrast*100:.1f}, %10'un altinda).")
        print(f"Tum degerler {int(p1)}-{int(p99)} arasinda sikismis - bu genelde")
        print("siyah seviyesi (pedestal) civarinda takili, yani pozlanmamis bir kare.")
        print("\nDogrudan v4l2 yakalamasinda otomatik pozlama YOK, elle ayarlanmali:")
        print("  v4l2-ctl -d /dev/video0 --set-ctrl gain=150 --set-ctrl exposure=300000 \\")
        print("    --set-fmt-video=width=1920,height=1080,pixelformat=RG10 \\")
        print("    --stream-mmap --stream-count=10 --stream-to=/home/tulpar/ham_kare.raw")
        print("\nKare hala karanliksa gain/exposure degerlerini kademeli artir")
        print("(gain max=357, exposure max=683710). Renk yorumu bu kareyle YAPILAMAZ.")
        return
    if doygun_oran > 20:
        print(f"\n[GECERSIZ] Piksellerin %{doygun_oran:.0f}'i doygun - kare yanmis.")
        print("Dogrudan v4l2 yakalamasinda otomatik pozlama YOK; pozlama/kazanc")
        print("elle ayarlanmali:")
        print("  v4l2-ctl -d /dev/video0 --list-ctrls   # once kontrolleri gor")
        print("  v4l2-ctl -d /dev/video0 --set-ctrl exposure=<dusuk deger>")
        print("  v4l2-ctl -d /dev/video0 --set-ctrl gain=<dusuk deger>")
        print("Renk yorumu bu kareyle YAPILAMAZ - dogru pozlanmis kare gerekli.")
        return
    if karanlik_oran > 80:
        print(f"\n[GECERSIZ] Piksellerin %{karanlik_oran:.0f}'i neredeyse siyah - "
              "kare cok karanlik.")
        print("Pozlama/kazanci artir veya sahneyi aydinlat. Renk yorumu yapilamaz.")
        return

    print("\n=== YORUM ===")
    # ONEMLI: Bu HAM veri - beyaz dengesi UYGULANMAMIS durumda. Ham bayer'de
    # yesilin baskin olmasi NORMALDIR (tipik R/G ~0.4-0.7, B/G ~0.4-0.8).
    # "Dengeli" beklemek yanlis olur; asil aranan sey yesilin DUSUK olmasi.
    rg = r / G if G > 0 else 0
    bg = b / G if G > 0 else 0

    if G / ort < 0.9:
        print("HAM veride yesil kanal DUSUK (beklenenin aksine).")
        print("-> Sorun ISP'den ONCE, optik/fiziksel katmanda:")
        print("   * IR-cut filtresi takili mi? (yoksa tipik pembe/magenta kayma olur)")
        print("   * Lens dogru oturmus mu, arada filtre kaymis olabilir mi?")
        print("   * Aydinlatma asiri kizil/IR agirlikli mi?")
        print("   ISP ayariyla ugrasmak bu durumda sonucu duzeltmez.")
    elif rg > 1.1 or bg > 1.1:
        print("HAM veride kirmizi veya mavi, yesilden yuksek - alisilmadik.")
        print("-> Bayer deseni yanlis yorumlanmis olabilir (RGGB disinda bir desen)")
        print("   ya da aydinlatma cok renkli. pixelformat'i kontrol et.")
    else:
        print("HAM veri SAGLIKLI: yesil baskin, kirmizi/mavi ondan dusuk -")
        print("beyaz dengesi uygulanmamis ham bayer icin beklenen tablo bu.")
        print("\n-> Sensor ve optik SORUNSUZ. Yani goruntudeki magenta kaymasi")
        print("   ISP (Argus) katmaninda ekleniyor: beyaz dengesi veya renk")
        print("   matrisi yanlis uygulaniyor.")
        print("   Sonraki adim: renk_testi.py ile farkli wbmode degerlerini dene,")
        print("   duzelmezse imx477.nito tuning dosyasinin modulunle uyumunu sorgula.")

    if doygun_oran > 2:
        print(f"\n[UYARI] Piksellerin %{doygun_oran:.1f}'i doygun. Parlak bolgeler")
        print("        renk oranlarini bir miktar bozabilir.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit("Kullanim: python3 ham_bayer_analiz.py <ham_kare.raw> [genislik] [yukseklik]")

    yol = sys.argv[1]
    w = int(sys.argv[2]) if len(sys.argv) > 2 else VARSAYILAN_W
    h = int(sys.argv[3]) if len(sys.argv) > 3 else VARSAYILAN_H

    bayer = oku(yol, w, h)
    analiz(bayer)


if __name__ == "__main__":
    main()
