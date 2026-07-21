#pragma once

#include <cmath>
#include <cstdint>

#include "AdimSurucuCikis.h"

namespace tulpar {

// Tek bir taret ekseni (PAN veya TILT) icin step/dir kontrolu + KTR 5.2
// guvenlik kurali: "taret motorunda +/-90 derece yazilimsal aci siniri,
// sinira yaklasinca motor enerjisi kesilir."
//
// ** ONEMLI - ONAY BEKLEYEN DEGERLER **
// - limit_derece: roadmap'in varsayimi +/-90 derece (KTR 5.2 metninden) -
//   Emin'den (taret sahibi) gercek mekanik/yazilimsal limit degeri TEYIT
//   EDILMEDI, varsayilan olarak kullanildi.
// - derece_basina_adim: TB6600'un DIP switch mikroadim ayari + motor adim
//   acisi + varsa disli orani bilinmeden hesaplanamaz - ELEKTRONIK EKIPTEN
//   ALINMALI. Su an placeholder (1.8 derece/adim motor, mikroadim yok
//   varsayilan = 200 adim/tur = 1.8 derece/adim) - GERCEK DEGERLE
//   DEGISTIRILMEDEN saha kalibrasyonu yanlis acida duracaktir.
// - Sifir/home konumu: gercek donanimda bir mekanik/elektriksel referans
//   (limit switch/endstop) olmadan "acilista 0 derece" varsayimi gercegi
//   yansitmayabilir - Emin/elektronik ekiple homing prosedurunun nasil
//   yapilacagi netlesmeli.
class TaretEksenKatmani {
 public:
  TaretEksenKatmani(AdimSurucuCikis & cikis, float derece_basina_adim,
                     float limit_derece)
      : cikis_(cikis),
        derece_basina_adim_(derece_basina_adim),
        limit_derece_(limit_derece),
        mevcut_derece_(0.0f) {}

  // Hedef aciya gider - limiti asan hedefler kirpilir (clamp), enerji
  // kesme davranisi cagiran koddaki "limitte mi" kontroluyle (limitteMi())
  // tetiklenmeli (motor surucu enerjisini kesme fiziksel bir role/pin
  // gerektirir, bu katmanin kapsami disinda - bkz. gercek entegrasyon notu
  // asagida).
  //
  // Donus degeri: hedef kirpildiyse true (cagiran taraf "limite carptik"
  // bilgisini bu sekilde alir).
  bool hedefeGit(float hedef_derece) {
    bool kirpildi = false;
    if (hedef_derece > limit_derece_) {
      hedef_derece = limit_derece_;
      kirpildi = true;
    } else if (hedef_derece < -limit_derece_) {
      hedef_derece = -limit_derece_;
      kirpildi = true;
    }

    float fark_derece = hedef_derece - mevcut_derece_;
    if (std::fabs(fark_derece) < 1e-6f) return kirpildi;

    bool ileri = fark_derece > 0.0f;
    cikis_.yonAyarla(ileri);

    int adim_sayisi = static_cast<int>(
        std::round(std::fabs(fark_derece) / derece_basina_adim_));
    for (int i = 0; i < adim_sayisi; ++i) {
      cikis_.adimAt();
    }

    // Gercekte atilan adim sayisina gore konumu guncelle (yuvarlama hatasi
    // birikmesin diye adim_sayisi*derece_basina_adim kullanilir, fark_derece
    // degil).
    mevcut_derece_ += (ileri ? 1.0f : -1.0f) * adim_sayisi * derece_basina_adim_;
    return kirpildi;
  }

  float mevcutDerece() const { return mevcut_derece_; }

  bool limitteMi() const {
    return std::fabs(mevcut_derece_) >= limit_derece_ - 1e-3f;
  }

 private:
  AdimSurucuCikis & cikis_;
  float derece_basina_adim_;
  float limit_derece_;
  float mevcut_derece_;
};

}  // namespace tulpar
