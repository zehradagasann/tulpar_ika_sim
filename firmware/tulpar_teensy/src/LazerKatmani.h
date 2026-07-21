#pragma once

#include "DijitalCikis.h"

namespace tulpar {

// Lazer role kartini (pin 40 -> role IN ucu) yonetir. Guvenlik kurali:
// setup()'ta ILK IS lazer KAPALI olmali (SurucuKatmani'nin "ilk is DAC=0"
// kuralindaki ayni mantik) - kilit rolesi HIGH olmadan/gaz sifirlanmadan
// lazer asla ateslenmemeli. Bu kisitin uygulanmasi (kilit rolesi durumunu
// kontrol etmek) bu katmanin degil, cagiran ana dongunun sorumlulugunda -
// bkz. tulpar_teensy.ino.
class LazerKatmani {
 public:
  explicit LazerKatmani(DijitalCikis & cikis) : cikis_(cikis) {}

  void baslat() { kapat(); }  // guvenli varsayilan: kapali

  void ac() { acik_ = true; cikis_.yaz(true); }
  void kapat() { acik_ = false; cikis_.yaz(false); }

  bool acikMi() const { return acik_; }

 private:
  DijitalCikis & cikis_;
  bool acik_ = false;
};

}  // namespace tulpar
