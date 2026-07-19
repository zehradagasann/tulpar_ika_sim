#pragma once

#include <string>

#include "tulpar_bt/trigger_service_action_base.hpp"

namespace tulpar_bt
{

// YAZILIMSAL TAMAMLANDI - lazer isaretleme donanimi bekleniyor.
// Gercek ROS2 arayuzu: /atis_yap (std_srvs/Trigger) service client.
// Servis ayaktaysa gercekten cagirir; degilse simulate_mode ile simule eder.
class AtisYap : public TriggerServiceActionBase
{
public:
  AtisYap(const std::string & name, const BT::NodeConfig & config)
  : TriggerServiceActionBase(
      name, config, "/atis_yap", "atis_simulate_mode", "AtisYap", "/tulpar_bt/atis_event")
  {}
};

}  // namespace tulpar_bt
