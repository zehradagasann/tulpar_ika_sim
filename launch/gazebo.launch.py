import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    AppendEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_path = get_package_share_directory("tulpar_description")
    xacro_file = os.path.join(pkg_path, "urdf", "robot.urdf.xacro")
    robot_desc = xacro.process_file(xacro_file).toxml()

    # model:// URI'lerin (mesh vb.) cozulmesi icin gerekli - bu olmadan
    # Gazebo dunyayi yuklerken meshi bulamaz ve sunucu hemen coker.
    gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.dirname(pkg_path)
    )

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(
            get_package_share_directory('tulpar_description'), 'worlds', 's01_robotlu_world.sdf'
        ),
        description='Gazebo world SDF path'
    )
    world = LaunchConfiguration('world')

    spawn_delay_arg = DeclareLaunchArgument(
        'spawn_delay',
        default_value='5.0',
        description=(
            'Robotu spawn etmeden once Gazebo dunyasinin yuklenmesini bekleme suresi (sn). '
            'Gazebo Harmonic"te "dunya hazir" event"i olmadigi icin sabit gecikme kullaniliyor - '
            'yavas makinede yetmezse arttir: world:=... spawn_delay:=8.0'
        ),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_desc}],
        output="screen"
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("ros_gz_sim"),
                "launch", "gz_sim.launch.py"
            )
        ]),
        launch_arguments={
            "gz_args": ["-r --render-engine ogre ", world]
        }.items()
    )

    # Robotu worlds/*.sdf'ye gomulu statik model YERINE canli xacro'dan Gazebo'ya
    # spawn eder. /robot_description transient_local QoS ile yayinlandigi icin
    # robot_state_publisher'a gore baslama sirasi onemli degil; asil kisit Gazebo'nun
    # create servisinin hazir olmasi icin gereken sabit gecikme (yukaridaki nota bkz).
    # Entity adi "tulpar" sabit tutuluyor - bridge'in /model/tulpar/tf remap'i buna bagli.
    spawn_robot = TimerAction(
        period=LaunchConfiguration('spawn_delay'),
        actions=[
            Node(
                package="ros_gz_sim",
                executable="create",
                arguments=[
                    "-topic", "robot_description",
                    "-name", "tulpar",
                    "-x", "0", "-y", "0", "-z", "0.05",
                ],
                output="screen",
            )
        ]
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            "/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            "/d435if/depth/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/d435if/depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/d435if/depth/image_raw/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
            "/model/tulpar/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        remappings=[
            ("/model/tulpar/tf", "/tf"),
        ],
        output="screen"
    )

    return LaunchDescription([
        gz_resource_path, world_arg, spawn_delay_arg,
        robot_state_publisher, gazebo, spawn_robot, bridge,
    ])
