// TULPAR IKA - Gaz Karti Firmware (Teensy 4.1)
//
// Kaynak: "TULPAR Gaz Karti - Donanim -> Yazilim Handoff (v1)" (19 Temmuz
// 2026). setup() sirasi dokumanin B3 bolumundeki guvenlik sirasini BIREBIR
// takip eder:
//   1. Kilit/ELRS roleleri aciktan LOW'a sabitlenir (guvenli varsayilan)
//   2. Wire.begin() + setClock(100000)
//   3. HEMEN ardindan 4 kanala da setGaz(0) - ilk I2C trafigi bu olmali
//   4. TCA9548A saglik kontrolu (0x70 ACK) - basarisizsa kilit LOW kalir
//   5. WDT acilir (reset -> setup() -> adim 3 gazlari yine sifirlar)
//   6. Gazlar sifirlanip saglik kontrolu gectikten SONRA kilit HIGH yapilir
//
// Bagimlilik: Arduino Library Manager'dan "Watchdog_t4" (tonton81) kurulmali.
// Board: Teensy 4.1 (Teensyduino).

#include "src/AdimSurucuCikis.h"
#include "src/CrsfParser.h"
#include "src/DijitalCikis.h"
#include "src/ElrsFailsafeKatmani.h"
#include "src/FrenServoKatmani.h"
#include "src/GercekDijitalCikis.h"
#include "src/LazerKatmani.h"
#include "src/PwmCikis.h"
#include "src/ServoPwmCikis.h"
#include "src/SurucuKatmani.h"
#include "src/TB6600Cikis.h"
#include "src/TaretEksenKatmani.h"
#include "src/Watchdog.h"
#include "src/WireI2CBus.h"
#include "src/config.h"

tulpar::WireI2CBus i2c_bus;
tulpar::SurucuKatmani surucu(i2c_bus);
tulpar::Watchdog wdt;

// Fren servolari (pin 14/15/36/37, elektronik ekipten 21 Temmuz 2026).
tulpar::ServoPwmCikis fren_on_sol_cikis, fren_on_sag_cikis;
tulpar::ServoPwmCikis fren_arka_sol_cikis, fren_arka_sag_cikis;
tulpar::FrenServoKatmani fren(fren_on_sol_cikis, fren_on_sag_cikis,
                               fren_arka_sol_cikis, fren_arka_sag_cikis);

// Taret PAN/TILT (TB6600, pin 33/34 ve 35/38). derece_basina_adim ve
// limit_derece HENUZ TEYIT EDILMEDI - bkz. TaretEksenKatmani.h dokstring'i.
tulpar::TB6600Cikis taret_pan_cikis(tulpar::PIN_TARET_PAN_PUL, tulpar::PIN_TARET_PAN_DIR);
tulpar::TB6600Cikis taret_tilt_cikis(tulpar::PIN_TARET_TILT_PUL, tulpar::PIN_TARET_TILT_DIR);
tulpar::TaretEksenKatmani taret_pan(taret_pan_cikis, /*derece_basina_adim=*/1.8f, /*limit_derece=*/90.0f);
tulpar::TaretEksenKatmani taret_tilt(taret_tilt_cikis, /*derece_basina_adim=*/1.8f, /*limit_derece=*/90.0f);

// Lazer role (pin 40).
tulpar::GercekDijitalCikis lazer_cikis(tulpar::PIN_LAZER_ROLE);
tulpar::LazerKatmani lazer(lazer_cikis);

// ELRS/CRSF alici (Serial1, pin 0/1, 420000 baud).
tulpar::CrsfParser crsf;
tulpar::ElrsFailsafeKatmani elrs_failsafe(tulpar::ELRS_FAILSAFE_TIMEOUT_MS);

