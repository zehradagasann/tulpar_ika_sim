cmake_minimum_required(VERSION 3.8)
project(tulpar_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY meshes urdf launch worlds resource
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
