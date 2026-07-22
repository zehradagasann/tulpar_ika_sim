#include "tulpar_bt/otonom_surus.hpp"

namespace tulpar_bt
{

OtonomSurus::OtonomSurus(const std::string & xml_tag_name, const BT::NodeConfig & conf)
: nav2_behavior_tree::BtActionNode<nav2_msgs::action::NavigateToPose>(
    xml_tag_name, "navigate_to_pose", conf)
{
  goal_pose_sub_ = node_->create_subscription<geometry_msgs::msg::PoseStamped>(
    "/tulpar_bt/hedef_pose", rclcpp::QoS(10),
    std::bind(&OtonomSurus::goalPoseCallback, this, std::placeholders::_1));
}

void OtonomSurus::goalPoseCallback(const geometry_msgs::msg::PoseStamped::SharedPtr msg)
{
  latest_goal_pose_ = *msg;
  has_goal_pose_ = true;
}

void OtonomSurus::on_tick()
{
  if (!has_goal_pose_) {
    RCLCPP_WARN(
      node_->get_logger(),
      "OtonomSurus: henuz /tulpar_bt/hedef_pose alinmadi, goal gonderilemiyor");
    should_send_goal_ = false;
    return;
  }

  goal_.pose = latest_goal_pose_;
  RCLCPP_INFO(
    node_->get_logger(),
    "OtonomSurus: NavigateToPose goal gonderiliyor (%.2f, %.2f)",
    goal_.pose.pose.position.x, goal_.pose.pose.position.y);
}

}  // namespace tulpar_bt
