#pragma once

#include <string>

#include "tulpar_bt/trigger_service_action_base.hpp"

namespace tulpar_bt
{

// YAZILIMSAL TAMAMLANDI - kamera ile hedef kilitleme donanimi/Emin'in
// goruntu isleme servisi bekleniyor.
// Gercek ROS2 arayuzu: /hedef_tespit_yap (std_srvs/Trigger) service client.
// Servis ayaktaysa gercekten cagirir; degilse simulate_mode ile simule eder.
class HedefTespitYap : public TriggerServiceActionBase
{
public:
  HedefTespitYap(const std::string & name, const BT::NodeConfig & config)
  : TriggerServiceActionBase(
      name, config, "/hedef_tespit_yap", "hedef_tespit_simulate_mode", "HedefTespitYap")
  {}
};

}  // namespace tulpar_bt
