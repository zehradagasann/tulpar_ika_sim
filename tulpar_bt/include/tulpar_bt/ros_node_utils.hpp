#pragma once

#include "behaviortree_cpp/behavior_tree.h"
#include "rclcpp/rclcpp.hpp"

namespace tulpar_bt
{

// Tum custom BT node'lari, executor'un blackboard'a koydugu rclcpp::Node'u
// bu anahtarla okur (nav2_behavior_tree::BtActionNode'un kullandigi ayni
// kural).
inline rclcpp::Node::SharedPtr getRosNode(const BT::NodeConfig & config)
{
  return config.blackboard->get<rclcpp::Node::SharedPtr>("node");
}

}  // namespace tulpar_bt
