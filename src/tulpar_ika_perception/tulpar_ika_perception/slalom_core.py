from dataclasses import dataclass
from typing import List, Optional, Tuple

FAR_TARGET_Y_THRESHOLD = 150.0
NEAR_TARGET_Y_THRESHOLD = 300.0
TURN_TOLERANCE_PX = 20.0


@dataclass
class ImageConeDetection:
    image_x: float
    image_y: float
    cone_color: str


# Geriye donuk uyumluluk: debug araclari hala ConeDetection ismini kullaniyor.
ConeDetection = ImageConeDetection


@dataclass
class SlalomResult:
    target_point: Optional[Tuple[float, float]]
    turn_direction: str
    speed_level: str


def split_cones_left_right(
    detections: List[ImageConeDetection],
    image_center_x: float,
) -> Tuple[List[ImageConeDetection], List[ImageConeDetection]]:
    left_cones = []
    right_cones = []

    for detection in detections:
        if detection.image_x < image_center_x:
            left_cones.append(detection)
        else:
            right_cones.append(detection)

    # En yakin koniler once gelsin diye alt satira (buyuk y) gore sirala.
    left_cones.sort(key=lambda detection: (-detection.image_y, detection.image_x))
    right_cones.sort(key=lambda detection: (-detection.image_y, detection.image_x))

    return left_cones, right_cones


def pair_cones(
    left_cones: List[ImageConeDetection],
    right_cones: List[ImageConeDetection],
) -> List[Tuple[ImageConeDetection, ImageConeDetection]]:
    pairs = []

    count = min(len(left_cones), len(right_cones))
    for i in range(count):
        pairs.append((left_cones[i], right_cones[i]))

    return pairs


def compute_midpoints(
    pairs: List[Tuple[ImageConeDetection, ImageConeDetection]],
) -> List[Tuple[float, float]]:
    midpoints = []

    for left_cone, right_cone in pairs:
        mid_x = (left_cone.image_x + right_cone.image_x) / 2.0
        mid_y = (left_cone.image_y + right_cone.image_y) / 2.0
        midpoints.append((mid_x, mid_y))

    return midpoints


def select_target_point(
    midpoints: List[Tuple[float, float]],
) -> Optional[Tuple[float, float]]:
    if not midpoints:
        return None

    # Araca en yakin kapiyi hedefle: goruntude en buyuk y degeri.
    return max(midpoints, key=lambda point: point[1])


def compute_turn_direction(
    target_point: Optional[Tuple[float, float]],
    image_center_x: float,
    tolerance: float = TURN_TOLERANCE_PX,
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

    if target_y < FAR_TARGET_Y_THRESHOLD:
        return "medium"

    if target_y < NEAR_TARGET_Y_THRESHOLD:
        return "slow"

    # Kapi araca cok yakinsa fren yerine temkinli ilerleme korunur.
    return "slow"


def run_slalom_logic(
    detections: List[ImageConeDetection],
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
