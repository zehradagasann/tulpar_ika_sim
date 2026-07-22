#include "tulpar_bt/mod_degisimi_yap.hpp"

#include "tulpar_bt/ros_node_utils.hpp"

namespace tulpar_bt
{

ModDegisimiYap::ModDegisimiYap(const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = getRosNode(config);
  action_client_ = rclcpp_action::create_client<NavigateToPose>(node_, "navigate_to_pose");
}

BT::NodeStatus ModDegisimiYap::onStart()
{
  nothing_to_cancel_ = false;
  start_time_ = node_->now();

  if (!action_client_->action_server_is_ready()) {
    RCLCPP_WARN(
      node_->get_logger(),
      "ModDegisimiYap: navigate_to_pose action server ayakta degil, iptal edilecek bir sey yok");
    nothing_to_cancel_ = true;
    return BT::NodeStatus::RUNNING;
  }

  RCLCPP_INFO(node_->get_logger(), "ModDegisimiYap: Nav2 goal'lari iptal ediliyor");
  cancel_future_ = action_client_->async_cancel_all_goals();
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus ModDegisimiYap::onRunning()
{
  if (nothing_to_cancel_) {
    return BT::NodeStatus::SUCCESS;
  }

  if (cancel_future_.wait_for(std::chrono::seconds(0)) == std::future_status::ready) {
    RCLCPP_INFO(node_->get_logger(), "ModDegisimiYap: Nav2 goal iptali onaylandi");
    return BT::NodeStatus::SUCCESS;
  }

  double elapsed = (node_->now() - start_time_).seconds();
  if (elapsed > 2.0) {
    RCLCPP_ERROR(node_->get_logger(), "ModDegisimiYap: iptal onayi zaman asimina ugradi");
    return BT::NodeStatus::FAILURE;
  }

  return BT::NodeStatus::RUNNING;
}

void ModDegisimiYap::onHalted()
{
}

}  // namespace tulpar_bt
