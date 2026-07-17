#pragma once

#include <string>

#include "behaviortree_cpp/behavior_tree.h"
#include "rclcpp/rclcpp.hpp"
#include "tulpar_ika_msgs/msg/sign_detection_array.hpp"

namespace tulpar_bt
{

// YAZILIMSAL TAMAMLANDI - Emin'in goruntu isleme cikisi bekleniyor.
// Gercek ROS2 arayuzu: /sign_detected (tulpar_ika_msgs/SignDetectionArray)
// subscriber (16 Temmuz'da /tabela_tespit std_msgs/Bool placeholder'indan
// gercek sozlesmeye tasindi). Sadece ACTION_ENTER_SHOOTING_ZONE (stage_12
// tabelasi, class_registry.yaml) tasiyan tespit atis akisini tetikler.
// Test icin elle tetiklenebilir (tek satirda):
//   ros2 topic pub /sign_detected tulpar_ika_msgs/msg/SignDetectionArray "{detections: [{class_name: 'stage_12', action: 9}]}"
class TabelaAlgilandiMi : public BT::ConditionNode
{
public:
  TabelaAlgilandiMi(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts() {return {};}

  BT::NodeStatus tick() override;

private:
  void callback(const tulpar_ika_msgs::msg::SignDetectionArray::SharedPtr msg);

  rclcpp::Node::SharedPtr node_;
  rclcpp::Subscription<tulpar_ika_msgs::msg::SignDetectionArray>::SharedPtr sub_;
  bool detected_{false};
};

}  // namespace tulpar_bt
