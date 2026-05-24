import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    package_name = "tulpar_description"
    pkg_path = get_package_share_directory(package_name)
    xacro_file = os.path.join(pkg_path, "urdf", "robot.urdf.xacro")
    robot_desc = xacro.process_file(xacro_file).toxml()

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
       launch_arguments={"gz_args": "-r --render-engine ogre empty.sdf"}.items()
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "tulpar",
            "-topic", "robot_description",
            "-x", "0", "-y", "0", "-z", "1.0"
        ],
        output="screen"
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry",
        ],
        output="screen"
    )

    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        spawn,
        bridge
    ])
