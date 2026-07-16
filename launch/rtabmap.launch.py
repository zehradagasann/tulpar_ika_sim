from launch import LaunchDescription
from launch_ros.actions import Node

# TAM İMPLEMENTE: RTAB-Map'i mevcut sensorlerle (YDLIDAR TG30 + RealSense
# D435if derinlik akisi) calisir hale getiren launch dosyasi.
#
# Kamera icin RGB sensoru olmadigindan (URDF'de sadece depth_camera var),
# gorsel ozellik tabanli RGB-D SLAM yerine lidar-oncelikli mod secildi:
# - Reg/Strategy=1 (ICP): kayit (registration) /scan'den, gorsel ozellik
#   gerektirmiyor.
# - Grid/FromDepth=false: occupancy grid sadece /scan'den uretiliyor.
# - Derinlik kamerasinin point cloud'u (/d435if/depth/image_raw/points,
#   gazebo.launch.py ile zaten bridge'leniyor) SLAM grafigine
#   karistirilmiyor; rviz'de ayri bir 3D katman olarak eklenip
#   gorsellestirilebilir.
#
# frame_id/odom_frame_id, gazebo.launch.py'deki DiffDrive plugin'inin
# (frame_id=odom, child_frame_id=base_footprint) ve URDF TF agacinin
# (base_footprint->base_link->lidar_link/d435i_link) birebir esidir.


def generate_launch_description():
    rtabmap_parameters = {
        "frame_id": "base_footprint",
        "odom_frame_id": "odom",
        "map_frame_id": "map",
        "subscribe_depth": False,
        "subscribe_rgb": False,
        "subscribe_scan": True,
        "approx_sync": True,
        "use_sim_time": True,
        "map_always_update": True,
        "Reg/Strategy": "1",
        "Grid/FromDepth": "false",
        "Grid/RangeMax": "20.0",
        "Icp/VoxelSize": "0.05",
        "Icp/MaxCorrespondenceDistance": "0.3",
        "RGBD/NeighborLinkRefining": "true",
    }

    rtabmap_remappings = [
        ("scan", "/scan"),
        ("odom", "/odom"),
    ]

    rtabmap_node = Node(
        package="rtabmap_slam",
        executable="rtabmap",
        output="screen",
        parameters=[rtabmap_parameters],
        remappings=rtabmap_remappings,
        arguments=["-d"],  # her testte temiz veritabani
    )

    return LaunchDescription([rtabmap_node])
