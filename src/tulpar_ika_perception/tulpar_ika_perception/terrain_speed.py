from dataclasses import dataclass

from tulpar_ika_perception.stage_decision import STAGE_INFO, normalize_stage_id

TERRAIN_STAGE_MAP = {
    "stage_01": "water_crossing",
    "stage_02": "rough_gravel",
    "stage_03": "side_slope",
    "stage_07": "rough_terrain",
}

TERRAIN_SPEED_MAP = {
    "water_crossing": "slow",
    "rough_gravel":   "slow",
    "side_slope":     "slow",
    "rough_terrain":  "slow",
    "normal":         "medium",
}


@dataclass
class TerrainSpeedResult:
    stage_id: str
    terrain_type: str
    speed_level: str
    is_known_stage: bool
    reason: str


def classify_terrain(stage_id: str) -> str:
    normalized_stage_id = normalize_stage_id(stage_id)
    return TERRAIN_STAGE_MAP.get(normalized_stage_id, "normal")


def compute_terrain_speed(stage_id: str) -> TerrainSpeedResult:
    normalized_stage_id = normalize_stage_id(stage_id)
    terrain_type = classify_terrain(normalized_stage_id)
    speed_level = TERRAIN_SPEED_MAP.get(terrain_type, "medium")
    is_known_stage = normalized_stage_id in STAGE_INFO

    if not is_known_stage:
        reason = f"{normalized_stage_id} taninmayan stage, varsayilan hiz={speed_level}"
    elif terrain_type == "normal":
        reason = f"{normalized_stage_id} zorlu zemin degil, hiz kisiti yok"
    else:
        reason = (
            f"{normalized_stage_id} -> {terrain_type} -> "
            f"hiz dusuruldu: {speed_level}"
        )

    return TerrainSpeedResult(
        stage_id=normalized_stage_id,
        terrain_type=terrain_type,
        speed_level=speed_level,
        is_known_stage=is_known_stage,
        reason=reason,
    )
