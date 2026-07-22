#pragma once

// Sadece Teensyduino derlemesinde kullanilir (gercek Wire kutuphanesine
// bagli) - PC-tarafi unit testler bunun yerine test/mock_i2c_bus.h kullanir.

#include <Wire.h>

#include "I2CBus.h"

namespace tulpar {

class WireI2CBus : public I2CBus {
 public:
  void beginTransmission(uint8_t addr) override { Wire.beginTransmission(addr); }
  void write(uint8_t b) override { Wire.write(b); }
  int endTransmission() override { return Wire.endTransmission(); }
};

}  // namespace tulpar
