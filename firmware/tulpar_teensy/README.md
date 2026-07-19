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

## Bilinen açık noktalar

- Trimpot kalibrasyonu (255→4.15V) donanım ekibinin görevi, koda dahil değil.
- `Serial` üzerinden manuel `setGaz()` test arayüzü henüz yok (loop()'ta TODO).
- Jetson→Teensy seri köprüsü (gerçek `/cmd_vel_safe` tüketimi) ayrı bir görev.
