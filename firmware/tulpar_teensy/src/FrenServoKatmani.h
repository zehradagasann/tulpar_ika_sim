#pragma once

#include <cstdint>

#include "PwmCikis.h"
#include "config.h"

namespace tulpar {

// 4 fren servosunu (PWM 50Hz, 500-2500us) yonetir. Elektronik ekipten gelen
// pin listesine gore (21 Temmuz 2026): ON_SOL=14, ON_SAG=15, ARKA_SOL=36,
// ARKA_SAG=37. 4 PwmCikis referansi disaridan verilir (dependency injection)
// - gercek donanimda ServoPwmCikis, PC unit testinde MockPwmCikis kullanilir.
//
// oran_0_1: 0.0 = fren yok (min PWM), 1.0 = tam fren (max PWM). Araya
// dogrusal enterpolasyon yapilir. Gercek fren tepki egrisi (servo acisi ->
// gercek fren kuvveti) mekanik ekipten kalibrasyon verisi gelmeden
// dogrusal varsayiliyor - saha testinde (Gun 11, m/s<->DAC kalibrasyonuna
// benzer sekilde) duzeltilebilir.
class FrenServoKatmani {
 public:
  FrenServoKatmani(PwmCikis & on_sol, PwmCikis & on_sag,
                    PwmCikis & arka_sol, PwmCikis & arka_sag)
      : servo_{&on_sol, &on_sag, &arka_sol, &arka_sag} {}

  void baslat() {
    servo_[ON_SOL]->attach(PIN_FREN_ON_SOL);
    servo_[ON_SAG]->attach(PIN_FREN_ON_SAG);
    servo_[ARKA_SOL]->attach(PIN_FREN_ARKA_SOL);
    servo_[ARKA_SAG]->attach(PIN_FREN_ARKA_SAG);
  }

  // Tek bir tekerin fren oranini ayarlar.
  void frenUygula(Teker teker, float oran_0_1) {
    if (oran_0_1 < 0.0f) oran_0_1 = 0.0f;
    if (oran_0_1 > 1.0f) oran_0_1 = 1.0f;
    uint16_t us = static_cast<uint16_t>(
        PWM_MIN_US + oran_0_1 * (PWM_MAX_US - PWM_MIN_US));
    servo_[teker]->writeMicroseconds(us);
  }

  // 4 tekerin de frenini ayni oranda uygular (tam durus icin).
  void tumTekerleriFrenle(float oran_0_1) {
    for (int k = 0; k < 4; ++k) {
      frenUygula(static_cast<Teker>(k), oran_0_1);
    }
  }

  // Frenleri tamamen birak (oran=0).
  void serbestBirak() { tumTekerleriFrenle(0.0f); }

 private:
  static constexpr uint16_t PWM_MIN_US = 500;
  static constexpr uint16_t PWM_MAX_US = 2500;

  PwmCikis * servo_[4];
};

}  // namespace tulpar
