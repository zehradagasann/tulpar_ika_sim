import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_path = get_package_share_directory("tulpar_description")
    xacro_file = os.path.join(pkg_path, "urdf", "robot.urdf.xacro")
    robot_desc = xacro.process_file(xacro_file).toxml()

    world_arg = DeclareLaunchArgument(
        'world',
        default_value='/home/talha/tulpar_ika_sim/worlds/s01_robotlu_world.sdf',
        description='Gazebo world SDF path'
    )
    world = LaunchConfiguration('world')

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

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            "/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model",
            "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
            "/camera/depth@sensor_msgs/msg/Image[gz.msgs.Image",
        ],
        output="screen"
    )

    return LaunchDescription([world_arg, robot_state_publisher, gazebo, bridge])
