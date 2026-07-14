#include "tulpar_bt/trigger_service_action_base.hpp"

#include "tulpar_bt/ros_node_utils.hpp"

namespace tulpar_bt
{

TriggerServiceActionBase::TriggerServiceActionBase(
  const std::string & name, const BT::NodeConfig & config,
  std::string service_name, std::string simulate_param_name, std::string log_prefix)
: BT::StatefulActionNode(name, config),
  service_name_(std::move(service_name)),
  simulate_param_name_(std::move(simulate_param_name)),
  log_prefix_(std::move(log_prefix))
{
  node_ = getRosNode(config);
  client_ = node_->create_client<std_srvs::srv::Trigger>(service_name_);

  if (!node_->has_parameter(simulate_param_name_)) {
    node_->declare_parameter<bool>(simulate_param_name_, true);
  }
}

BT::NodeStatus TriggerServiceActionBase::onStart()
{
  getInput("simulate_delay_sec", simulate_delay_sec_);
  start_time_ = node_->now();

  if (client_->service_is_ready()) {
    simulating_ = false;
    RCLCPP_INFO(
      node_->get_logger(), "%s: gercek servis (%s) cagriliyor",
      log_prefix_.c_str(), service_name_.c_str());
    future_ = client_->async_send_request(
      std::make_shared<std_srvs::srv::Trigger::Request>()).future.share();
    return BT::NodeStatus::RUNNING;
  }

  const bool simulate_mode = node_->get_parameter(simulate_param_name_).as_bool();
  if (!simulate_mode) {
    RCLCPP_ERROR(
      node_->get_logger(),
      "%s: servis (%s) mevcut degil ve simulate_mode kapali - FAILURE",
      log_prefix_.c_str(), service_name_.c_str());
    return BT::NodeStatus::FAILURE;
  }

  simulating_ = true;
  RCLCPP_WARN(
    node_->get_logger(),
    "%s: SIMULASYON - gercek servis (%s) yok, donanim/veri bekleniyor, %.1fs simule ediliyor",
    log_prefix_.c_str(), service_name_.c_str(), simulate_delay_sec_);
  return BT::NodeStatus::RUNNING;
}

BT::NodeStatus TriggerServiceActionBase::onRunning()
{
  const double elapsed = (node_->now() - start_time_).seconds();

  if (simulating_) {
    if (elapsed >= simulate_delay_sec_) {
      RCLCPP_INFO(node_->get_logger(), "%s: SIMULASYON tamamlandi, SUCCESS", log_prefix_.c_str());
      return BT::NodeStatus::SUCCESS;
    }
    return BT::NodeStatus::RUNNING;
  }

  if (future_.wait_for(std::chrono::seconds(0)) == std::future_status::ready) {
    auto response = future_.get();
    if (response->success) {
      RCLCPP_INFO(
        node_->get_logger(), "%s: servis basarili (%s)",
        log_prefix_.c_str(), response->message.c_str());
      return BT::NodeStatus::SUCCESS;
    }
    RCLCPP_ERROR(
      node_->get_logger(), "%s: servis basarisiz (%s)",
      log_prefix_.c_str(), response->message.c_str());
    return BT::NodeStatus::FAILURE;
  }

  if (elapsed > 5.0) {
    RCLCPP_ERROR(node_->get_logger(), "%s: servis yaniti zaman asimina ugradi", log_prefix_.c_str());
    return BT::NodeStatus::FAILURE;
  }

  return BT::NodeStatus::RUNNING;
}

void TriggerServiceActionBase::onHalted()
{
}

}  // namespace tulpar_bt
