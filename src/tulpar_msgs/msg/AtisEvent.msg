# /tulpar_bt/atis_event -- Behaviour Tree'ye giden ayrik olay.
# Her karede DEGIL, sadece durum degistiginde yayinlanir.
# transient_local QoS ile gec abone olan BT son durumu yine de alir.

std_msgs/Header header

uint8 ACTION_NONE=0
uint8 ACTION_ENTER_SHOOTING_ZONE=1
uint8 ACTION_EXIT_SHOOTING_ZONE=2
uint8 ACTION_TARGET_LOST=3
uint8 ACTION_LOCK_STABLE=4          # hedef N kare boyunca bolgede kaldi

uint8   action
uint32  track_id
uint16  class_id
string  class_name
float32 confidence
float32 dwell_seconds
