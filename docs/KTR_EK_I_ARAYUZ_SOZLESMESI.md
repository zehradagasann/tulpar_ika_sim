# TULPAR İKA — KTR Ek-I ROS 2 Arayüz Sözleşmesi

## Görüntü topikleri

| Topik | Mesaj tipi | Açıklama |
|---|---|---|
| /camera/front/color/image_raw | sensor_msgs/msg/Image | Ham ön kamera görüntüsü |
| /perception/front/image_preprocessed | sensor_msgs/msg/Image | Ön işlenmiş renkli görüntü |
| /perception/front/color_mask | sensor_msgs/msg/Image | HSV ikili renk maskesi |

## Algılama topikleri

| Topik | Mesaj tipi | Açıklama |
|---|---|---|
| /detections | tulpar_ika_msgs/msg/Detection2DArray | Genel nesne ve koni tespitleri |
| /sign_detected | tulpar_ika_msgs/msg/SignDetectionArray | Tabela tespitleri ve davranış kodları |

## Servisler

| Servis | Servis tipi | Açıklama |
|---|---|---|
| /perception/reset | tulpar_ika_srvs/srv/ResetPerception | Algılama durumunu sıfırlar |
| /perception/set_mode | tulpar_ika_srvs/srv/SetPerceptionMode | Aktif algılama modunu seçer |
| /perception/reload_config | tulpar_ika_srvs/srv/ReloadPerceptionConfig | Konfigürasyonu yeniden yükler |

## Birimler

- Görüntü koordinatları: piksel
- Mesafe: metre
- Açı: radyan
- Doğrusal hız: metre/saniye
- Açısal hız: radyan/saniye
- Güven değerleri: 0.0–1.0
