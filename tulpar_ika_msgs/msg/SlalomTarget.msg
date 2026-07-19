# Zehra'nin slalom_core.py (run_slalom_logic()) ciktisinin ROS2 sozlesmesi
# (18 Temmuz 2026 - Talha/Zehra arasinda konusulan waypoint yaklasiminin
# taslak sozlesmesi, Zehra kendi node'unu yazarken degistirebilir).
#
# header.frame_id: hedef pikselin hesaplandigi kamera optik frame'i
# (orn. d435if_color_optical_frame) - slalom_hedef_bridge bunu derinlik
# goruntusu + TF ile odom'a cevirir.

std_msgs/Header header

# Piksel koordinatinda hedef nokta (3D/odom pose DEGIL)
float32 target_x_px
float32 target_y_px

# left / right / straight / unknown
string turn_direction

# fast / medium / slow / stop
string speed_level