void setup() {
  Serial.begin(115200);

  // 1) Guvenli varsayilan: roleler aciktan LOW (donanimda zaten pull-down var,
  // burada yazilim tarafinda da ayni garantiyi acikca veriyoruz).
  pinMode(tulpar::PIN_KILIT_ROLE, OUTPUT);
  digitalWrite(tulpar::PIN_KILIT_ROLE, LOW);
  pinMode(tulpar::PIN_ELRS_ROLE, OUTPUT);
  digitalWrite(tulpar::PIN_ELRS_ROLE, LOW);

  // 1b) Fren/taret/lazer/ELRS - gaz kartinin (TCA9548A/mux) B3 guvenlik
  // sirasindan BAGIMSIZ, ayri pinler uzerinden calisir. Mux henuz takili
  // olmasa da (asagidaki adim 4'te setup() burada asilabilir) bu alt
  // sistemler baslatilabilsin diye TCA saglik kontrolunden ONCE baslatiliyor
  // - kasitli bir mimari karar, gaz kartinin B3 kuralinin kapsamini
  // genisletmiyor.
  fren.baslat();
  fren.serbestBirak();
  lazer.baslat();
  Serial1.begin(tulpar::ELRS_CRSF_BAUD);

  // 2) I2C baslat - PCF8591 400 kHz desteklemedigi icin 100 kHz'de sabit.
  Wire.begin();
  Wire.setClock(tulpar::I2C_HZ);

  // 3) Ilk I2C trafigi: 4 kanala da gaz=0 yaz (handoff B3, adim 2).
  surucu.tumGazlariSifirla();

  // 4) TCA9548A yanit vermiyorsa kilit LOW kalir, sonsuz dongude bekle -
  // WDT bir sure sonra tetiklenip setup()'i yeniden calistirir. NOT: bu
  // sadece gaz/surus zincirini durdurur - fren/taret/lazer/ELRS yukarida
  // zaten baslatildi, bu dongude de calismaya devam ederler (loop()'a
  // ulasilamadigi icin ELRS okuma/serial komut isleme dahil HERSEY durur -
  // bu bilinen bir sinirlama, bkz. README).
  if (!surucu.tcaSaglikliMi()) {
    Serial.println("HATA: TCA9548A (0x70) yanit vermiyor - kilit LOW kaliyor.");
    while (true) {
      delay(500);
    }
  }

  // 5) WDT'yi ac - reset sonrasi setup() yeniden calisip gazlari sifirlar.
  wdt.begin(tulpar::WDT_TIMEOUT_MS);

  // 6) Gazlar sifirlanip I2C saglikli dogrulandiktan SONRA kilit acilir
  // (handoff B3 kurali - acilis anindaki DAC-tanimsizligi motorlara ulasmasin).
  digitalWrite(tulpar::PIN_KILIT_ROLE, HIGH);

  Serial.println("tulpar_teensy hazir.");
}

// Serial komut arayuzu: "G<kanal 0-3> <deger 0-255>" - mux/DAC donanimi
// gelmeden once parse + I2C-yok hata yolunu izole test etmek, mux gelince
// de gercek etkiyle dogrulamak icin (/cmd_vel_safe -> Teensy koprusu
// gelene kadar gecici manuel test araci).
void islemGazKomutu(const String &satir) {
  int kanal = -1;
  int deger = -1;
  if (sscanf(satir.c_str(), "G%d %d", &kanal, &deger) != 2) {
    Serial.println("HATA: format 'G<kanal 0-3> <deger 0-255>' olmali, orn: G0 128");
    return;
  }
  if (kanal < 0 || kanal > 3) {
    Serial.println("HATA: kanal 0-3 araliginda olmali (0=on_sol,1=on_sag,2=arka_sol,3=arka_sag)");
    return;
  }
  if (deger < 0 || deger > 255) {
    Serial.println("HATA: deger 0-255 araliginda olmali");
    return;
  }
  if (!surucu.tcaSaglikliMi()) {
    Serial.println("HATA: TCA9548A (0x70) yanit vermiyor - komut uygulanamadi (donanim bagli degil)");
    return;
  }
  surucu.setGaz(static_cast<tulpar::Teker>(kanal), static_cast<uint8_t>(deger));
  Serial.print("OK: kanal ");
  Serial.print(kanal);
  Serial.print(" -> gaz ");
  Serial.println(deger);
}

// Fren komutu: "F<kanal 0-3> <oran 0.0-1.0>", orn: F0 0.5
void islemFrenKomutu(const String &satir) {
  int kanal = -1;
  float oran = -1.0f;
  if (sscanf(satir.c_str(), "F%d %f", &kanal, &oran) != 2) {
    Serial.println("HATA: format 'F<kanal 0-3> <oran 0.0-1.0>' olmali, orn: F0 0.5");
    return;
  }
  if (kanal < 0 || kanal > 3) {
    Serial.println("HATA: kanal 0-3 araliginda olmali");
    return;
  }
  fren.frenUygula(static_cast<tulpar::Teker>(kanal), oran);
  Serial.print("OK: fren kanal ");
  Serial.print(kanal);
  Serial.print(" -> oran ");
  Serial.println(oran);
}

