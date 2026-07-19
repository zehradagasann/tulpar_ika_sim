from dataclasses import dataclass


# Emin'in class_registry.yaml dosyasindaki kanonik /sign_detected etiketleri.
# shooting_target ve traffic_cone, parkur stage'lerinden cok yardimci algi
# etiketleridir; yine de uyumluluk icin asagida desteklenir.
STAGE_INFO = {
    #  class_name      (gorev,                speed_level, davranis)
    "stage_01":       ("su_gecisi",           "slow",   "none"),
    "stage_02":       ("tasli_cakilli_yol",   "slow",   "none"),
    "stage_03":       ("yan_egim",            "slow",   "none"),
    "stage_04":       ("dik_engel",           "slow",   "none"),
    "stage_05":       ("trafik_konileri",     "medium", "slalom_mode"),
    "stage_06":       ("kayar_engel",         "slow",   "dynamic_obstacle"),
    "stage_07":       ("engebeli_arazi",      "slow",   "center_track"),
    "stage_08":       ("dik_egim_cikis",      "slow",   "stop_required"),
    "stage_09":       ("atis_bolgesi",        "stop",   "shooting_mode"),
    "stage_10":       ("dik_egim_inis",       "slow",   "stop_required"),
    "stage_11":       ("hizlanma_baslangic",  "fast",   "acceleration_mode"),
    "stage_12":       ("atis_bolgesi_girisi", "slow",   "shooting_mode"),
    "stop_marking":   ("stop_cizgisi",        "stop",   "stop_required"),
    "shooting_target": ("atis_hedefi",        "stop",   "shooting_mode"),
    "traffic_cone":   ("trafik_konisi",       "medium", "slalom_mode"),
}

STAGE_ALIASES = {
    "stage12": "stage_12",
    "stop_line": "stop_marking",
    "stop_sign": "stop_marking",
}

DEFAULT_INFO = ("bilinmeyen", "medium", "none")

# speed_level oncelik sirasi (dusuk indeks = daha kisitlayici)
SPEED_PRIORITY = ["stop", "slow", "medium", "fast"]


@dataclass
class StageDecision:
    stage_id: str
    mission: str
    speed_level: str
    behavior: str
    reason: str


def normalize_stage_id(stage_id: str) -> str:
    normalized = stage_id.strip().lower()
    return STAGE_ALIASES.get(normalized, normalized)


def decide_stage(stage_id: str) -> StageDecision:
    normalized_stage_id = normalize_stage_id(stage_id)
    mission, speed_level, behavior = STAGE_INFO.get(normalized_stage_id, DEFAULT_INFO)
    reason = (
        f"{normalized_stage_id} -> {mission} -> "
        f"hiz={speed_level}, davranis={behavior}"
    )
    return StageDecision(
        stage_id=normalized_stage_id,
        mission=mission,
        speed_level=speed_level,
        behavior=behavior,
        reason=reason,
    )


def combine_speed(stage_speed: str, terrain_speed: str) -> str:
    """Iki hiz kararindan daha kisitlayici olani secer (min mantigi)."""
    stage_idx = SPEED_PRIORITY.index(stage_speed) if stage_speed in SPEED_PRIORITY else 2
    terrain_idx = SPEED_PRIORITY.index(terrain_speed) if terrain_speed in SPEED_PRIORITY else 2
    return SPEED_PRIORITY[min(stage_idx, terrain_idx)]
