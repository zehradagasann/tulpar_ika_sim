## Amaç
  Koni çiftlerinden geçiş için orta hedef nokta üretmek.

  ## Girdi
  - Sol koniler
  - Sağ koniler
  - Her koni için görüntü merkezi veya 2D konum bilgisi

  ## Adımlar
  1. Konileri sol ve sağ diye ayır
  2. Yakın sol-sağ konileri eşleştir
  3. Her eşleşme için orta nokta hesapla
  4. En uygun orta noktayı hedef seç
  5. Hedefe göre yön bilgisi üret
  6. Hedef uzaklığına göre hız seviyesi üret

  ## Geçici Çıkışlar
  - target_point_x
  - target_point_y
  - turn_direction
  - speed_level

  ## Açık Konular
  - Navigation tarafı obstacle mı waypoint mi corridor mu bekliyor?
  - ROS mesajı hangi formatta olacak?
