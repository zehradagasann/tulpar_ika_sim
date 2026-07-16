import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_name = "tulpar_description"
    pkg_path = get_package_share_directory(package_name)
    pkg_share_parent = os.path.dirname(pkg_path)
    ros_gz_sim_path = get_package_share_directory("ros_gz_sim")

    xacro_file = os.path.join(pkg_path, "urdf", "robot.urdf.xacro")
    default_world = os.path.join(pkg_path, "worlds", "sim_world.sdf")

    robot_description = ParameterValue(Command(["xacro ", xacro_file]), value_type=str)
    world = LaunchConfiguration("world")

    current_resource_path = os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    resource_paths = [
        pkg_share_parent,
        pkg_path,
        os.path.join(pkg_path, "meshes"),
        os.path.join(pkg_path, "meshes", "parkur"),
    ]
    if current_resource_path:
        resource_paths.append(current_resource_path)

    declare_world = DeclareLaunchArgument(
        "world",
        default_value=default_world,
        description="Gazebo world file",
    )

    declare_headless = DeclareLaunchArgument(
        "headless",
        default_value="false",
        description="Run Gazebo server-only for Jetson or low-load usage",
    )

    set_gz_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=":".join(resource_paths),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{
            "robot_description": robot_description,
            "use_sim_time": True,
        }],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_path, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": ["-r ", world]}.items(),
        condition=UnlessCondition(LaunchConfiguration("headless")),
    )

    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_path, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": ["-r -s ", world]}.items(),
        condition=IfCondition(LaunchConfiguration("headless")),
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-name", "tulpar",
            "-topic", "robot_description",
            "-x", "-18.0",
            "-y", "0.0",
            "-z", "0.60",
        ],
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
        ],
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription([
        declare_world,
        declare_headless,
        set_gz_resource_path,
        robot_state_publisher,
        gazebo,
        gazebo_headless,
        spawn,
        bridge,
    ])
