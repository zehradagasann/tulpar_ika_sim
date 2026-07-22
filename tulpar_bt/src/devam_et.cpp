#include "tulpar_bt/devam_et.hpp"

#include "tulpar_bt/ros_node_utils.hpp"

namespace tulpar_bt
{

DevamEt::DevamEt(const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = getRosNode(config);
  action_client_ = rclcpp_action::create_client<NavigateToPose>(node_, "navigate_to_pose");
}

BT::NodeStatus DevamEt::onStart()
{
  start_time_ = node_->now();
  if (action_client_->action_server_is_ready()) {
    RCLCPP_INFO(node_->get_logger(), "DevamEt: Nav2 hazir, otonom suruse devam ediliyor");
    return BT::NodeStatus::SUCCESS;
  }
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus DevamEt::onRunning()
{
  if (action_client_->action_server_is_ready()) {
    RCLCPP_INFO(node_->get_logger(), "DevamEt: Nav2 hazir, otonom suruse devam ediliyor");
    return BT::NodeStatus::SUCCESS;
  }

  double elapsed = (node_->now() - start_time_).seconds();
  if (elapsed > 5.0) {
    RCLCPP_ERROR(node_->get_logger(), "DevamEt: Nav2 action server 5s icinde hazir olmadi");
    return BT::NodeStatus::FAILURE;
  }

  return BT::NodeStatus::RUNNING;
}

void DevamEt::onHalted()
{
}

}  // namespace tulpar_bt
