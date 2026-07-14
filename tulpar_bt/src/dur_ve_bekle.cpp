#include "tulpar_bt/dur_ve_bekle.hpp"

#include "tulpar_bt/ros_node_utils.hpp"

namespace tulpar_bt
{

DurVeBekle::DurVeBekle(const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = getRosNode(config);
  cmd_vel_pub_ = node_->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", rclcpp::QoS(10));
}

BT::NodeStatus DurVeBekle::onStart()
{
  getInput("bekleme_sn", bekleme_sn_);
  cmd_vel_pub_->publish(geometry_msgs::msg::Twist());
  start_time_ = node_->now();
  RCLCPP_INFO(node_->get_logger(), "DurVeBekle: durduruldu, %.1f sn bekleniyor", bekleme_sn_);
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus DurVeBekle::onRunning()
{
  cmd_vel_pub_->publish(geometry_msgs::msg::Twist());

  const double elapsed = (node_->now() - start_time_).seconds();
  if (elapsed >= bekleme_sn_) {
    RCLCPP_INFO(node_->get_logger(), "DurVeBekle: bekleme tamamlandi, devam ediliyor");
    return BT::NodeStatus::SUCCESS;
  }
  return BT::NodeStatus::RUNNING;
}

void DurVeBekle::onHalted()
{
}

}  // namespace tulpar_bt
