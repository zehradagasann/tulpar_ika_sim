# /tulpar_kamera/taret_pid -- Emin'in kamera_node.py'sindeki mevcut PID
# (pid_pan/pid_tilt, hedef pikseli hatasindan hesaplaniyor) ciktisinin taslak
# sozlesmesi (22 Temmuz 2026, Talha - turret bridge icin). Emin'in PID/YOLO
# mantigina dokunmuyor, sadece zaten hesapladigi degerleri disari veriyor.
#
# pan_derece/tilt_derece MUTLAK aci DEGIL - bu tick'te taret'in mevcut
# acisina EKLENECEK delta (PID.update()'in kendi ciktisi, dt ile olceklenmis
# zaten). Mutlak aciya cevirme (birikimli toplama + ±90° kirpma) turret
# bridge'in sorumlulugunda, Emin'in kodunda hicbir birikim yok.

std_msgs/Header header

bool  hedef_var       # find_shooting_target() None donduyse false - bridge
                       # bu durumda acida DEGISIKLIK YAPMAMALI (PID zaten
                       # Emin tarafinda resetleniyor, delta anlamsiz olur)
float32 pan_derece
float32 tilt_derece
float32 confidence
