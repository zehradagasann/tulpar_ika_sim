from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    default_xml_path = PathJoinSubstitution([
        FindPackageShare('tulpar_bt'), 'behavior_trees', 'ana_tree.xml',
    ])

    bt_xml_path_arg = DeclareLaunchArgument(
        'bt_xml_path',
        default_value=default_xml_path,
        description="ana_tree.xml yolu (varsayilan: tulpar_bt paketinin share dizini).",
    )

    bt_executor = Node(
        package='tulpar_bt',
        executable='bt_executor',
        name='tulpar_bt_executor',
        output='screen',
        parameters=[
            {'bt_xml_path': LaunchConfiguration('bt_xml_path')},
        ],
    )

    return LaunchDescription([bt_xml_path_arg, bt_executor])
