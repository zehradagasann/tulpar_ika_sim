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
// 0,1         : ELRS alici (Serial1, CRSF 420000 baud)
// 4..11       : 4x AMT102 enkoder A/B
// 14,15,36,37 : fren servolari PWM (50Hz, 500-2500us)
// 22,23       : CAN1 (SN65HVD230, Daly BMS)
// 28,29,32    : WT901C IMU (Serial7 + MAX485 DE/RE=32)

}  // namespace tulpar
