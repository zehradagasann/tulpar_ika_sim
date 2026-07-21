#pragma once

#include <Servo.h>

#include "PwmCikis.h"

namespace tulpar {

// PwmCikis'in gercek Teensy/Arduino Servo kutuphanesiyle calisan impl'i.
// Sadece gercek donanimda derlenir (Servo.h Arduino framework'une bagli) -
// PC unit testlerinde bunun yerine MockPwmCikis kullanilir.
class ServoPwmCikis : public PwmCikis {
 public:
  void attach(uint8_t pin) override { servo_.attach(pin); }
  void writeMicroseconds(uint16_t us) override { servo_.writeMicroseconds(us); }

 private:
  Servo servo_;
};

}  // namespace tulpar
