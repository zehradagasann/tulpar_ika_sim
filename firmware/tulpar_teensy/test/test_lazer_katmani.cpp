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

static void test_baslat_guvenli_kapali_ve_silahsiz_durumdan_baslar() {
  MockDijitalCikis cikis;
  LazerKatmani lazer(cikis);

  lazer.baslat();

  assert(!lazer.acikMi());
  assert(!lazer.silahliMi());
  assert(cikis.son_deger == false);

  std::printf("OK: test_baslat_guvenli_kapali_ve_silahsiz_durumdan_baslar\n");
}

static void test_silahsizken_ac_reddedilir() {
  MockDijitalCikis cikis;
  LazerKatmani lazer(cikis);
  lazer.baslat();

  bool atesledi = lazer.ac();

  assert(!atesledi);
  assert(!lazer.acikMi());
  assert(cikis.son_deger == false);

  std::printf("OK: test_silahsizken_ac_reddedilir\n");
}

static void test_silahlandiktan_sonra_ac_ve_kapat_dogru_calisir() {
  MockDijitalCikis cikis;
  LazerKatmani lazer(cikis);
  lazer.baslat();

  lazer.silahlandir();
  assert(lazer.silahliMi());

  bool atesledi = lazer.ac();
  assert(atesledi);
  assert(lazer.acikMi());
  assert(cikis.son_deger == true);

  lazer.kapat();
  assert(!lazer.acikMi());
  assert(cikis.son_deger == false);

  std::printf("OK: test_silahlandiktan_sonra_ac_ve_kapat_dogru_calisir\n");
}

static void test_silahsizlandirma_aciksa_kapatir() {
  MockDijitalCikis cikis;
  LazerKatmani lazer(cikis);
  lazer.baslat();
  lazer.silahlandir();
  lazer.ac();
  assert(lazer.acikMi());

  lazer.silahsizlandir();

  assert(!lazer.silahliMi());
  assert(!lazer.acikMi());
  assert(cikis.son_deger == false);

  std::printf("OK: test_silahsizlandirma_aciksa_kapatir\n");
}

int main() {
  test_baslat_guvenli_kapali_ve_silahsiz_durumdan_baslar();
  test_silahsizken_ac_reddedilir();
  test_silahlandiktan_sonra_ac_ve_kapat_dogru_calisir();
  test_silahsizlandirma_aciksa_kapatir();
  std::printf("Tum testler gecti.\n");
  return 0;
}
