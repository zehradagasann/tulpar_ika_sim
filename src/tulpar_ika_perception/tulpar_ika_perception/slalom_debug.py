from tulpar_ika_perception.slalom_core import (
    ConeDetection,
    run_slalom_logic,
)


def main() -> None:
    detections = [
        ConeDetection(x=180.0, y=220.0, color="blue"),
        ConeDetection(x=460.0, y=230.0, color="yellow"),
        ConeDetection(x=200.0, y=320.0, color="blue"),
        ConeDetection(x=440.0, y=330.0, color="yellow"),
    ]

    image_center_x = 320.0

    result = run_slalom_logic(
        detections=detections,
        image_center_x=image_center_x,
    )

    print("Slalom debug sonucu:")
    print(f"target_point={result.target_point}")
    print(f"turn_direction={result.turn_direction}")
    print(f"speed_level={result.speed_level}")


if __name__ == "__main__":
    main()
