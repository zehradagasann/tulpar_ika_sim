// Donanim/gercek zaman OLMADAN calisan ELRS failsafe zamanlama testleri.
//
// Derleme: g++ -std=c++17 -I.. test_elrs_failsafe_katmani.cpp -o /tmp/test_failsafe
// Calistirma: /tmp/test_failsafe

#include <cassert>
#include <cstdio>

#include "../src/ElrsFailsafeKatmani.h"

using namespace tulpar;

static void test_hic_paket_gelmediyse_failsafe_true() {
  ElrsFailsafeKatmani fs(400);
  assert(fs.failsafeMi(0));
  assert(fs.failsafeMi(1000));

  std::printf("OK: test_hic_paket_gelmediyse_failsafe_true\n");
}

static void test_esik_altinda_failsafe_degil() {
  ElrsFailsafeKatmani fs(400);
  fs.paketGeldi(1000);

  assert(!fs.failsafeMi(1399));  // 399ms fark

  std::printf("OK: test_esik_altinda_failsafe_degil\n");
}

static void test_esik_ustunde_failsafe_true() {
  ElrsFailsafeKatmani fs(400);
  fs.paketGeldi(1000);

  assert(fs.failsafeMi(1401));  // 401ms fark

  std::printf("OK: test_esik_ustunde_failsafe_true\n");
}

static void test_yeni_paket_failsafe_i_sifirlar() {
  ElrsFailsafeKatmani fs(400);
  fs.paketGeldi(1000);
  assert(fs.failsafeMi(1500));  // failsafe'e girdi (500ms fark)

  fs.paketGeldi(1500);  // yeni paket geldi
  assert(!fs.failsafeMi(1600));  // artik guvenli (100ms fark)

  std::printf("OK: test_yeni_paket_failsafe_i_sifirlar\n");
}

int main() {
  test_hic_paket_gelmediyse_failsafe_true();
  test_esik_altinda_failsafe_degil();
  test_esik_ustunde_failsafe_true();
  test_yeni_paket_failsafe_i_sifirlar();
  std::printf("Tum testler gecti.\n");
  return 0;
}
