#pragma once

#include <Arduino.h>

#include "AdimSurucuCikis.h"

namespace tulpar {

// AdimSurucuCikis'in gercek Teensy pinleriyle calisan impl'i. Sadece gercek
// donanimda derlenir - PC unit testlerinde MockAdimSurucuCikis kullanilir.
class TB6600Cikis : public AdimSurucuCikis {
 public:
  TB6600Cikis(uint8_t pul_pin, uint8_t dir_pin)
      : pul_pin_(pul_pin), dir_pin_(dir_pin) {
    pinMode(pul_pin_, OUTPUT);
    pinMode(dir_pin_, OUTPUT);
    digitalWrite(pul_pin_, LOW);
    digitalWrite(dir_pin_, LOW);
  }

  void yonAyarla(bool ileri) override {
    digitalWrite(dir_pin_, ileri ? HIGH : LOW);
    delayMicroseconds(5);  // TB6600 DIR setup suresi
  }

  void adimAt() override {
    digitalWrite(pul_pin_, HIGH);
    delayMicroseconds(10);  // TB6600 min pulse genisligi
    digitalWrite(pul_pin_, LOW);
    delayMicroseconds(10);
  }

 private:
  uint8_t pul_pin_;
  uint8_t dir_pin_;
};

}  // namespace tulpar
