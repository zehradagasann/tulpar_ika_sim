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

// --- Enkoderler (4x AMT102, quadrature A/B) ---
constexpr uint8_t PIN_ENC_ON_SOL_A = 4;
constexpr uint8_t PIN_ENC_ON_SOL_B = 5;
constexpr uint8_t PIN_ENC_ON_SAG_A = 6;
constexpr uint8_t PIN_ENC_ON_SAG_B = 7;
constexpr uint8_t PIN_ENC_ARKA_SOL_A = 8;
constexpr uint8_t PIN_ENC_ARKA_SOL_B = 9;
constexpr uint8_t PIN_ENC_ARKA_SAG_A = 10;
constexpr uint8_t PIN_ENC_ARKA_SAG_B = 11;

// --- ELRS alici (RadioMaster Nano, CRSF) ---
// 21 Temmuz 2026: elektronik ekipten gercek pin geldi - bu, 19 Temmuz'daki
// "ELRS/IMU/CAN AKV'de fake gosterilecek, pin ayrilmiyor" kararini ELRS icin
// GECERSIZ KILIYOR (IMU icin hala pin verilmedi, asagiya bkz). Serial1
// uzerinden: pin0=RX1 (alicinin TX'inden gelir), pin1=TX1 (alicinin RX'ine
// gider). Besleme 5V+GND raydan, Teensy'den degil.
constexpr uint8_t PIN_ELRS_RX = 0;   // Serial1 RX1
constexpr uint8_t PIN_ELRS_TX = 1;   // Serial1 TX1
constexpr uint32_t ELRS_CRSF_BAUD = 420000;
constexpr uint32_t ELRS_FAILSAFE_TIMEOUT_MS = 400;  // roadmap: 400ms paket gelmezse failsafe

// --- Fren servolari (PWM 50Hz, 500-2500us) ---
// 21 Temmuz 2026: elektronik ekipten geldi, onceki "PIN BELLI DEGIL" notu kapandi.
constexpr uint8_t PIN_FREN_ON_SOL = 14;
constexpr uint8_t PIN_FREN_ON_SAG = 15;
constexpr uint8_t PIN_FREN_ARKA_SOL = 36;
constexpr uint8_t PIN_FREN_ARKA_SAG = 37;

// --- SN65HVD230 CAN modulu (ileride Daly BMS icin, 3.3V beslemeli) ---
// 21 Temmuz 2026: elektronik ekipten geldi - bu da 19 Temmuz'daki "CAN icin
// pin ayrilmiyor" kararini GECERSIZ KILIYOR.
constexpr uint8_t PIN_CAN_TX = 22;  // CTX1 -> modulun D/CTX ucu
constexpr uint8_t PIN_CAN_RX = 23;  // CRX1 <- modulun R/CRX ucu

// --- Taret (TB6600 step/dir surucu, PUL-/DIR- GND rayina ortak) ---
constexpr uint8_t PIN_TARET_PAN_PUL = 33;
constexpr uint8_t PIN_TARET_PAN_DIR = 34;
constexpr uint8_t PIN_TARET_TILT_PUL = 35;
constexpr uint8_t PIN_TARET_TILT_DIR = 38;

// --- Lazer role karti ---
constexpr uint8_t PIN_LAZER_ROLE = 40;  // -> role kartinin IN ucu, VCC/GND raydan

// --- REZERVE / HALA BELLI DEGIL ---
// Kaynak: handoff v1 B4 + 21 Temmuz 2026 elektronik ekip pin listesi.
//   - WT901C IMU - pin/arayuz HALA BELLI DEGIL (21 Temmuz listesinde de yok,
//     muhtemelen RS485 uzerinden ayri bir yerden - teyit gerekli)
//   - 4x PCF8591 + OP291 - Teensy'ye DOGRUDAN pin baglantisi YOK, TCA9548A'nin
//     arkasinda I2C uzerinden erisiliyor (yukaridaki PIN_SDA/PIN_SCL)

}  // namespace tulpar
