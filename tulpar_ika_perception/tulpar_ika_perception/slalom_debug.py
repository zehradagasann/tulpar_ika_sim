from tulpar_ika_perception.slalom_core import (
    ConeDetection,
    run_slalom_logic,
)


def main() -> None:
    detections = [
        ConeDetection(image_x=180.0, image_y=220.0, cone_color="blue"),
        ConeDetection(image_x=460.0, image_y=230.0, cone_color="yellow"),
        ConeDetection(image_x=200.0, image_y=320.0, cone_color="blue"),
        ConeDetection(image_x=440.0, image_y=330.0, cone_color="yellow"),
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
