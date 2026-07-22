cmake_minimum_required(VERSION 3.8)
project(tulpar_bt)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(nav2_behavior_tree REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(lifecycle_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(tulpar_ika_msgs REQUIRED)

include_directories(include)

set(TULPAR_BT_NODE_SOURCES
  src/wait_for_system_ready.cpp
  src/otonom_surus.cpp
  src/mod_degisimi_yap.cpp
  src/devam_et.cpp
  src/stop_noktasinda_mi.cpp
  src/dur_ve_bekle.cpp
  src/trigger_service_action_base.cpp
  src/tabela_algilandi_mi.cpp
)

add_library(tulpar_bt_nodes ${TULPAR_BT_NODE_SOURCES})
ament_target_dependencies(tulpar_bt_nodes
  rclcpp
  rclcpp_action
  behaviortree_cpp
  nav2_behavior_tree
  nav2_msgs
  lifecycle_msgs
  std_msgs
  std_srvs
  geometry_msgs
  nav_msgs
  tulpar_ika_msgs
)

add_executable(bt_executor src/bt_executor_main.cpp)
target_link_libraries(bt_executor tulpar_bt_nodes)
ament_target_dependencies(bt_executor
  rclcpp
  behaviortree_cpp
  ament_index_cpp
)

install(TARGETS
  bt_executor
  DESTINATION lib/${PROJECT_NAME}
)

# behavior_trees/ XML tek dogruluk kaynagi olarak ../behavior_trees'te kalir;
# build sirasinda tulpar_bt'nin kendi share dizinine kopyalanir.
install(
  DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../behavior_trees/
  DESTINATION share/${PROJECT_NAME}/behavior_trees
)

install(
  DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

ament_package()
