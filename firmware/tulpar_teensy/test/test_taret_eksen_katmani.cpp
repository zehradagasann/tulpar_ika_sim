// Donanim OLMADAN calisan taret ekseni mantik testleri - ozellikle KTR 5.2
// guvenlik kurali olan +/-90 derece yazilimsal aci sinirinin GERCEKTEN
// kirpildigini dogrular.
//
// Derleme: g++ -std=c++17 -I.. test_taret_eksen_katmani.cpp -o /tmp/test_taret
// Calistirma: /tmp/test_taret

#include <cassert>
#include <cmath>
#include <cstdio>

#include "../src/TaretEksenKatmani.h"
#include "mock_adim_surucu_cikis.h"

using namespace tulpar;

static bool yaklasikEsit(float a, float b, float tol = 0.01f) {
  return std::fabs(a - b) < tol;
}

static void test_hedefeGit_limit_icinde_dogru_adim_atar() {
  MockAdimSurucuCikis cikis;
  // 1.8 derece/adim, limit=90 derece
  TaretEksenKatmani taret(cikis, 1.8f, 90.0f);

  bool kirpildi = taret.hedefeGit(18.0f);  // 10 adim gerekir

  assert(!kirpildi);
  assert(cikis.son_yon_ileri == true);
  assert(cikis.toplam_adim_cagrisi == 10);
  assert(yaklasikEsit(taret.mevcutDerece(), 18.0f));

  std::printf("OK: test_hedefeGit_limit_icinde_dogru_adim_atar\n");
}

static void test_hedefeGit_limit_disi_hedef_kirpilir() {
  MockAdimSurucuCikis cikis;
  TaretEksenKatmani taret(cikis, 1.8f, 90.0f);

  bool kirpildi = taret.hedefeGit(150.0f);  // limit disi

  assert(kirpildi);
  assert(yaklasikEsit(taret.mevcutDerece(), 90.0f, 1.0f));  // ~limit civarinda

  std::printf("OK: test_hedefeGit_limit_disi_hedef_kirpilir\n");
}

static void test_hedefeGit_negatif_limit_de_kirpilir() {
  MockAdimSurucuCikis cikis;
  TaretEksenKatmani taret(cikis, 1.8f, 90.0f);

  bool kirpildi = taret.hedefeGit(-200.0f);

  assert(kirpildi);
  assert(cikis.son_yon_ileri == false);
  assert(yaklasikEsit(taret.mevcutDerece(), -90.0f, 1.0f));

  std::printf("OK: test_hedefeGit_negatif_limit_de_kirpilir\n");
}

static void test_geri_donus_dogru_yonde_adim_atar() {
  MockAdimSurucuCikis cikis;
  TaretEksenKatmani taret(cikis, 1.8f, 90.0f);

  taret.hedefeGit(36.0f);   // ileri 20 adim
  taret.hedefeGit(0.0f);    // geri donmeli

  assert(cikis.son_yon_ileri == false);
  assert(yaklasikEsit(taret.mevcutDerece(), 0.0f, 0.5f));

  std::printf("OK: test_geri_donus_dogru_yonde_adim_atar\n");
}

static void test_limitteMi_dogru_calisir() {
  MockAdimSurucuCikis cikis;
  TaretEksenKatmani taret(cikis, 1.8f, 90.0f);

  assert(!taret.limitteMi());
  taret.hedefeGit(200.0f);  // limite kirpilir
  assert(taret.limitteMi());

  std::printf("OK: test_limitteMi_dogru_calisir\n");
}

int main() {
  test_hedefeGit_limit_icinde_dogru_adim_atar();
  test_hedefeGit_limit_disi_hedef_kirpilir();
  test_hedefeGit_negatif_limit_de_kirpilir();
  test_geri_donus_dogru_yonde_adim_atar();
  test_limitteMi_dogru_calisir();
  std::printf("Tum testler gecti.\n");
  return 0;
}
