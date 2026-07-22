#pragma once

#include <cstdint>

namespace tulpar {

// ELRS failsafe zamanlamasi (roadmap: "CRSF'den 400ms paket gelmezse -> 4
// kanala DAC=0 + kilit rolesi LOW"). Zaman disaridan verilir (millis()
// dogrudan cagrilmaz) - boylece PC'de sahte zaman degerleriyle test
// edilebilir, gercek Teensy'de tulpar_teensy.ino millis()'i besler.
class ElrsFailsafeKatmani {
 public:
  explicit ElrsFailsafeKatmani(uint32_t zaman_asimi_ms) : zaman_asimi_ms_(zaman_asimi_ms) {}

  void paketGeldi(uint32_t simdi_ms) {
    son_paket_ms_ = simdi_ms;
    paket_alindi_mi_ = true;
  }

  // Hic paket gelmediyse (acilis ani) de guvenli varsayilan olarak
  // failsafe kabul edilir - "veri yok" ile "veri var ama eski" ayni
  // sekilde ele alinir.
  bool failsafeMi(uint32_t simdi_ms) const {
    if (!paket_alindi_mi_) return true;
    return (simdi_ms - son_paket_ms_) > zaman_asimi_ms_;
  }

 private:
  uint32_t zaman_asimi_ms_;
  uint32_t son_paket_ms_ = 0;
  bool paket_alindi_mi_ = false;
};

}  // namespace tulpar
