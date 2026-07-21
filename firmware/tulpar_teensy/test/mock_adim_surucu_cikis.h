#pragma once

#include "../src/AdimSurucuCikis.h"

namespace tulpar {

class MockAdimSurucuCikis : public AdimSurucuCikis {
 public:
  void yonAyarla(bool ileri) override { son_yon_ileri = ileri; }
  void adimAt() override {
    adim_sayaci += son_yon_ileri ? 1 : -1;
    toplam_adim_cagrisi++;
  }

  bool son_yon_ileri = true;
  int adim_sayaci = 0;        // net yonlu adim (ileri - geri)
  int toplam_adim_cagrisi = 0;
};

}  // namespace tulpar
