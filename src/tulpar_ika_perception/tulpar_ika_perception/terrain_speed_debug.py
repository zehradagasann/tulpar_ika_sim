from terrain_speed import compute_terrain_speed


def main() -> None:
    test_cases = [
        "stage_01",
        "stage_02",
        "stage_03",
        "stage_07",
        "stage_10",
        "unknown",
    ]

    print("=== TerrainSpeed Debug ===")
    for stage_id in test_cases:
        result = compute_terrain_speed(stage_id)
        print(
            f"stage={result.stage_id:12s} "
            f"terrain={result.terrain_type:15s} "
            f"speed={result.speed_level:8s} "
            f"| {result.reason}"
        )


if __name__ == "__main__":
    main()
