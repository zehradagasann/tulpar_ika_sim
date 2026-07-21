# /tulpar_kamera/atis_event -- Behaviour Tree'ye giden ayrik atis olayi.
# Her karede DEGIL, sadece durum degistiginde yayinlanir.
# transient_local QoS ile gec abone olan BT son durumu yine de alir.
#
# NOT (22 Tem): Topic ONCEDEN /tulpar_bt/atis_event idi. Talha'nin AtisYap
# BT node'u ayni isimde std_msgs/Header yayinliyordu (BT'nin kendi "atis
# yapildi" onayi) -- ayni topic adinda iki farkli mesaj tipi ROS2'de
# sessizce eslesmiyordu. Bu akis BT'ye GIREN bir algilama-durumu sinyali
# oldugu icin /tulpar_kamera/ altina tasindi; Talha'nin Header sinyali
# ve konsol kaydi degismedi.
#
# NOT: ACTION_ENTER_SHOOTING_ZONE=9, Zehra'nin SignDetection.msg
# konvansiyonuyla ayni deger. EXIT/LOST/LOCK Zehra listesinde yoktu,
# devami olarak 10-12 verildi -- Talha'nin BT enum'uyla TEYIT EDILECEK.

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
