import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class BrightnessAnalysis:
    mean_brightness: float
    std_contrast: float
    condition: str
    clahe_applied: bool


OVEREXPOSED_THRESHOLD = 200.0
UNDEREXPOSED_THRESHOLD = 60.0
LOW_CONTRAST_THRESHOLD = 18.0
HIGH_VARIANCE_THRESHOLD = 45.0


def analyze_brightness(gray_image: np.ndarray) -> BrightnessAnalysis:
    mean_val = float(np.mean(gray_image))
    std_val = float(np.std(gray_image))

    if mean_val > OVEREXPOSED_THRESHOLD:
        condition = "overexposed"
    elif mean_val < UNDEREXPOSED_THRESHOLD:
        condition = "underexposed"
    elif std_val > HIGH_VARIANCE_THRESHOLD:
        condition = "high_variance"
    elif std_val < LOW_CONTRAST_THRESHOLD:
        condition = "low_contrast"
    else:
        condition = "normal"

    clahe_applied = condition != "normal"

    return BrightnessAnalysis(
        mean_brightness=mean_val,
        std_contrast=std_val,
        condition=condition,
        clahe_applied=clahe_applied,
    )


def apply_clahe(bgr_image: np.ndarray, clip_limit: float = 3.0, tile_size: int = 8) -> np.ndarray:
    lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    l_enhanced = clahe.apply(l_channel)

    lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
    bgr_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    return bgr_enhanced


def process_frame(bgr_image: np.ndarray):
    if bgr_image is None or bgr_image.size == 0:
        raise ValueError("Bos goruntu alindi.")

    if len(bgr_image.shape) != 3 or bgr_image.shape[2] != 3:
        raise ValueError(
            f"Beklenmeyen goruntu formati alindi: shape={bgr_image.shape}"
        )

    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    analysis = analyze_brightness(gray)

    if analysis.clahe_applied and analysis.condition != "high_variance":
        output_image = apply_clahe(bgr_image)
        analysis.clahe_applied = True
    else:
        output_image = bgr_image
        analysis.clahe_applied = False

    return output_image, analysis
