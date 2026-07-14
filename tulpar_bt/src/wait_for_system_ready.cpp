#include "tulpar_bt/wait_for_system_ready.hpp"

#include <sstream>

#include "tulpar_bt/ros_node_utils.hpp"

namespace tulpar_bt
{

namespace
{
std::vector<std::string> splitCsv(const std::string & s)
{
  std::vector<std::string> out;
  std::stringstream ss(s);
  std::string item;
  while (std::getline(ss, item, ',')) {
    size_t start = item.find_first_not_of(" \t");
    size_t end = item.find_last_not_of(" \t");
    if (start != std::string::npos) {
      out.push_back(item.substr(start, end - start + 1));
    }
  }
  return out;
}
}  // namespace

WaitForSystemReady::WaitForSystemReady(
  const std::string & name, const BT::NodeConfig & config)
: BT::StatefulActionNode(name, config)
{
  node_ = getRosNode(config);
}

BT::NodeStatus WaitForSystemReady::onStart()
{
  std::string node_names_csv;
  getInput("node_names", node_names_csv);
  getInput("timeout_sec", timeout_sec_);

  checks_.clear();
  for (const auto & n : splitCsv(node_names_csv)) {
    NodeCheck check;
    check.name = n;
    check.client = node_->create_client<lifecycle_msgs::srv::GetState>(
      "/" + n + "/get_state");
    checks_.push_back(check);
  }

  start_time_ = node_->now();
  RCLCPP_INFO(
    node_->get_logger(),
    "WaitForSystemReady: %zu lifecycle node bekleniyor (timeout=%.1fs)",
    checks_.size(), timeout_sec_);

  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus WaitForSystemReady::onRunning()
{
  bool all_active = true;

  for (auto & check : checks_) {
    if (check.active) {
      continue;
    }

    if (!check.future.valid()) {
      if (check.client->service_is_ready()) {
        check.future = check.client->async_send_request(
          std::make_shared<lifecycle_msgs::srv::GetState::Request>()).future.share();
      }
      all_active = false;
      continue;
    }

    if (check.future.wait_for(std::chrono::seconds(0)) == std::future_status::ready) {
      auto response = check.future.get();
      if (response->current_state.id == lifecycle_msgs::msg::State::PRIMARY_STATE_ACTIVE) {
        check.active = true;
        RCLCPP_INFO(node_->get_logger(), "WaitForSystemReady: '%s' ACTIVE", check.name.c_str());
      } else {
        check.future = rclcpp::Client<lifecycle_msgs::srv::GetState>::SharedFuture();
        all_active = false;
      }
    } else {
      all_active = false;
    }
  }

  if (all_active) {
    RCLCPP_INFO(node_->get_logger(), "WaitForSystemReady: tum node'lar ACTIVE, devam ediliyor");
    return BT::NodeStatus::SUCCESS;
  }

  double elapsed = (node_->now() - start_time_).seconds();
  if (elapsed > timeout_sec_) {
    RCLCPP_ERROR(
      node_->get_logger(),
      "WaitForSystemReady: timeout (%.1fs) - sistem hazir olmadi", timeout_sec_);
    return BT::NodeStatus::FAILURE;
  }

  return BT::NodeStatus::RUNNING;
}

void WaitForSystemReady::onHalted()
{
}

}  // namespace tulpar_bt
