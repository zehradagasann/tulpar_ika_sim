# Slalom Algorithm Notes

## Amaç
Koni çiftlerinden geçiş için orta hedef nokta üretmek.

## Girdi
- Ham koni algısı: `/detections` (`Detection2DArray`)
- Her koni için görüntü merkezi (`center_px`) ve varsa `depth_m`

## İş Akışı
1. Ham koni algısını al
2. Derinlik ve TF ile konileri `odom` frame'ine taşı
3. İşlenmiş koni merkezlerini `/parkur/koni_tespitleri` (`PoseArray`) olarak üret
4. Sol-sağ koni çiftlerinden orta hedef noktayı hesapla
5. Slalom hedefini `/tulpar_bt/hedef_pose` (`PoseStamped`) olarak yayınla

## Kararlaştırılan Format
- Koni işlenmiş çıkışı:
  - topic: `/parkur/koni_tespitleri`
  - mesaj: `geometry_msgs/msg/PoseArray`
  - frame: `odom`
- Slalom hedef çıkışı:
  - topic: `/tulpar_bt/hedef_pose`
  - mesaj: `geometry_msgs/msg/PoseStamped`

## Notlar
- `turn_direction` ayrı topic olarak taşınmayacak.
- `speed_level` şimdilik taşınmayacak.
- Ham detection ile navigation çıktısı ayrı tutulacak.
- TEB/costmap obstacle hattı Talha tarafında ayrı görev olarak ilerleyecek.
