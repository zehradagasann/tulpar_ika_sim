cmake_minimum_required(VERSION 3.8)
project(tulpar_ika_msgs)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Detection2D.msg"
  "msg/Detection2DArray.msg"
  "msg/SignDetection.msg"
  "msg/SignDetectionArray.msg"
  "msg/ConeDetection.msg"
  "msg/SlalomTarget.msg"
  "msg/AtisEvent.msg"
  "msg/TaretPid.msg"
  "msg/SpeedDecision.msg"
  "msg/TerrainSpeedDecision.msg"

  DEPENDENCIES
    std_msgs
    sensor_msgs
    geometry_msgs
)

ament_export_dependencies(rosidl_default_runtime)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
