#pragma once

namespace tulpar {

// TB6600 step/dir surucusune giden PUL/DIR pinlerini soyutlar - boylece
// TaretEksenKatmani gercek donanim olmadan PC'de (mock ile) test edilebilir.
// Gercek zamanlama (pulse genisligi, min bekleme) sadece gercek impl'de.
class AdimSurucuCikis {
 public:
  virtual ~AdimSurucuCikis() = default;
  virtual void yonAyarla(bool ileri) = 0;
  virtual void adimAt() = 0;  // tek bir PUL darbesi uretir
};

}  // namespace tulpar
