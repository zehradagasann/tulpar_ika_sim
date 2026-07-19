#pragma once

#include <cstdint>

// Kaynak: "TULPAR Gaz Karti - Donanim -> Yazilim Handoff (v1)" (19 Temmuz 2026,
// donanim/elektronik ekibinden), bolum B4. Pinler ve adresler o dokumana
// BIREBIR gore ayarlandi - baska kaynaktaki (roadmap) eski degerler DEGIL.
// Herhangi bir uyusmazlik cikarsa asil kaynak bu handoff dokumanidir.

namespace tulpar {

// --- I2C ---
constexpr uint8_t PIN_SDA = 18;
constexpr uint8_t PIN_SCL = 19;
constexpr uint32_t I2C_HZ = 100000;  // PCF8591 400 kHz DESTEKLEMEZ - sabit tut

constexpr uint8_t ADDR_TCA9548A = 0x70;
constexpr uint8_t ADDR_PCF8591 = 0x48;  // 4'u de ayni adres - mux ayirt eder
constexpr uint8_t PCF_CTRL_DAC = 0x40;  // DAC/analog cikis enable control byte

// Kanal -> teker eslemesi (mux kanali = dizin)
enum Teker : uint8_t {
  ON_SOL = 0,
  ON_SAG = 1,
  ARKA_SOL = 2,
  ARKA_SAG = 3,
};

// --- Guvenlik cikislari ---
// Aktif-HIGH. Reset/baslangicta GPIO=LOW => roleler BIRAKIR => guvenli
// varsayilan (donanimda pull-down mevcut, burada da aciktan LOW yaziliyor).
constexpr uint8_t PIN_ELRS_ROLE = 2;   // HIGH = ELRS guvenlik rolesi cekili
constexpr uint8_t PIN_KILIT_ROLE = 3;  // HIGH = surucler uyanik - ANCAK gazlar
                                        // sifirlanip I2C saglik kontrolu
                                        // gectikten SONRA HIGH yapilir
                                        // (handoff B3 kurali, tulpar_teensy.ino)

// --- Watchdog ---
constexpr uint32_t WDT_TIMEOUT_MS = 1000;  // bu sure icinde feed() gelmezse reset

// --- REZERVE (bu gaz karti kodunun DOKUNMAYACAGI pinler) ---
// Kaynak: handoff v1 B4 - baska alt sistemlere ayrildi.
//
// 19 Temmuz 2026 (kullanici karari): ELRS/IMU/CAN, AKV (video kanit)
// asamasinda donanimsal olarak FAKE gosterilecek - gercek baglanti simdilik
// hic planlanmadi. Bu yuzden pinleri burada REZERVE EDILMIYOR (handoff v1'de
// verilen degerler bilerek KULLANILMADI, bekliyor):
//   - ELRS alici        - pin HENUZ BELLI DEGIL
//   - WT901C IMU        - pin HENUZ BELLI DEGIL
//   - CAN1 / Daly BMS   - pin HENUZ BELLI DEGIL
//
// 4..11       : 4x AMT102 enkoder A/B (handoff v1 B4 - degismedi, aktif)
//
// ASAGIDAKILERIN PINI DE HENUZ BELIRLENMEDI (19 Temmuz 2026) - kullanici
// yarin bilgi verecek, o zamana kadar bos birakildi, bu kod bunlara DOKUNMUYOR:
//   - Fren servolari PWM       - PIN BELLI DEGIL
//   - Lazer/atis mekanizmasi + taret motoru - PIN BELLI DEGIL

}  // namespace tulpar
