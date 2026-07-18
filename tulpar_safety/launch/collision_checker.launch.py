from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    collision_checker = Node(
        package='tulpar_safety',
        executable='collision_checker',
        name='collision_checker',
        output='screen',
    )

    return LaunchDescription([collision_checker])
