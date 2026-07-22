#include "tulpar_bt/stop_noktasinda_mi.hpp"

#include <cmath>
#include <sstream>

#include "tulpar_bt/ros_node_utils.hpp"

namespace tulpar_bt
{

StopNoktasindaMi::StopNoktasindaMi(const std::string & name, const BT::NodeConfig & config)
: BT::ConditionNode(name, config)
{
  node_ = getRosNode(config);

  std::string stop_points_str;
  getInput("stop_points", stop_points_str);
  if (stop_points_str.empty()) {
    if (!node_->has_parameter("stop_noktalari")) {
      node_->declare_parameter<std::string>("stop_noktalari", "");
    }
    stop_points_str = node_->get_parameter("stop_noktalari").as_string();
  }
  getInput("tolerance", tolerance_);

  stop_points_ = parseStopPoints(stop_points_str);
  RCLCPP_INFO(
    node_->get_logger(), "StopNoktasindaMi: %zu stop noktasi yuklendi (tolerance=%.2fm)",
    stop_points_.size(), tolerance_);

  odom_sub_ = node_->create_subscription<nav_msgs::msg::Odometry>(
    "/odom", rclcpp::QoS(10),
    std::bind(&StopNoktasindaMi::odomCallback, this, std::placeholders::_1));
}

std::vector<StopNoktasindaMi::StopPoint> StopNoktasindaMi::parseStopPoints(const std::string & s)
{
  std::vector<StopPoint> points;
  std::stringstream ss(s);
  std::string pair_str;
  while (std::getline(ss, pair_str, ';')) {
    if (pair_str.empty()) {
      continue;
    }
    std::stringstream ps(pair_str);
    std::string x_str, y_str;
    if (std::getline(ps, x_str, ',') && std::getline(ps, y_str, ',')) {
      try {
        points.push_back({std::stod(x_str), std::stod(y_str), false});
      } catch (const std::exception &) {
        // gecersiz format, bu noktayi atla
      }
    }
  }
  return points;
}

void StopNoktasindaMi::odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
  latest_odom_ = *msg;
  has_odom_ = true;
}

BT::NodeStatus StopNoktasindaMi::tick()
{
  if (!has_odom_ || stop_points_.empty()) {
    return BT::NodeStatus::FAILURE;
  }

  const double x = latest_odom_.pose.pose.position.x;
  const double y = latest_odom_.pose.pose.position.y;

  for (auto & p : stop_points_) {
    if (p.consumed) {
      continue;
    }
    const double dx = x - p.x;
    const double dy = y - p.y;
    const double dist = std::sqrt(dx * dx + dy * dy);
    if (dist <= tolerance_) {
      p.consumed = true;
      RCLCPP_INFO(
        node_->get_logger(), "StopNoktasindaMi: stop noktasina varildi (%.2f, %.2f)", p.x, p.y);
      return BT::NodeStatus::SUCCESS;
    }
  }

  return BT::NodeStatus::FAILURE;
}

}  // namespace tulpar_bt
