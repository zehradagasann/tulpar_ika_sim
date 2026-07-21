#pragma once

#include <cstdint>

namespace tulpar {

// ELRS (RadioMaster Nano) CRSF protokol parser'i - Serial1 (pin0/1,
// 420000 baud) uzerinden gelen byte akisini cerceve cerceve ayristirir.
// Arduino'ya bagimliligi yok (sadece cstdint) - PC'de dogrudan unit test
// edilebilir, gercek donanim/Serial olmadan.
//
// Cerceve format: [sync=0xC8][uzunluk][tip][...yuk...][crc8]
// Su an sadece RC_CHANNELS_PACKED (tip=0x16, 16 kanal x 11 bit) destekleniyor
// - CRSF'in diger cerceve tipleri (link istatistikleri vb.) yok sayilir.
class CrsfParser {
 public:
  static constexpr int KANAL_SAYISI = 16;
  static constexpr uint8_t SYNC_BYTE = 0xC8;
  static constexpr uint8_t TYPE_RC_CHANNELS_PACKED = 0x16;

  // Serial'den gelen tek bir byte'i isler, state machine'i ilerletir.
  void byteIsle(uint8_t b);

  // Gecerli (CRC dogrulanmis) bir RC_CHANNELS_PACKED cercevesi hazir mi.
  bool yeniCerceveVarMi() const { return yeni_cerceve_; }

  // Cerceve okundu, bir sonrakine kadar bayragi dusur.
  void cerceveOkundu() { yeni_cerceve_ = false; }

  // Kanalin ham CRSF degeri (172..1811 araligi, orta nokta ~992).
  uint16_t kanalHam(int i) const { return kanallar_[i]; }

  // Ham CRSF degerini standart RC PWM araligina (988..2012 us) cevirir.
  static uint16_t crsfToMicroseconds(uint16_t ham);

 private:
  enum class Durum { SYNC_BEKLE, UZUNLUK_BEKLE, VERI_BEKLE };

  static constexpr int TAMPON_BOYUTU = 64;

  Durum durum_ = Durum::SYNC_BEKLE;
  uint8_t tampon_[TAMPON_BOYUTU] = {};
  uint8_t uzunluk_ = 0;
  uint8_t index_ = 0;
  uint16_t kanallar_[KANAL_SAYISI] = {};
  bool yeni_cerceve_ = false;

  void cerceveTamamlandi();
  static void kanallariCoz(const uint8_t * yuk, uint16_t * out);
  static uint8_t crc8(const uint8_t * veri, int uzunluk);
};

}  // namespace tulpar
