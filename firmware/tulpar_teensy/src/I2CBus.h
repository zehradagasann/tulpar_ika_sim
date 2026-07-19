#pragma once

#include <cstdint>

namespace tulpar {

// Wire'in (TwoWire) gercek Teensy davranisini soyutlar - boylece
// SurucuKatmani, gercek I2C donanimi olmadan PC'de (mock ile) test edilebilir.
// Sozlesme Wire.h ile ayni: endTransmission() 0 dondururse basarili.
class I2CBus {
 public:
  virtual ~I2CBus() = default;
  virtual void beginTransmission(uint8_t addr) = 0;
  virtual void write(uint8_t b) = 0;
  virtual int endTransmission() = 0;
};

}  // namespace tulpar
