import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# TAM İMPLEMENTE: Nav2'yi (MPPI local planner, NavFn global planner,
# global+local costmap, bt_navigator, velocity_smoother, lifecycle_manager)
# ayaga kaldiran, gazebo.launch.py ve rtabmap.launch.py'den TAMAMEN AYRI
# calisan launch dosyasi (rtabmap.launch.py ile ayni desen).
#
# Bilerek nav2_bringup paketinin kendi launch dosyasi INCLUDE EDILMIYOR -
# o map_server/AMCL de getirir, biz istemiyoruz: harita RTAB-Map'ten canli
# geliyor (launch/rtabmap.launch.py, /map topic'i), statik harita dosyasi yok.
#
# Calistirma sirasi (3 ayri terminal):
#   ros2 launch tulpar_description gazebo.launch.py
#   ros2 launch tulpar_description rtabmap.launch.py
#   ros2 launch tulpar_description nav2_bringup.launch.py
#
# lifecycle_manager'in yonettigi node isimleri
# (controller_server, planner_server, bt_navigator, ...) tulpar_bt'nin
# WaitForSystemReady node'unun varsayilan olarak bekledigi isimlerle
# (bt_navigator,controller_server,planner_server) birebir eslesir -
# bkz. tulpar_bt/include/tulpar_bt/wait_for_system_ready.hpp.


def generate_launch_description():
    pkg_path = get_package_share_directory("tulpar_description")

    params_file_arg = DeclareLaunchArgument(
        "params_file",
        default_value=os.path.join(pkg_path, "config", "nav2_params.yaml"),
        description="Nav2 parametre dosyasi (config/nav2_params.yaml)",
    )
    params_file = LaunchConfiguration("params_file")

    lifecycle_nodes = [
        "controller_server",
        "planner_server",
        "behavior_server",
        "bt_navigator",
        "velocity_smoother",
    ]

    controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        output="screen",
        parameters=[params_file],
    )

    planner_server = Node(
        package="nav2_planner",
        executable="planner_server",
        output="screen",
        parameters=[params_file],
    )

    behavior_server = Node(
        package="nav2_behaviors",
        executable="behavior_server",
        output="screen",
        parameters=[params_file],
    )

    bt_navigator = Node(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        output="screen",
        parameters=[params_file],
    )

    velocity_smoother = Node(
        package="nav2_velocity_smoother",
        executable="velocity_smoother",
        output="screen",
        parameters=[params_file],
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        output="screen",
        parameters=[
            params_file,
            {"node_names": lifecycle_nodes, "autostart": True, "use_sim_time": True},
        ],
    )

    return LaunchDescription(
        [
            params_file_arg,
            controller_server,
            planner_server,
            behavior_server,
            bt_navigator,
            velocity_smoother,
            lifecycle_manager,
        ]
    )
