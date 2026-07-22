#pragma once

#include <string>
#include <vector>

#include "behaviortree_cpp/behavior_tree.h"
#include "nav_msgs/msg/odometry.hpp"
#include "rclcpp/rclcpp.hpp"

namespace tulpar_bt
{

// TAM IMPLEMENTE
// /odom'dan gelen gercek pozisyonu, sartname madde 6.10'daki rampa stop
// noktalariyla karsilastirir. Her nokta en fazla bir kez tetiklenir
// (StopPoint::consumed) - aksi halde arac stop noktasinda dururken bir
// sonraki Repeat dongusunde ayni nokta tekrar tetiklenip sonsuz beklemeye
// girerdi.
class StopNoktasindaMi : public BT::ConditionNode
{
public:
  StopNoktasindaMi(const std::string & name, const BT::NodeConfig & config);

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<std::string>(
        "stop_points", "",
        "Rampadaki stop noktalari \"x1,y1;x2,y2;...\" formatinda. "
        "Bos ise 'stop_noktalari' ROS parametresi kullanilir."),
      BT::InputPort<double>("tolerance", 0.5, "Stop noktasina varildi sayilacak yaricap (m)")
    };
  }

  BT::NodeStatus tick() override;

private:
  struct StopPoint
  {
    double x;
    double y;
    bool consumed{false};
  };

  static std::vector<StopPoint> parseStopPoints(const std::string & s);
  void odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg);

  rclcpp::Node::SharedPtr node_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  nav_msgs::msg::Odometry latest_odom_;
  bool has_odom_{false};
  std::vector<StopPoint> stop_points_;
  double tolerance_{0.5};
};

}  // namespace tulpar_bt
