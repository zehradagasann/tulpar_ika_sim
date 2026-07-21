#pragma once

#include <Arduino.h>

#include "DijitalCikis.h"

namespace tulpar {

// DijitalCikis'in gercek Teensy piniyle calisan impl'i. Sadece gercek
// donanimda derlenir - PC unit testlerinde MockDijitalCikis kullanilir.
class GercekDijitalCikis : public DijitalCikis {
 public:
  explicit GercekDijitalCikis(uint8_t pin) : pin_(pin) {
    pinMode(pin_, OUTPUT);
    digitalWrite(pin_, LOW);
  }

  void yaz(bool yuksek) override { digitalWrite(pin_, yuksek ? HIGH : LOW); }

 private:
  uint8_t pin_;
};

}  // namespace tulpar
