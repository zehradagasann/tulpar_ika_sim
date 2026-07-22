#pragma once

#include "../src/DijitalCikis.h"

namespace tulpar {

class MockDijitalCikis : public DijitalCikis {
 public:
  void yaz(bool yuksek) override { son_deger = yuksek; yazma_sayisi++; }

  bool son_deger = false;
  int yazma_sayisi = 0;
};

}  // namespace tulpar
