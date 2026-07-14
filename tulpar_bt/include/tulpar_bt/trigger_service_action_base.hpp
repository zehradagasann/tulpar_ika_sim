#pragma once

#include <future>
#include <string>

#include "behaviortree_cpp/behavior_tree.h"
#include "rclcpp/rclcpp.hpp"
#include "std_srvs/srv/trigger.hpp"

namespace tulpar_bt
{

// Donanima/baska ekip uyesine bagli node'lar (HedefTespitYap, AtisYap)
// icin ortak taban sinif. Gercek servis (std_srvs/Trigger) ayaktaysa
// onu cagirir - bu sayede Emin'in goruntu isleme / lazer donanimi ekibi
// bu servisi hayata gecirdiginde node degistirilmeden calisir. Servis
// yoksa (bugunku durum) ve ilgili ROS parametresi (varsayilan true) ile
// simulate_mode acik ise, kisa bir gecikme sonrasi SUCCESS doner ve
// "SIMULASYON" olarak loglar.
class TriggerServiceActionBase : public BT::StatefulActionNode
{
public:
  TriggerServiceActionBase(
    const std::string & name, const BT::NodeConfig & config,
    std::string service_name, std::string simulate_param_name, std::string log_prefix);

  static BT::PortsList providedPorts()
  {
    return {
      BT::InputPort<double>("simulate_delay_sec", 1.0, "Simulasyon modunda beklenecek sure (sn)")
    };
  }

  BT::NodeStatus onStart() override;
  BT::NodeStatus onRunning() override;
  void onHalted() override;

protected:
  rclcpp::Node::SharedPtr node_;

private:
  std::string service_name_;
  std::string simulate_param_name_;
  std::string log_prefix_;

  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr client_;
  std::shared_future<std_srvs::srv::Trigger::Response::SharedPtr> future_;

  bool simulating_{false};
  double simulate_delay_sec_{1.0};
  rclcpp::Time start_time_;
};

}  // namespace tulpar_bt
