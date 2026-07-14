#pragma once

#include <future>
#include <string>

#include "behaviortree_cpp/behavior_tree.h"
#include "nav2_msgs/action/navigate_to_pose.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

namespace tulpar_bt
{

// TAM IMPLEMENTE
// Nav2'nin aktif NavigateToPose goal'unu gercekten iptal eder
// (action_client_->async_cancel_all_goals()). Nav2 zaten bos/goal
// yoksa ya da action server ayakta degilse de SUCCESS doner (iptal
// edilecek bir sey olmamasi bu node icin hata degildir).
class ModDegisimiYap : public BT::StatefulActionNode
{
public:
  ModDegisimiYap(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts() {return {};}

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  using NavigateToPose = nav2_msgs::action::NavigateToPose;
  using CancelResponse = rclcpp_action::Client<NavigateToPose>::CancelResponse;

  rclcpp::Node::SharedPtr node_;
  rclcpp_action::Client<NavigateToPose>::SharedPtr action_client_;
  std::shared_future<CancelResponse::SharedPtr> cancel_future_;
  rclcpp::Time start_time_;
  bool nothing_to_cancel_{false};
};

}  // namespace tulpar_bt
