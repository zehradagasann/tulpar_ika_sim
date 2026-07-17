from dataclasses import dataclass
from typing import Optional


TERRAIN_STAGE_MAP = {
    "stage_02": "rough_water",
    "stage_03": "rough_gravel",
    "stage_07": "rough_terrain",
}

TERRAIN_SPEED_MAP = {
    "rough_water":   "slow",
    "rough_gravel":  "slow",
    "rough_terrain": "slow",
    "normal":        "medium",
}


@dataclass
class TerrainSpeedResult:
    stage_id: str
    terrain_type: str
    speed_level: str
    reason: str


def classify_terrain(stage_id: str) -> str:
    return TERRAIN_STAGE_MAP.get(stage_id, "normal")


def compute_terrain_speed(stage_id: str) -> TerrainSpeedResult:
    terrain_type = classify_terrain(stage_id)
    speed_level = TERRAIN_SPEED_MAP.get(terrain_type, "medium")

    if terrain_type == "normal":
        reason = f"{stage_id} zorlu zemin degil, hiz kisiti yok"
    else:
        reason = f"{stage_id} -> {terrain_type} -> hiz dusuruldu: {speed_level}"

    return TerrainSpeedResult(
        stage_id=stage_id,
        terrain_type=terrain_type,
        speed_level=speed_level,
        reason=reason,
    )
