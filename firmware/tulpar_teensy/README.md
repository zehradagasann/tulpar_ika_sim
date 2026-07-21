# tulpar_teensy — Gaz Kartı Firmware

Kaynak: **"TULPAR Gaz Kartı — Donanım → Yazılım Handoff (v1)"** (19 Temmuz 2026,
donanım/elektronik ekibi) — tüm pin/adres/sıralama değerleri bu dokümana göre
ayarlandı. Roadmap dokümanındaki eski VESC/CAN mimarisiyle bir ilgisi yok.

## Donanım build (Teensy 4.1)

1. Arduino IDE + Teensyduino kurulu olmalı.
2. Kütüphane: **"Watchdog_t4"** (tonton81) — Library Manager'dan kur.
3. Board: **Teensy 4.1**.
4. `tulpar_teensy.ino`'yu aç, upload et.

`src/` altındaki dosyalar Arduino IDE tarafından otomatik derlenir (alt
klasördeki `.cpp`/`.h` dosyaları desteklenir). Derleme sorunu çıkarsa
dosyaları sketch köküne düzleştirmek bir fallback.

## PC'de donanımsız mantık testi

`SurucuKatmani`, gerçek `Wire` yerine bir `I2CBus` arayüzü kullanıyor
(`WireI2CBus` = gerçek donanım, `MockI2CBus` = test) — böylece mux
seçim/DAC yazım sırası donanım gelmeden doğrulanabilir:

```bash
cd firmware/tulpar_teensy
g++ -std=c++17 -I. test/test_surucu_katmani.cpp src/SurucuKatmani.cpp -o /tmp/test_surucu
/tmp/test_surucu
```

**Bu testler ne doğrular, ne doğrulamaz**: I2C mesajlarının doğru
adrese/sırayla/byte'la gittiğini doğrular. Gerçek voltaj çıktısını,
TCA9548A/PCF8591'in fiziksel yanıtını **doğrulamaz** — bunlar için handoff
dokümanının B6 bölümündeki multimetre bring-up adımları gerekli (donanım
masaya gelince).

## Fren / Taret / Lazer / ELRS (21 Temmuz 2026, elektronik ekibin pin listesine göre)

Aynı "gerçek/mock donanım arayüzü" deseniyle donanımsız test edilebilir
şekilde yazıldı — `PwmCikis`/`AdimSurucuCikis`/`DijitalCikis` arayüzleri
`SurucuKatmani`'nin `I2CBus`'ıyla aynı mantık. `Serial` komutları:

- `F<kanal 0-3> <oran 0.0-1.0>` — fren servosu (örn. `F0 0.5`)
- `TP <derece>` / `TT <derece>` — taret pan/tilt (örn. `TP 30`), **±90° yazılımsal
  sınır otomatik kırpılır** (KTR 5.2) — sınıra çarpınca "LIMITE KIRPILDI" basar
- `L1` / `L0` — lazer röle aç/kapat

**Gerçek Teensy 4.1 hedefi için derleme doğrulandı** (`arduino-cli compile
--fqbn teensy:avr:teensy41 .`, sadece kütüphane uyarıları, hata yok).

**Onay bekleyen değerler** (bkz. `src/TaretEksenKatmani.h` dokstring'i):
- Taret `derece_basina_adim` (motor step açısı + TB6600 mikroadım DIP anahtarı
  + varsa dişli oranı) — şu an placeholder `1.8°/adım` (mikroadımsız 200
  adım/tur varsayımı), elektronik ekipten gerçek değer gerekiyor.
- Taret `limit_derece=90.0` — roadmap'in KTR 5.2 metninden varsayımı, Emin'den
  (taret sahibi) kesin teyit gelmedi.
- Taret sıfır/home konumu — gerçek bir limit switch/endstop olmadan "açılışta
  0°" varsayılıyor, homing prosedürü elektronik ekiple netleşmeli.
- Fren servo oranı→gerçek fren kuvveti eğrisi doğrusal varsayıldı, saha
  kalibrasyonu (Gün 11, m/s↔DAC kalibrasyonuna benzer) gerekebilir.

**ELRS/CRSF**: `CrsfParser` (Serial1, pin 0/1, 420000 baud) `loop()`'ta sürekli
okunuyor, `RC_CHANNELS_PACKED` (tip 0x16) çerçevelerini CRC doğrulayarak
çözüyor — 16 kanal + `crsfToMicroseconds()` yardımcı fonksiyonu hazır. Şu an
sadece parse ediliyor, **manuel/otonom devralma mantığı (PIN_ELRS_ROLE ile)
donanım gelmeden yazılmadı** — gerçek alıcıyla test edilmesi gerekiyor.

**ELRS failsafe (400ms)**: `ElrsFailsafeKatmani` roadmap'in "400ms paket
gelmezse DAC=0+kilit LOW" kuralını uyguluyor, test edildi — **ama
`tulpar_teensy.ino`'nun `loop()`'una bilerek bağlanmadı**. Gerekçe: ELRS
alıcısı fiziksel olarak takılı değilken bu kural "hiç paket gelmedi =
failsafe" olduğu için sürekli tetiklenir ve mevcut `Serial` `G<kanal>`
bench-test aracını (ELRS'siz gaz kartı testi için var) kullanılamaz hale
getirir. Gerçek alıcı takılınca "ELRS bağlıyken failsafe aktif, değilken
bench-test modu" ayrımı nasıl yapılacak (örn. ayrı bir `ELRS_AKTIF`
bayrağı/komutu) netleşmeden otomatik zincire eklenmeyecek.

**Mimari not**: fren/taret/lazer/ELRS, gaz kartının (TCA9548A/mux) B3 güvenlik
zincirinden bağımsız — mux takılı olmasa bile `setup()`'ta bu alt sistemler
başlatılıyor (gaz/sürüş zinciri hâlâ mux gelmeden `loop()`'a ulaşamıyor, bu
değişmedi).

**⚠️ ELRS/CAN pin kararı çelişkisi**: 19 Temmuz'da "AKV'de ELRS/IMU/CAN fake
gösterilecek, pin ayrılmayacak" kararı verilmişti. 21 Temmuz'da elektronik
ekipten gelen tam pin listesi ELRS'e (Serial1) ve CAN'a (pin 22/23) gerçek pin
veriyor — bu kararı fiilen geçersiz kılıyor gibi görünüyor ama kullanıcıdan
açık bir "kararı değiştirdim" onayı alınmadı, sadece pinler koda işlendi.

## Bilinen açık noktalar

- Trimpot kalibrasyonu (255→4.15V) donanım ekibinin görevi, koda dahil değil.
- `Serial` üzerinden manuel `setGaz()` test arayüzü eklendi: `"G<kanal 0-3> <deger 0-255>"` (örn. `G0 128`) — TCA9548A yoksa/yanıt vermiyorsa komut uygulanmadan hata basar, gerçek donanım gelince aynı komutla gerçek etki test edilecek.
- Jetson→Teensy seri köprüsü (gerçek `/cmd_vel_safe` tüketimi) ayrı bir görev.
- SN65HVD230 CAN (pin 22/23, ileride Daly BMS için) hiç kod yazılmadı —
  Daly BMS'in gerçek CAN mesaj protokolü (ID'ler, byte formatı) olmadan
  anlamlı bir parser yazılamaz, elektronik ekipten protokol dokümanı gerekiyor.
