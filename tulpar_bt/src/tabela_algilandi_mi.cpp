#include "tulpar_bt/tabela_algilandi_mi.hpp"

#include "tulpar_bt/ros_node_utils.hpp"

namespace tulpar_bt
{

TabelaAlgilandiMi::TabelaAlgilandiMi(const std::string & name, const BT::NodeConfig & config)
: BT::ConditionNode(name, config)
{
  node_ = getRosNode(config);
  sub_ = node_->create_subscription<std_msgs::msg::Bool>(
    "/tabela_tespit", rclcpp::QoS(10),
    std::bind(&TabelaAlgilandiMi::callback, this, std::placeholders::_1));
}

void TabelaAlgilandiMi::callback(const std_msgs::msg::Bool::SharedPtr msg)
{
  detected_ = msg->data;
}

BT::NodeStatus TabelaAlgilandiMi::tick()
{
  return detected_ ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
}

}  // namespace tulpar_bt
