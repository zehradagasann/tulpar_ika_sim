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
from launch.substitutions import LaunchConfiguration, PythonExpression, IfElseSubstitution
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
            get_package_share_directory('tulpar_description'), 'worlds', 'sim_world.sdf'
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

    # 18 Temmuz 2026: Nav2 dogrulama oturumunda gz sim GUI'nin (~3.2GB RSS)
    # sistem bellegini swap'a ittigi, bunun da RTAB-Map'in TF senkronunu
    # bozup /map'i hic yayinlatmadigi goruldu - GUI'siz calisma secenegi
    # eklendi: headless:=true ile "-s" bayragi eklenir (gz sim server-only).
    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='true ise Gazebo GUI acilmaz (gz sim -s), bellek baskisi altinda kullan.',
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
            "gz_args": [
                IfElseSubstitution(
                    LaunchConfiguration('headless'),
                    if_value="-r -s --render-engine ogre2 ",
                    else_value="-r --render-engine ogre2 ",
                ),
                world,
            ]
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
            "/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            "/d435if/depth/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/d435if/depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/d435if/depth/image_raw/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked",
            "/rear_camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/rear_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/rpi_hq_camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/rpi_hq_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/model/tulpar/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V",
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        remappings=[
            ("/model/tulpar/tf", "/tf"),
        ],
        output="screen"
    )

    # ÇÖZÜLDÜ (18 Temmuz 2026) — Gazebo'nun render-tabanli sensorleri (gpu_lidar,
    # depth_camera) LaserScan/Image/CameraInfo mesajlarinin frame_id'sine URDF'nin
    # gercek link ismini degil, kendi ic scoped-entity ismini (<model>/<kok_link>/
    # <sensor_adi>, orn. "tulpar/base_footprint/ydlidar_tg30") yaziyor - bu isim
    # robot_state_publisher'in yayinladigi TF agacinda hic yok, bu yuzden RTAB-Map
    # (ve muhtemelen tulpar_obstacle_injector) "frame does not exist" hatasi veriyor.
    # SDF'de bunu duzeltecek bir <frame_id> elemani yok (sadece kamera icin
    # optical_frame_id var, bu ham sensor frame'ini kapsamiyor) - statik (sifir
    # offsetli) TF alias'lariyla gercek URDF frame'lerine baglaniyor.
    sensor_frame_aliases = [
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=["0", "0", "0", "0", "0", "0", "lidar_link", "tulpar/base_footprint/ydlidar_tg30"],
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=["0", "0", "0", "0", "0", "0", "d435if_depth_optical_frame", "tulpar/base_footprint/d435if_depth"],
        ),
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=["0", "0", "0", "0", "0", "0", "rear_camera_optical_frame", "tulpar/base_footprint/rear_camera"],
        ),
    ]

    return LaunchDescription([
        gz_resource_path, world_arg, spawn_delay_arg, headless_arg,
        robot_state_publisher, gazebo, spawn_robot, bridge,
        *sensor_frame_aliases,
    ])
