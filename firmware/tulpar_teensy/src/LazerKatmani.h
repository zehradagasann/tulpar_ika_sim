#pragma once

#include "DijitalCikis.h"

namespace tulpar {

// Lazer role kartini (pin 40 -> role IN ucu) yonetir.
//
// GUVENLIK ARA KILIDI (interlock, 22 Temmuz 2026 eklendi): onceki halde
// ac() (seri "L1") kosulsuz atesliyordu - "otonom izin" kontrolu hicbir
// yerde yoktu, sorumluluk cagiran ana donguye birakilmisti ama dongu bunu
// hic uygulamiyordu. Artik ac() SADECE silahlandir() (seri "S1") onceden
// cagrilmissa gercekten atesler; aksi halde sessizce reddedip false doner.
// Jetson/BT tarafi (AtisYap) hedef kilitlendi + atis bolgesi dogrulandi
// gibi kendi kosullarini kontrol ettikten SONRA "S1" gonderip silahlandirmali,
// atesten hemen once/sonra "S0" ile silahsizlandirmali - boylece tek bir
// yanlislikla gonderilen "L1" baslibasina asla ates etmez.
class LazerKatmani {
 public:
  explicit LazerKatmani(DijitalCikis & cikis) : cikis_(cikis) {}

  // Guvenli varsayilan: kapali VE silahsiz.
  void baslat() { kapat(); silahsizlandir(); }

  void silahlandir() { silahli_ = true; }
  void silahsizlandir() { silahli_ = false; kapat(); }
  bool silahliMi() const { return silahli_; }

  // Silahli degilse atesLemez, false doner (cagiran taraf ayirt edebilsin).
  bool ac() {
    if (!silahli_) return false;
    acik_ = true;
    cikis_.yaz(true);
    return true;
  }
  void kapat() { acik_ = false; cikis_.yaz(false); }

  bool acikMi() const { return acik_; }

 private:
  DijitalCikis & cikis_;
  bool acik_ = false;
  bool silahli_ = false;
};

}  // namespace tulpar
