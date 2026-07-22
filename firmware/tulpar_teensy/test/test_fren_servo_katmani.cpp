// Donanim OLMADAN calisan fren servo mantik testleri.
//
// Derleme: g++ -std=c++17 -I.. test_fren_servo_katmani.cpp -o /tmp/test_fren
// Calistirma: /tmp/test_fren

#include <cassert>
#include <cstdio>

#include "../src/FrenServoKatmani.h"
#include "mock_pwm_cikis.h"

using namespace tulpar;

static void test_baslat_dogru_pinlere_attach_eder() {
  MockPwmCikis on_sol, on_sag, arka_sol, arka_sag;
  FrenServoKatmani fren(on_sol, on_sag, arka_sol, arka_sag);

  fren.baslat();

  assert(on_sol.attached && on_sol.attached_pin == PIN_FREN_ON_SOL);
  assert(on_sag.attached && on_sag.attached_pin == PIN_FREN_ON_SAG);
  assert(arka_sol.attached && arka_sol.attached_pin == PIN_FREN_ARKA_SOL);
  assert(arka_sag.attached && arka_sag.attached_pin == PIN_FREN_ARKA_SAG);

  std::printf("OK: test_baslat_dogru_pinlere_attach_eder\n");
}

static void test_frenUygula_oran_0_min_pwm_verir() {
  MockPwmCikis on_sol, on_sag, arka_sol, arka_sag;
  FrenServoKatmani fren(on_sol, on_sag, arka_sol, arka_sag);

  fren.frenUygula(ON_SOL, 0.0f);
  assert(on_sol.son_us == 500);

  std::printf("OK: test_frenUygula_oran_0_min_pwm_verir\n");
}

static void test_frenUygula_oran_1_max_pwm_verir() {
  MockPwmCikis on_sol, on_sag, arka_sol, arka_sag;
  FrenServoKatmani fren(on_sol, on_sag, arka_sol, arka_sag);

  fren.frenUygula(ARKA_SAG, 1.0f);
  assert(arka_sag.son_us == 2500);

  std::printf("OK: test_frenUygula_oran_1_max_pwm_verir\n");
}

static void test_frenUygula_araliK_disi_deger_kirpilir() {
  MockPwmCikis on_sol, on_sag, arka_sol, arka_sag;
  FrenServoKatmani fren(on_sol, on_sag, arka_sol, arka_sag);

  fren.frenUygula(ON_SAG, -0.5f);
  assert(on_sag.son_us == 500);

  fren.frenUygula(ON_SAG, 1.5f);
  assert(on_sag.son_us == 2500);

  std::printf("OK: test_frenUygula_araliK_disi_deger_kirpilir\n");
}

static void test_tumTekerleriFrenle_hepsini_ayni_orana_ayarlar() {
  MockPwmCikis on_sol, on_sag, arka_sol, arka_sag;
  FrenServoKatmani fren(on_sol, on_sag, arka_sol, arka_sag);

  fren.tumTekerleriFrenle(0.5f);

  assert(on_sol.son_us == 1500);
  assert(on_sag.son_us == 1500);
  assert(arka_sol.son_us == 1500);
  assert(arka_sag.son_us == 1500);

  std::printf("OK: test_tumTekerleriFrenle_hepsini_ayni_orana_ayarlar\n");
}

static void test_serbestBirak_tum_frenleri_sifirlar() {
  MockPwmCikis on_sol, on_sag, arka_sol, arka_sag;
  FrenServoKatmani fren(on_sol, on_sag, arka_sol, arka_sag);

  fren.tumTekerleriFrenle(1.0f);
  fren.serbestBirak();

  assert(on_sol.son_us == 500);
  assert(arka_sag.son_us == 500);

  std::printf("OK: test_serbestBirak_tum_frenleri_sifirlar\n");
}

int main() {
  test_baslat_dogru_pinlere_attach_eder();
  test_frenUygula_oran_0_min_pwm_verir();
  test_frenUygula_oran_1_max_pwm_verir();
  test_frenUygula_araliK_disi_deger_kirpilir();
  test_tumTekerleriFrenle_hepsini_ayni_orana_ayarlar();
  test_serbestBirak_tum_frenleri_sifirlar();
  std::printf("Tum testler gecti.\n");
  return 0;
}
