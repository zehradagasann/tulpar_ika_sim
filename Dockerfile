FROM osrf/ros:humble-desktop

# Gazebo ve temel araçları kuruyoruz
RUN apt-get update && apt-get install -y \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /workspace
