import numpy as np
from brightness_filter import process_frame


def make_test_image(mean_value: int, noise_std: int = 10) -> np.ndarray:
    base = np.full((240, 320, 3), mean_value, dtype=np.uint8)
    noise = np.random.normal(0, noise_std, base.shape).astype(np.int16)
    noisy = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy


def main() -> None:
    print("=== BrightnessFilter Debug (Sanliurfa saha kosullari) ===")

    test_cases = [
        ("normal_gun_isigi",        128, 40),
        ("gunes_parlamasi_hafif",   210, 20),
        ("ogle_gunesi_urfa_45C",    248,  8),   # oglen dik gunes, ekstrem parlama
        ("golge_karanlik",           35, 10),
        ("dusuk_kontrast_sisli",    128,  8),
        ("golge_gunes_gecisi",      128, 90),   # keskin golge/gunes siniri - yuksek std
    ]

    for name, mean_val, noise_std in test_cases:
        img = make_test_image(mean_val, noise_std)
        _, analysis = process_frame(img)
        print(
            f"{name:22s} mean={analysis.mean_brightness:6.1f} "
            f"std={analysis.std_contrast:5.1f} "
            f"durum={analysis.condition:15s} "
            f"clahe={analysis.clahe_applied}"
        )


if __name__ == "__main__":
    main()
