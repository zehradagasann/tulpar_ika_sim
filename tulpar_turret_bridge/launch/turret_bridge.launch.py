from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    seri_port_arg = DeclareLaunchArgument(
        'seri_port_adi', default_value='/dev/ttyACM0',
        description='Teensy USB seri port yolu.',
    )

    return LaunchDescription([
        seri_port_arg,
        Node(
            package='tulpar_turret_bridge',
            executable='turret_bridge',
            name='turret_bridge',
            output='screen',
            parameters=[{'seri_port_adi': LaunchConfiguration('seri_port_adi')}],
        ),
    ])
