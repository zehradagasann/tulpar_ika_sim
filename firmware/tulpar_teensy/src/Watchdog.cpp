#include "Watchdog.h"

namespace tulpar {

void Watchdog::begin(uint32_t timeout_ms) {
  WDT_timings_t config;
  config.trigger = (timeout_ms / 1000.0f) * 0.8f;  // erken uyari (opsiyonel)
  config.timeout = timeout_ms / 1000.0f;
  wdt_.begin(config);
}

void Watchdog::feed() { wdt_.feed(); }

}  // namespace tulpar
