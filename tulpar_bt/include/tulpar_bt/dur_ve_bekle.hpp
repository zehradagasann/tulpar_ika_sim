#pragma once

#include <string>

#include "behaviortree_cpp/behavior_tree.h"
#include "geometry_msgs/msg/twist.hpp"
#include "rclcpp/rclcpp.hpp"

namespace tulpar_bt
{

// TAM IMPLEMENTE
// Sartname madde 6.10: araci gercekten durdurur (sifir Twist /cmd_vel'e
// basilir, bekleme boyunca tekrar tekrar basilmaya devam edilir) ve
// gercek wall-clock sureyle en az bekleme_sn (varsayilan 2.0s) bekler.
class DurVeBekle : public BT::StatefulActionNode
{
public:
  DurVeBekle(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<double>("bekleme_sn", 2.0, "Bekleme suresi (sn)")
    };
  }

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

private:
  rclcpp::Node::SharedPtr node_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
  rclcpp::Time start_time_;
  double bekleme_sn_{2.0};
};

}  // namespace tulpar_bt
