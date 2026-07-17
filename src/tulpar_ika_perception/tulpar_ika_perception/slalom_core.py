from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ConeDetection:
    x: float
    y: float
    color: str


@dataclass
class SlalomResult:
    target_point: Optional[Tuple[float, float]]
    turn_direction: str
    speed_level: str


def split_cones_left_right(
    detections: List[ConeDetection],
    image_center_x: float,
) -> Tuple[List[ConeDetection], List[ConeDetection]]:
    left_cones = []
    right_cones = []

    for detection in detections:
        if detection.x < image_center_x:
            left_cones.append(detection)
        else:
            right_cones.append(detection)

    return left_cones, right_cones


def pair_cones(
    left_cones: List[ConeDetection],
    right_cones: List[ConeDetection],
) -> List[Tuple[ConeDetection, ConeDetection]]:
    pairs = []

    count = min(len(left_cones), len(right_cones))
    for i in range(count):
        pairs.append((left_cones[i], right_cones[i]))

    return pairs


def compute_midpoints(
    pairs: List[Tuple[ConeDetection, ConeDetection]],
) -> List[Tuple[float, float]]:
    midpoints = []

    for left_cone, right_cone in pairs:
        mid_x = (left_cone.x + right_cone.x) / 2.0
        mid_y = (left_cone.y + right_cone.y) / 2.0
        midpoints.append((mid_x, mid_y))

    return midpoints


def select_target_point(
    midpoints: List[Tuple[float, float]],
) -> Optional[Tuple[float, float]]:
    if not midpoints:
        return None

    return sorted(midpoints, key=lambda point: point[1])[0]


def compute_turn_direction(
    target_point: Optional[Tuple[float, float]],
    image_center_x: float,
    tolerance: float = 20.0,
) -> str:
    if target_point is None:
        return "unknown"

    target_x = target_point[0]

    if target_x < image_center_x - tolerance:
        return "left"

    if target_x > image_center_x + tolerance:
        return "right"

    return "straight"


def compute_speed_level(
    target_point: Optional[Tuple[float, float]],
) -> str:
    if target_point is None:
        return "stop"

    target_y = target_point[1]

    if target_y < 150:
        return "fast"

    if target_y < 300:
        return "medium"

    return "slow"


def run_slalom_logic(
    detections: List[ConeDetection],
    image_center_x: float,
) -> SlalomResult:
    left_cones, right_cones = split_cones_left_right(
        detections,
        image_center_x,
    )

    pairs = pair_cones(left_cones, right_cones)
    midpoints = compute_midpoints(pairs)
    target_point = select_target_point(midpoints)
    turn_direction = compute_turn_direction(
        target_point,
        image_center_x,
    )
    speed_level = compute_speed_level(target_point)

    return SlalomResult(
        target_point=target_point,
        turn_direction=turn_direction,
        speed_level=speed_level,
    )
