#pragma once

#include <cstdint>
#include <vector>

#include "../src/I2CBus.h"

namespace tulpar {

struct I2CTransaction {
  uint8_t addr;
  std::vector<uint8_t> bytes;
};

// Gercek I2C donanimi olmadan SurucuKatmani mantigini test etmek icin sahte
// bus - hangi adrese hangi byte'larin, hangi sirayla yazildigini kaydeder.
class MockI2CBus : public I2CBus {
 public:
  void beginTransmission(uint8_t addr) override {
    current_.addr = addr;
    current_.bytes.clear();
  }

  void write(uint8_t b) override { current_.bytes.push_back(b); }

  int endTransmission() override {
    log.push_back(current_);
    if (fail_next) {
      fail_next = false;
      return 1;
    }
    return 0;
  }

  std::vector<I2CTransaction> log;
  bool fail_next = false;

 private:
  I2CTransaction current_;
};

}  // namespace tulpar
