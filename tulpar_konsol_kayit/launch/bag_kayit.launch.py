"""Her kosuyu ros2 bag ile kaydeder ("her kosu kayit altina alinir" - ileri
faz gereksinimi, 22 Temmuz 2026'da baslangic noktasi olarak eklendi).

Varsayilan konum ~/.tulpar_ika/bags/<zaman_damgasi> - olay_gunlugu.db'nin
ayni ~/.tulpar_ika/ altinda durmasiyla tutarli. Topic listesi, su an
onemli bilinen tum akislari kapsiyor (sensor/kontrol/algi/BT) - yeni bir
topic eklendiginde burasi da guncellenmeli, otomatik kesfetmiyor (ros2 bag
record -a tum topic'leri - /rosout dahil - kaydedip disk/performans
acisindan gereksiz yuk bindirebilir, bilerek kullanilmadi).
"""

import os
from datetime import datetime

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration

TOPICS = [
    '/odom', '/imu', '/scan', '/tf', '/joint_states',
    '/cmd_vel', '/cmd_vel_safe', '/cmd_vel_yon_duzeltmeli',
    '/cmd_vel_final', '/cmd_vel_guvenli',
    '/detections', '/sign_detected',
    '/parkur/koni_tespitleri', '/parkur/slalom_target',
    '/tulpar_bt/hedef_pose', '/parkur/hiz_seviyesi',
    '/tulpar_bt/atis_event', '/tulpar_kamera/atis_event',
    '/konsol/heartbeat', '/guvenlik/asiri_egim',
]


def generate_launch_description():
    varsayilan_dizin = os.path.join(
        os.path.expanduser('~'), '.tulpar_ika', 'bags',
        datetime.now().strftime('%Y%m%d_%H%M%S'),
    )

    bag_dizin_arg = DeclareLaunchArgument(
        'bag_dizin', default_value=varsayilan_dizin,
        description='ros2 bag kayit klasoru (var olmamali, ros2 bag olusturur).',
    )

    bag_kaydet = ExecuteProcess(
        cmd=['ros2', 'bag', 'record', '-o', LaunchConfiguration('bag_dizin'), *TOPICS],
        output='screen',
    )

    return LaunchDescription([bag_dizin_arg, bag_kaydet])
