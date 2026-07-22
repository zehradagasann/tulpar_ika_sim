#pragma once

#include <cstdint>

namespace tulpar {

// Arduino Servo kutuphanesini soyutlar - boylece FrenServoKatmani gercek
// donanim olmadan PC'de (mock ile) test edilebilir. Sozlesme Servo.h ile
// ayni: attach(pin) sonra writeMicroseconds(500..2500).
class PwmCikis {
 public:
  virtual ~PwmCikis() = default;
  virtual void attach(uint8_t pin) = 0;
  virtual void writeMicroseconds(uint16_t us) = 0;
};

}  // namespace tulpar
