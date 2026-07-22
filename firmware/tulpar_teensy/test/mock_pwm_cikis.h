#pragma once

#include <cstdint>

#include "../src/PwmCikis.h"

namespace tulpar {

class MockPwmCikis : public PwmCikis {
 public:
  void attach(uint8_t pin) override { attached_pin = pin; attached = true; }
  void writeMicroseconds(uint16_t us) override { son_us = us; }

  bool attached = false;
  uint8_t attached_pin = 0;
  uint16_t son_us = 0;
};

}  // namespace tulpar
