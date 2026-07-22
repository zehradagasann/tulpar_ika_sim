# /tulpar_kamera/atis_event -- kamera/algi tarafinin hedef-durumu olayi
# (Emin'in kamera_node'u yayinlar). BT'nin kendi "atis yaptim" sinyaliyle
# (/tulpar_bt/atis_event, std_msgs/Header, AtisYap SUCCESS) KARISTIRILMASIN
# - ikisi farkli olay/farkli topic, bkz. CLAUDE.md "AtisEvent" notu.
# Her karede DEGIL, sadece durum degistiginde yayinlanir.
# transient_local QoS ile gec abone olan BT son durumu yine de alir.
#
# ACTION_ENTER_SHOOTING_ZONE=9, SignDetection.msg konvansiyonuyla ayni deger
# (22 Temmuz 2026, Talha tarafindan tulpar_bt kodunda cakisma olmadigi
# teyit edildi). EXIT/LOST/LOCK_STABLE (10-12) yeni degerler, hicbir yerle
# cakismiyor.

std_msgs/Header header

uint8 ACTION_NONE=0
uint8 ACTION_ENTER_SHOOTING_ZONE=9
uint8 ACTION_EXIT_SHOOTING_ZONE=10
uint8 ACTION_TARGET_LOST=11
uint8 ACTION_LOCK_STABLE=12

uint8   action
uint32  track_id
uint16  class_id
string  class_name
float32 confidence
float32 dwell_seconds
