#pragma once

#include <cstdint>

#include "I2CBus.h"
#include "config.h"

namespace tulpar {

// TCA9548A mux + 4x PCF8591 DAC zincirini yonetir (handoff v1, B1/B4).
// I2CBus baglantisi disaridan verilir (dependency injection) - gercek
// donanimda WireI2CBus, PC unit testinde MockI2CBus kullanilir.
class SurucuKatmani {
 public:
  explicit SurucuKatmani(I2CBus & bus) : bus_(bus) {}

  // TCA9548A'nin (0x70) I2C'de yanit verip vermedigini kontrol eder.
  bool tcaSaglikliMi();

  // Bir tekerin gaz degerini yazar: mux kanalini sec -> PCF8591'e
  // {PCF_CTRL_DAC, deger} yaz -> mux kanalini kapat (handoff B1/B4).
  void setGaz(Teker teker, uint8_t deger_0_255);

  // 4 tekerin de gazini sifirlar. setup()'ta Wire.begin() SONRASI ilk I2C
  // trafigi bu olmali (handoff B3) - guvenlik kritik siralama.
  void tumGazlariSifirla();

 private:
  void tcaSelect(uint8_t kanal);
  void tcaKapat();

  I2CBus & bus_;
};

}  // namespace tulpar
