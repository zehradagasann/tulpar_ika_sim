#include "tulpar_bt/tabela_algilandi_mi.hpp"

#include <algorithm>

#include "tulpar_bt/ros_node_utils.hpp"

namespace tulpar_bt
{

TabelaAlgilandiMi::TabelaAlgilandiMi(const std::string & name, const BT::NodeConfig & config)
: BT::ConditionNode(name, config)
{
  node_ = getRosNode(config);
  sub_ = node_->create_subscription<tulpar_ika_msgs::msg::SignDetectionArray>(
    "/sign_detected", rclcpp::QoS(10),
    std::bind(&TabelaAlgilandiMi::callback, this, std::placeholders::_1));
}

void TabelaAlgilandiMi::callback(const tulpar_ika_msgs::msg::SignDetectionArray::SharedPtr msg)
{
  // 17 Temmuz 2026: ACTION_ENTER_SHOOTING_ZONE=9 eklendi (stage_12 tabelasi,
  // class_registry.yaml). Atis akisi artik sadece bu tabela gorulunce
  // tetikleniyor - STOP/SPEED_LIMIT/vb. diger tabelalar bu koşulu tetiklemez.
  detected_ = std::any_of(
    msg->detections.begin(), msg->detections.end(),
    [](const auto & det) {
      return det.action == tulpar_ika_msgs::msg::SignDetection::ACTION_ENTER_SHOOTING_ZONE;
    });
}

BT::NodeStatus TabelaAlgilandiMi::tick()
{
  return detected_ ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
}

}  // namespace tulpar_bt
