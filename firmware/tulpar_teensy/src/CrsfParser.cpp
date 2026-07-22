#include "CrsfParser.h"

namespace tulpar {

void CrsfParser::byteIsle(uint8_t b) {
  switch (durum_) {
    case Durum::SYNC_BEKLE:
      if (b == SYNC_BYTE) {
        durum_ = Durum::UZUNLUK_BEKLE;
      }
      break;

    case Durum::UZUNLUK_BEKLE:
      // uzunluk = tip(1) + yuk(N) + crc(1); en az 2 (tip+crc), tampon tasmasin
      if (b < 2 || b > TAMPON_BOYUTU) {
        durum_ = Durum::SYNC_BEKLE;
        break;
      }
      uzunluk_ = b;
      index_ = 0;
      durum_ = Durum::VERI_BEKLE;
      break;

    case Durum::VERI_BEKLE:
      tampon_[index_++] = b;
      if (index_ >= uzunluk_) {
        cerceveTamamlandi();
        durum_ = Durum::SYNC_BEKLE;
      }
      break;
  }
}

void CrsfParser::cerceveTamamlandi() {
  // tampon_[0] = tip, tampon_[1..uzunluk_-2] = yuk, tampon_[uzunluk_-1] = crc
  uint8_t alinan_crc = tampon_[uzunluk_ - 1];
  uint8_t hesaplanan_crc = crc8(tampon_, uzunluk_ - 1);  // tip+yuk uzerinden
  if (alinan_crc != hesaplanan_crc) {
    return;  // bozuk cerceve, sessizce at
  }

  uint8_t tip = tampon_[0];
  int yuk_uzunlugu = uzunluk_ - 2;  // tip ve crc haric
  if (tip == TYPE_RC_CHANNELS_PACKED && yuk_uzunlugu == 22) {
    kanallariCoz(&tampon_[1], kanallar_);
    yeni_cerceve_ = true;
  }
  // baska tipler (link istatistikleri vb.) simdilik yok sayiliyor
}

void CrsfParser::kanallariCoz(const uint8_t * yuk, uint16_t * out) {
  uint32_t tampon = 0;
  int tampon_bit = 0;
  int kanal_idx = 0;
  for (int i = 0; i < 22 && kanal_idx < KANAL_SAYISI; ++i) {
    tampon |= static_cast<uint32_t>(yuk[i]) << tampon_bit;
    tampon_bit += 8;
    while (tampon_bit >= 11 && kanal_idx < KANAL_SAYISI) {
      out[kanal_idx++] = static_cast<uint16_t>(tampon & 0x7FF);
      tampon >>= 11;
      tampon_bit -= 11;
    }
  }
}

uint8_t CrsfParser::crc8(const uint8_t * veri, int uzunluk) {
  // CRC8 DVB-S2, poly 0xD5 - CRSF standardi
  uint8_t crc = 0;
  for (int i = 0; i < uzunluk; ++i) {
    crc ^= veri[i];
    for (int bit = 0; bit < 8; ++bit) {
      if (crc & 0x80) {
        crc = static_cast<uint8_t>((crc << 1) ^ 0xD5);
      } else {
        crc = static_cast<uint8_t>(crc << 1);
      }
    }
  }
  return crc;
}

uint16_t CrsfParser::crsfToMicroseconds(uint16_t ham) {
  // Standart CRSF->PWM donusumu: 172..1811 -> 988..2012 us
  if (ham < 172) ham = 172;
  if (ham > 1811) ham = 1811;
  return static_cast<uint16_t>(988.0f + (ham - 172) * (2012.0f - 988.0f) / (1811.0f - 172.0f));
}

}  // namespace tulpar
