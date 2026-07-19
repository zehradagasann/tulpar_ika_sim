// TULPAR IKA - Gaz Karti Firmware (Teensy 4.1)
//
// Kaynak: "TULPAR Gaz Karti - Donanim -> Yazilim Handoff (v1)" (19 Temmuz
// 2026). setup() sirasi dokumanin B3 bolumundeki guvenlik sirasini BIREBIR
// takip eder:
//   1. Kilit/ELRS roleleri aciktan LOW'a sabitlenir (guvenli varsayilan)
//   2. Wire.begin() + setClock(100000)
//   3. HEMEN ardindan 4 kanala da setGaz(0) - ilk I2C trafigi bu olmali
//   4. TCA9548A saglik kontrolu (0x70 ACK) - basarisizsa kilit LOW kalir
//   5. WDT acilir (reset -> setup() -> adim 3 gazlari yine sifirlar)
//   6. Gazlar sifirlanip saglik kontrolu gectikten SONRA kilit HIGH yapilir
//
// Bagimlilik: Arduino Library Manager'dan "Watchdog_t4" (tonton81) kurulmali.
// Board: Teensy 4.1 (Teensyduino).

#include "src/SurucuKatmani.h"
#include "src/Watchdog.h"
#include "src/WireI2CBus.h"
#include "src/config.h"

tulpar::WireI2CBus i2c_bus;
tulpar::SurucuKatmani surucu(i2c_bus);
tulpar::Watchdog wdt;

void setup() {
  Serial.begin(115200);

  // 1) Guvenli varsayilan: roleler aciktan LOW (donanimda zaten pull-down var,
  // burada yazilim tarafinda da ayni garantiyi acikca veriyoruz).
  pinMode(tulpar::PIN_KILIT_ROLE, OUTPUT);
  digitalWrite(tulpar::PIN_KILIT_ROLE, LOW);
  pinMode(tulpar::PIN_ELRS_ROLE, OUTPUT);
  digitalWrite(tulpar::PIN_ELRS_ROLE, LOW);

  // 2) I2C baslat - PCF8591 400 kHz desteklemedigi icin 100 kHz'de sabit.
  Wire.begin();
  Wire.setClock(tulpar::I2C_HZ);

  // 3) Ilk I2C trafigi: 4 kanala da gaz=0 yaz (handoff B3, adim 2).
  surucu.tumGazlariSifirla();

  // 4) TCA9548A yanit vermiyorsa kilit LOW kalir, sonsuz dongude bekle -
  // WDT bir sure sonra tetiklenip setup()'i yeniden calistirir.
  if (!surucu.tcaSaglikliMi()) {
    Serial.println("HATA: TCA9548A (0x70) yanit vermiyor - kilit LOW kaliyor.");
    while (true) {
      delay(500);
    }
  }

  // 5) WDT'yi ac - reset sonrasi setup() yeniden calisip gazlari sifirlar.
  wdt.begin(tulpar::WDT_TIMEOUT_MS);

  // 6) Gazlar sifirlanip I2C saglikli dogrulandiktan SONRA kilit acilir
  // (handoff B3 kurali - acilis anindaki DAC-tanimsizligi motorlara ulasmasin).
  digitalWrite(tulpar::PIN_KILIT_ROLE, HIGH);

  Serial.println("tulpar_teensy hazir.");
}

void loop() {
  wdt.feed();

  // TODO: /cmd_vel_safe -> Teensy seri koprusu gelene kadar, gaz kartini
  // izole test etmek icin basit bir Serial komut arayuzu eklenebilir
  // (orn. "G0 128" -> surucu.setGaz(tulpar::ON_SOL, 128)).

  delay(10);
}
