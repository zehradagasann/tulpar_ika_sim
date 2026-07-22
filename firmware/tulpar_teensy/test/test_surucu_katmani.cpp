// Donanim OLMADAN calisan mantik testleri - MockI2CBus ile SurucuKatmani'nin
// dogru adrese/dogru sirayla/dogru byte'lari yazdigini dogrular. Gercek
// donanim geldiginde bu testler DEGISMEZ, sadece bring-up (multimetre)
// adimlari ayrica yapilir (bkz. handoff v1, B6).
//
// Derleme: g++ -std=c++17 -I.. test_surucu_katmani.cpp ../src/SurucuKatmani.cpp -o /tmp/test_surucu
// Calistirma: /tmp/test_surucu

#include <cassert>
#include <cstdio>

#include "../src/SurucuKatmani.h"
#include "mock_i2c_bus.h"

using namespace tulpar;

static void test_setGaz_dogru_sira_ve_byte_uretir() {
  MockI2CBus bus;
  SurucuKatmani surucu(bus);

  surucu.setGaz(ARKA_SAG, 200);  // kanal 3

  // Beklenen 3 I2C islemi: mux-sec(kanal3) -> PCF DAC yaz -> mux-kapat
  assert(bus.log.size() == 3);

  assert(bus.log[0].addr == ADDR_TCA9548A);
  assert(bus.log[0].bytes.size() == 1);
  assert(bus.log[0].bytes[0] == (1 << 3));

  assert(bus.log[1].addr == ADDR_PCF8591);
  assert(bus.log[1].bytes.size() == 2);
  assert(bus.log[1].bytes[0] == PCF_CTRL_DAC);
  assert(bus.log[1].bytes[1] == 200);

  assert(bus.log[2].addr == ADDR_TCA9548A);
  assert(bus.log[2].bytes.size() == 1);
  assert(bus.log[2].bytes[0] == 0x00);

  std::printf("OK: test_setGaz_dogru_sira_ve_byte_uretir\n");
}

static void test_tumGazlariSifirla_4_kanali_da_sifirlar() {
  MockI2CBus bus;
  SurucuKatmani surucu(bus);

  surucu.tumGazlariSifirla();

  // Her kanal icin 3 islem (mux-sec, dac-yaz, mux-kapat) = 12 islem
  assert(bus.log.size() == 12);
  for (int k = 0; k < 4; ++k) {
    const auto & mux_sec = bus.log[k * 3 + 0];
    const auto & dac_yaz = bus.log[k * 3 + 1];
    assert(mux_sec.addr == ADDR_TCA9548A);
    assert(mux_sec.bytes[0] == (1 << k));
    assert(dac_yaz.addr == ADDR_PCF8591);
    assert(dac_yaz.bytes[1] == 0);  // her kanalda deger=0
  }

  std::printf("OK: test_tumGazlariSifirla_4_kanali_da_sifirlar\n");
}

static void test_tcaSaglikliMi_endTransmission_hatasinda_false_doner() {
  MockI2CBus bus;
  SurucuKatmani surucu(bus);

  bus.fail_next = true;
  assert(surucu.tcaSaglikliMi() == false);
  assert(surucu.tcaSaglikliMi() == true);  // ikinci cagri normal

  std::printf("OK: test_tcaSaglikliMi_endTransmission_hatasinda_false_doner\n");
}

static void test_setGaz_deger_sinirlarini_oldugu_gibi_gecirir() {
  MockI2CBus bus;
  SurucuKatmani surucu(bus);

  surucu.setGaz(ON_SOL, 0);
  surucu.setGaz(ON_SOL, 255);

  assert(bus.log[1].bytes[1] == 0);
  assert(bus.log[4].bytes[1] == 255);

  std::printf("OK: test_setGaz_deger_sinirlarini_oldugu_gibi_gecirir\n");
}

int main() {
  test_setGaz_dogru_sira_ve_byte_uretir();
  test_tumGazlariSifirla_4_kanali_da_sifirlar();
  test_tcaSaglikliMi_endTransmission_hatasinda_false_doner();
  test_setGaz_deger_sinirlarini_oldugu_gibi_gecirir();
  std::printf("Tum testler gecti.\n");
  return 0;
}
