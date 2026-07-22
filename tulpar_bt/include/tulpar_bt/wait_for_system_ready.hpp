#pragma once

#include <memory>
#include <string>
#include <vector>

#include "behaviortree_cpp/behavior_tree.h"
#include "lifecycle_msgs/msg/state.hpp"
#include "lifecycle_msgs/srv/get_state.hpp"
#include "rclcpp/rclcpp.hpp"

namespace tulpar_bt
{

// TAM IMPLEMENTE
// Verilen Nav2 lifecycle node'larinin (varsayilan: bt_navigator,
// controller_server, planner_server) hepsi ACTIVE state'e gecene kadar
// bekler. Her node icin "<ad>/get_state" servisini cagirir. timeout_sec
// asilirsa FAILURE doner.
class WaitForSystemReady : public BT::StatefulActionNode
{
public:
  WaitForSystemReady(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<std::string>(
        "node_names", "bt_navigator,controller_server,planner_server",
        "Kontrol edilecek lifecycle node adlari (virgulle ayrilmis)"),
      BT::InputPort<double>("timeout_sec", 30.0, "Maksimum bekleme suresi (sn)")
    };
  }

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  struct NodeCheck
  {
    std::string name;
    rclcpp::Client<lifecycle_msgs::srv::GetState>::SharedPtr client;
    rclcpp::Client<lifecycle_msgs::srv::GetState>::SharedFuture future;
    bool active{false};
  };

  rclcpp::Node::SharedPtr node_;
  std::vector<NodeCheck> checks_;
  rclcpp::Time start_time_;
  double timeout_sec_{30.0};
};

}  // namespace tulpar_bt
