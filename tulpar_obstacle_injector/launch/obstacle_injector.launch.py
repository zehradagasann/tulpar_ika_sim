from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    cone_class_name_arg = DeclareLaunchArgument(
        'cone_class_name', default_value='traffic_cone',
        description="Detection2D.class_name icinde koni sinifinin adi.",
    )
    target_frame_arg = DeclareLaunchArgument(
        'target_frame', default_value='odom',
        description="Cikan PoseArray'in yayinlanacagi frame.",
    )

    obstacle_injector = Node(
        package='tulpar_obstacle_injector',
        executable='obstacle_injector',
        name='obstacle_injector',
        output='screen',
        parameters=[{
            'cone_class_name': LaunchConfiguration('cone_class_name'),
            'target_frame': LaunchConfiguration('target_frame'),
        }],
    )

    return LaunchDescription([
        cone_class_name_arg,
        target_frame_arg,
        obstacle_injector,
    ])
