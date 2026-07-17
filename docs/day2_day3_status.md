## Tamamlananlar
- D435if topic isimleri güncellendi.
- Gazebo bridge kamera/depth topicleri düzeltildi.
- RPi HQ camera, rear camera ve D435if isimleri netleştirildi.
- `sign_detected` ve `detections` topic yapısı netleşti.
- Slalom debug altyapısı yazıldı ve test edildi.
- Talha'dan slalom hedef topic'i ve koni işlenmiş çıktı formatı netleştirildi.

## Bende Eksik Olanlar
- Slalom algoritmasını gerçek koni sıralamasına göre güçlendirmek
- `/tulpar_bt/hedef_pose` üreten ROS 2 node'unu yazmak
- Ham detection -> `PoseArray(odom)` ara katmanını netleştirmek
- Gün 2 ve Gün 3 görev notlarını son hale getirmek

## Emin'den Beklenenler
- Model output formatı
- Confidence threshold önerisi
- Hangi kamera topic'ini dinleyeceği
- `stage_09` ve `atis_hedefi` mapping doğrulaması

## Talha'dan Beklenenler
- TEB obstacle hattı implementation sırası
- `odom` frame kullanan tüketici node'un son entegrasyon detayları
