#pragma once

#include <string>

#include "behaviortree_cpp/behavior_tree.h"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/bool.hpp"

namespace tulpar_bt
{

// YAZILIMSAL TAMAMLANDI - Emin'in goruntu isleme cikisi bekleniyor.
// Gercek ROS2 arayuzu: /tabela_tespit (std_msgs/Bool) subscriber. Henuz
// kimse yayin yapmasa da dogru calisir; test icin elle tetiklenebilir:
//   ros2 topic pub /tabela_tespit std_msgs/msg/Bool "{data: true}"
class TabelaAlgilandiMi : public BT::ConditionNode
{
public:
  TabelaAlgilandiMi(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts() {return {};}

  BT::NodeStatus tick() override;

private:
  void callback(const std_msgs::msg::Bool::SharedPtr msg);

  rclcpp::Node::SharedPtr node_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr sub_;
  bool detected_{false};
};

}  // namespace tulpar_bt