// Taret komutu: "TP <derece>" (pan) veya "TT <derece>" (tilt), orn: TP 30
void islemTaretKomutu(const String &satir) {
  char eksen = 0;
  float derece = 0.0f;
  if (sscanf(satir.c_str(), "T%c %f", &eksen, &derece) != 2 || (eksen != 'P' && eksen != 'T')) {
    Serial.println("HATA: format 'TP <derece>' (pan) veya 'TT <derece>' (tilt) olmali, orn: TP 30");
    return;
  }
  bool kirpildi = (eksen == 'P') ? taret_pan.hedefeGit(derece) : taret_tilt.hedefeGit(derece);
  float sonuc = (eksen == 'P') ? taret_pan.mevcutDerece() : taret_tilt.mevcutDerece();
  Serial.print("OK: taret ");
  Serial.print(eksen == 'P' ? "PAN" : "TILT");
  Serial.print(" -> ");
  Serial.print(sonuc);
  Serial.println(kirpildi ? " derece (LIMITE KIRPILDI)" : " derece");
}

// Lazer komutu: "L1" (ac) / "L0" (kapat)
void islemLazerKomutu(const String &satir) {
  if (satir == "L1") {
    lazer.ac();
    Serial.println("OK: lazer ACIK");
  } else if (satir == "L0") {
    lazer.kapat();
    Serial.println("OK: lazer KAPALI");
  } else {
    Serial.println("HATA: format 'L1' (ac) veya 'L0' (kapat) olmali");
  }
}

void islemKomut(const String &satir) {
  if (satir.length() == 0) return;
  switch (satir[0]) {
    case 'G': islemGazKomutu(satir); break;
    case 'F': islemFrenKomutu(satir); break;
    case 'T': islemTaretKomutu(satir); break;
    case 'L': islemLazerKomutu(satir); break;
    default:
      Serial.println("HATA: bilinmeyen komut (G/F/T/L ile baslamali)");
  }
}

// ELRS/CRSF: Serial1'den gelen her byte parser'a beslenir, tam ve gecerli
// bir RC_CHANNELS_PACKED cercevesi olustugunda elrs_failsafe'e "paket geldi"
// bildirilir. Kanal verisi su an sadece parse ediliyor, gercek "manuel/
// otonom devralma" mantigi (hangi kanal/esik = manuel mod - Emin/elektronik
// ekiple netlesmeli) donanim geldiginde eklenecek.
void elrsOku() {
  while (Serial1.available() > 0) {
    crsf.byteIsle(static_cast<uint8_t>(Serial1.read()));
  }
  if (crsf.yeniCerceveVarMi()) {
    crsf.cerceveOkundu();
    elrs_failsafe.paketGeldi(millis());
  }
}

// Roadmap: "ELRS'den 400ms paket gelmezse -> 4 kanala DAC=0 + kilit rolesi
// LOW." Mantik yazildi ve test edildi (bkz. test/test_elrs_failsafe_katmani.cpp)
// AMA loop()'a BAGLANMADI - ELRS alicisi fiziksel olarak takili degilken bu
// kural "hic paket gelmedi = failsafe" oldugu icin surekli tetiklenir ve
// mevcut Serial "G<kanal>" bench-test aracini (ELRS'siz gaz karti testi
// icin var) tamamen kullanilamaz hale getirir. Gercek ELRS alicisi takilip
// "ELRS bagliyken failsafe aktif, degilken bench-test modu" ayrimi nasil
// yapilacagi netlesmeden (orn. ayri bir "ELRS_AKTIF" bayragi/komutu) otomatik
// zincire eklenmeyecek - bilincli olarak bagli DEGIL, kafadan karar verilmedi.
void elrsFailsafeKontrolEt() {
  if (elrs_failsafe.failsafeMi(millis())) {
    surucu.tumGazlariSifirla();
    digitalWrite(tulpar::PIN_KILIT_ROLE, LOW);
  }
}

void loop() {
  wdt.feed();
  elrsOku();
  // elrsFailsafeKontrolEt() KASITLI OLARAK CAGRILMIYOR - yukaridaki notu oku.

  static String satir;
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
    if (c == '\n') {
      satir.trim();
      if (satir.length() > 0) {
        islemKomut(satir);
      }
      satir = "";
    } else if (c != '\r') {
      satir += c;
    }
  }

  delay(10);
}
