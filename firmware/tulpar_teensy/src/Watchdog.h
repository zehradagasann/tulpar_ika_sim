#pragma once

// Teensy 4.1 donanimsal WDT sarmalayicisi. PCF8591'in kendi watchdog'u
// olmadigi icin (handoff v1, "Yeni Kritik Uyarilar") Teensy donarsa DAC son
// degerde asili kalir - bu yuzden WDT acik olmadan hicbir commit kabul
// edilmemeli. Reset sonrasi setup() yeniden calisip gazlari sifirlar.
//
// Bagimlilik: "Watchdog_t4" kutuphanesi (Arduino Library Manager, tonton81) -
// Teensy 4.x icin yaygin kullanilan donanimsal WDT sarmalayicisi.

#include <Watchdog_t4.h>

namespace tulpar {

class Watchdog {
 public:
  void begin(uint32_t timeout_ms);
  void feed();

 private:
  WDT_T4<WDT1> wdt_;
};

}  // namespace tulpar
