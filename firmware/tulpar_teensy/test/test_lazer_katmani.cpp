// Donanim OLMADAN calisan lazer role mantik testleri - ozellikle baslat()'in
// guvenli varsayilan (kapali) durumdan basladigini dogrular (SurucuKatmani'nin
// "setup()'ta ilk is DAC=0" kuraliyla ayni mantik).
//
// Derleme: g++ -std=c++17 -I.. test_lazer_katmani.cpp -o /tmp/test_lazer
// Calistirma: /tmp/test_lazer

#include <cassert>
#include <cstdio>

#include "../src/LazerKatmani.h"
#include "mock_dijital_cikis.h"

using namespace tulpar;

static void test_baslat_guvenli_kapali_durumdan_baslar() {
  MockDijitalCikis cikis;
  LazerKatmani lazer(cikis);

  lazer.baslat();

  assert(!lazer.acikMi());
  assert(cikis.son_deger == false);

  std::printf("OK: test_baslat_guvenli_kapali_durumdan_baslar\n");
}

static void test_ac_ve_kapat_dogru_calisir() {
  MockDijitalCikis cikis;
  LazerKatmani lazer(cikis);
  lazer.baslat();

  lazer.ac();
  assert(lazer.acikMi());
  assert(cikis.son_deger == true);

  lazer.kapat();
  assert(!lazer.acikMi());
  assert(cikis.son_deger == false);

  std::printf("OK: test_ac_ve_kapat_dogru_calisir\n");
}

int main() {
  test_baslat_guvenli_kapali_durumdan_baslar();
  test_ac_ve_kapat_dogru_calisir();
  std::printf("Tum testler gecti.\n");
  return 0;
}
