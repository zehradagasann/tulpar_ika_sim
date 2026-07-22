#pragma once

#include <string>

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "nav2_behavior_tree/bt_action_node.hpp"
#include "nav2_msgs/action/navigate_to_pose.hpp"
#include "rclcpp/rclcpp.hpp"

namespace tulpar_bt
{

// TAM IMPLEMENTE
// Nav2 NavigateToPose action client'i (nav2_behavior_tree::BtActionNode
// tabanli, gercek action goal gonderimi/iptali/halt semantigi Nav2'nin
// kendi altyapisindan gelir). Hedef pose /tulpar_bt/hedef_pose topic'inden
// alinir; henuz pose gelmediyse FAILURE doner (log ile aciklanir).
class OtonomSurus : public nav2_behavior_tree::BtActionNode<nav2_msgs::action::NavigateToPose>
{
public:
  OtonomSurus(const std::string & xml_tag_name, const BT::NodeConfig & conf);

  static BT::PortsList providedPorts()
  {
    return providedBasicPorts({});
  }

  void on_tick() override;

private:
  void goalPoseCallback(const geometry_msgs::msg::PoseStamped::SharedPtr msg);

  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr goal_pose_sub_;
  geometry_msgs::msg::PoseStamped latest_goal_pose_;
  bool has_goal_pose_{false};
};

}  // namespace tulpar_bt
