#include "SurucuKatmani.h"

namespace tulpar {

void SurucuKatmani::tcaSelect(uint8_t kanal) {
  bus_.beginTransmission(ADDR_TCA9548A);
  bus_.write(static_cast<uint8_t>(1u << kanal));
  bus_.endTransmission();
}

void SurucuKatmani::tcaKapat() {
  bus_.beginTransmission(ADDR_TCA9548A);
  bus_.write(0x00);
  bus_.endTransmission();
}

bool SurucuKatmani::tcaSaglikliMi() {
  bus_.beginTransmission(ADDR_TCA9548A);
  return bus_.endTransmission() == 0;
}

void SurucuKatmani::setGaz(Teker teker, uint8_t deger_0_255) {
  const uint8_t kanal = static_cast<uint8_t>(teker);
  tcaSelect(kanal);
  bus_.beginTransmission(ADDR_PCF8591);
  bus_.write(PCF_CTRL_DAC);
  bus_.write(deger_0_255);
  bus_.endTransmission();
  // Ayni anda birden fazla PCF8591 (hepsi 0x48) acik kalmasin diye kanali
  // kapatiyoruz - dorduncusu de ayni adreste oldugu icin bu adres
  // celismesini onluyor (handoff B1).
  tcaKapat();
}

void SurucuKatmani::tumGazlariSifirla() {
  setGaz(ON_SOL, 0);
  setGaz(ON_SAG, 0);
  setGaz(ARKA_SOL, 0);
  setGaz(ARKA_SAG, 0);
}

}  // namespace tulpar
