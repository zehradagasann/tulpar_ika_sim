from tulpar_ika_perception.stage_decision import combine_speed, decide_stage


def main() -> None:
    print("=== StageDecision Debug ===")
    all_stages = [
        f"stage_{i:02d}" for i in range(1, 13)
    ] + [
        "stop_marking",
        "stop_line",
        "traffic_cone",
        "shooting_target",
        "unknown",
    ]
    for stage_id in all_stages:
        d = decide_stage(stage_id)
        print(
            f"{stage_id:16s} -> "
            f"normalized={d.stage_id:14s} "
            f"gorev={d.mission:20s} "
            f"hiz={d.speed_level:7s} "
            f"davranis={d.behavior:18s}"
        )

    print()
    print("=== combine_speed testleri ===")
    cases = [
        ("medium", "slow"),   # zemin daha kisitlayici -> slow
        ("stop", "fast"),     # stage daha kisitlayici -> stop
        ("fast", "medium"),   # -> medium
        ("slow", "slow"),     # esit -> slow
    ]
    for stage_s, terrain_s in cases:
        result = combine_speed(stage_s, terrain_s)
        print(f"stage={stage_s:7s} + terrain={terrain_s:7s} -> {result}")


if __name__ == "__main__":
    main()
