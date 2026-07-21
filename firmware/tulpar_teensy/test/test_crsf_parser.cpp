// Donanim/gercek Serial OLMADAN calisan CRSF parser testleri - elle
// olusturulmus (dogru CRC'li) cerceveler ile byteIsle()'in dogru sekilde
// cozdugunu, bozuk CRC'yi reddettigini ve senkronizasyon kaybindan
// (rastgele on-ek byte'lar) kurtulabildigini dogrular.
//
// Derleme: g++ -std=c++17 -I.. test_crsf_parser.cpp ../src/CrsfParser.cpp -o /tmp/test_crsf
// Calistirma: /tmp/test_crsf

#include <cassert>
#include <cstdio>
#include <vector>

#include "../src/CrsfParser.h"

using namespace tulpar;

static uint8_t crc8_dvb_s2(const std::vector<uint8_t> & veri) {
  uint8_t crc = 0;
  for (uint8_t b : veri) {
    crc ^= b;
    for (int bit = 0; bit < 8; ++bit) {
      crc = (crc & 0x80) ? static_cast<uint8_t>((crc << 1) ^ 0xD5)
                          : static_cast<uint8_t>(crc << 1);
    }
  }
  return crc;
}

// 16 kanalin 11-bit ham degerini standart CRSF paketleme sirasina (LSB-first
// bit-packing) gore 22 byte'a sikistirir - CrsfParser::kanallariCoz'un tersi.
static std::vector<uint8_t> kanallariPaketle(const uint16_t kanallar[16]) {
  std::vector<uint8_t> payload(22, 0);
  uint32_t tampon = 0;
  int tampon_bit = 0;
  int byte_idx = 0;
  for (int k = 0; k < 16; ++k) {
    tampon |= static_cast<uint32_t>(kanallar[k] & 0x7FF) << tampon_bit;
    tampon_bit += 11;
    while (tampon_bit >= 8) {
      payload[byte_idx++] = static_cast<uint8_t>(tampon & 0xFF);
      tampon >>= 8;
      tampon_bit -= 8;
    }
  }
  if (tampon_bit > 0 && byte_idx < 22) {
    payload[byte_idx++] = static_cast<uint8_t>(tampon & 0xFF);
  }
  return payload;
}

static std::vector<uint8_t> gecerliCerceveOlustur(const uint16_t kanallar[16]) {
  std::vector<uint8_t> payload = kanallariPaketle(kanallar);
  std::vector<uint8_t> tip_ve_yuk;
  tip_ve_yuk.push_back(CrsfParser::TYPE_RC_CHANNELS_PACKED);
  tip_ve_yuk.insert(tip_ve_yuk.end(), payload.begin(), payload.end());
  uint8_t crc = crc8_dvb_s2(tip_ve_yuk);

  std::vector<uint8_t> cerceve;
  cerceve.push_back(CrsfParser::SYNC_BYTE);
  cerceve.push_back(static_cast<uint8_t>(tip_ve_yuk.size() + 1));  // tip+yuk+crc
  cerceve.insert(cerceve.end(), tip_ve_yuk.begin(), tip_ve_yuk.end());
  cerceve.push_back(crc);
  return cerceve;
}

static void test_gecerli_cerceve_dogru_kanallari_verir() {
  uint16_t kanallar[16];
  for (int i = 0; i < 16; ++i) kanallar[i] = 992 + i;  // her kanal farkli deger

  auto cerceve = gecerliCerceveOlustur(kanallar);

  CrsfParser parser;
  for (uint8_t b : cerceve) parser.byteIsle(b);

  assert(parser.yeniCerceveVarMi());
  for (int i = 0; i < 16; ++i) {
    assert(parser.kanalHam(i) == kanallar[i]);
  }

  std::printf("OK: test_gecerli_cerceve_dogru_kanallari_verir\n");
}

static void test_bozuk_crc_reddedilir() {
  uint16_t kanallar[16];
  for (int i = 0; i < 16; ++i) kanallar[i] = 992;

  auto cerceve = gecerliCerceveOlustur(kanallar);
  cerceve.back() ^= 0xFF;  // CRC'yi boz

  CrsfParser parser;
  for (uint8_t b : cerceve) parser.byteIsle(b);

  assert(!parser.yeniCerceveVarMi());

  std::printf("OK: test_bozuk_crc_reddedilir\n");
}

static void test_rastgele_on_ek_byte_senkronizasyonu_bozmaz() {
  uint16_t kanallar[16];
  for (int i = 0; i < 16; ++i) kanallar[i] = 500 + i * 10;

  auto cerceve = gecerliCerceveOlustur(kanallar);

  CrsfParser parser;
  // gurultu simulasyonu - sync byte'a (0xC8) esit OLMAYAN degerler, boylece
  // yanlis bir resync tetiklenmez (0xC8 gorulmesi gercek bir cerceve
  // baslangici sayilir, bu testin amaci degil - ayri bir senaryo)
  parser.byteIsle(0x00);
  parser.byteIsle(0xFF);
  parser.byteIsle(0x11);
  parser.byteIsle(0x22);

  for (uint8_t b : cerceve) parser.byteIsle(b);

  assert(parser.yeniCerceveVarMi());
  assert(parser.kanalHam(0) == 500);
  assert(parser.kanalHam(15) == 500 + 15 * 10);

  std::printf("OK: test_rastgele_on_ek_byte_senkronizasyonu_bozmaz\n");
}

static void test_cerceveOkundu_bayragi_dusurur() {
  uint16_t kanallar[16] = {};
  auto cerceve = gecerliCerceveOlustur(kanallar);

  CrsfParser parser;
  for (uint8_t b : cerceve) parser.byteIsle(b);
  assert(parser.yeniCerceveVarMi());

  parser.cerceveOkundu();
  assert(!parser.yeniCerceveVarMi());

  std::printf("OK: test_cerceveOkundu_bayragi_dusurur\n");
}

static void test_crsfToMicroseconds_sinirlar_ve_orta_nokta() {
  assert(CrsfParser::crsfToMicroseconds(172) == 988);
  assert(CrsfParser::crsfToMicroseconds(1811) == 2012);
  uint16_t orta = CrsfParser::crsfToMicroseconds(992);
  assert(orta > 1490 && orta < 1510);  // ~1500us civari

  std::printf("OK: test_crsfToMicroseconds_sinirlar_ve_orta_nokta\n");
}

int main() {
  test_gecerli_cerceve_dogru_kanallari_verir();
  test_bozuk_crc_reddedilir();
  test_rastgele_on_ek_byte_senkronizasyonu_bozmaz();
  test_cerceveOkundu_bayragi_dusurur();
  test_crsfToMicroseconds_sinirlar_ve_orta_nokta();
  std::printf("Tum testler gecti.\n");
  return 0;
}
