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
    use_sim_time = LaunchConfiguration("use_sim_time")
    spawn_x = LaunchConfiguration("spawn_x")
    spawn_y = LaunchConfiguration("spawn_y")
    spawn_z = LaunchConfiguration("spawn_z")
    spawn_yaw = LaunchConfiguration("spawn_yaw")

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

    declare_use_sim_time = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use Gazebo simulation clock",
    )

    declare_headless = DeclareLaunchArgument(
        "headless",
        default_value="false",
        description="Run Gazebo server-only for Jetson or low-load usage",
    )

    declare_spawn_x = DeclareLaunchArgument(
        "spawn_x",
        default_value="-18.0",
        description="Robot spawn X coordinate",
    )

    declare_spawn_y = DeclareLaunchArgument(
        "spawn_y",
        default_value="0.0",
        description="Robot spawn Y coordinate",
    )

    declare_spawn_z = DeclareLaunchArgument(
        "spawn_z",
        default_value="0.60",
        description="Robot spawn Z coordinate",
    )

    declare_spawn_yaw = DeclareLaunchArgument(
        "spawn_yaw",
        default_value="0.0",
        description="Robot spawn yaw in radians",
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
            "use_sim_time": use_sim_time,
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
            "-x", spawn_x,
            "-y", spawn_y,
            "-z", spawn_z,
            "-Y", spawn_yaw,
        ],
    )

    # Yaris senaryosu icin tum kameralar, derinlik ve lidar ayni anda bridge edilir.
    # Derinlik kamerasi ana perception zincirine kaynak olacagi icin image, camera_info
    # ve point cloud akislari birlikte acilir.
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            "/scan/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
            "/d435if/depth/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/d435if/depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/d435if/depth/image_raw/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
            "/rear_camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/rear_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/rpi_hq_camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/rpi_hq_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
        ],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    return LaunchDescription([
        declare_world,
        declare_use_sim_time,
        declare_headless,
        declare_spawn_x,
        declare_spawn_y,
        declare_spawn_z,
        declare_spawn_yaw,
        set_gz_resource_path,
        robot_state_publisher,
        gazebo,
        gazebo_headless,
        spawn,
        bridge,
    ])
