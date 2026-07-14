#pragma once

#include <string>

#include "behaviortree_cpp/behavior_tree.h"
#include "nav2_msgs/action/navigate_to_pose.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

namespace tulpar_bt
{

// TAM IMPLEMENTE
// Nav2'nin otonom suruse geri donmeye hazir oldugunu (navigate_to_pose
// action server ayakta mi) dogrular. OtonomSurus'un goal'u yeniden
// gondermesi ReactiveFallback'in bir sonraki dongusunde kendiliginden
// olur - bu node sadece Nav2'nin hazir oldugunu teyit eden senkronizasyon
// noktasidir.
class DevamEt : public BT::StatefulActionNode
{
public:
  DevamEt(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts() {return {};}

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  using NavigateToPose = nav2_msgs::action::NavigateToPose;

  rclcpp::Node::SharedPtr node_;
  rclcpp_action::Client<NavigateToPose>::SharedPtr action_client_;
  rclcpp::Time start_time_;
};

}  // namespace tulpar_bt
