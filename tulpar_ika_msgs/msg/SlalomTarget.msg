# Zehra'nin slalom_core.py (run_slalom_logic()) ciktisinin ROS2 sozlesmesi
# (18 Temmuz 2026 - Talha/Zehra arasinda konusulan waypoint yaklasiminin
# taslak sozlesmesi, Zehra kendi node'unu yazarken degistirebilir).
#
# header.frame_id: hedef pikselin hesaplandigi kamera optik frame'i
# (orn. d435if_color_optical_frame) - slalom_hedef_bridge bunu derinlik
# goruntusu + TF ile odom'a cevirir.
#
# UYARI (19 Temmuz 2026): slalom_hedef_bridge derinligi target_x_px/y_px
# konumundan DOGRUDAN /d435if/depth/image_raw uzerinden ornekliyor - yani bu
# piksel koordinatlarinin DERINLIK goruntusuyle AYNI cozunurluk/FOV'da
# hesaplanmis olmasi gerekiyor. Ornekteki d435if_color_optical_frame RGB
# frame'i - RGB ve derinlik goruntuleri farkli cozunurlukte/FOV'da ise (gercek
# D435if'te tipik durum budur) piksel koordinatlari source_width/height ile
# birlikte bildirilmeli, bridge bunlari derinlik goruntusunun boyutuna oranla
# olcekliyor (bkz. slalom_hedef_bridge_node.py). Zehra kendi node'unu
# yazarken source_width/height'i KENDI ciktisini urettigi goruntunun gercek
# cozunurlugune esitlemeli - yoksa hedef nokta sessizce yanlis hesaplanir.

std_msgs/Header header

# Piksel koordinatinda hedef nokta (3D/odom pose DEGIL)
float32 target_x_px
float32 target_y_px

# target_x_px/y_px'in hesaplandigi goruntunun cozunurlugu (piksel). Derinlik
# goruntusuyle (camera_info) farkliysa bridge oransal olcekleme yapar.
uint32 source_width
uint32 source_height

# left / right / straight / unknown
string turn_direction

# fast / medium / slow / stop
string speed_level
