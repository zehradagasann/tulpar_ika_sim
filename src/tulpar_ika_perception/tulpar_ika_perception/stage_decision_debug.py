from stage_decision import decide_stage, combine_speed


def main() -> None:
    print("=== StageDecision Debug ===")
    all_stages = [f"stage_{i:02d}" for i in range(1, 13)] + ["stop_marking", "unknown"]
    for stage_id in all_stages:
        d = decide_stage(stage_id)
        print(f"{d.stage_id:14s} gorev={d.mission:20s} hiz={d.speed_level:7s} davranis={d.behavior}")

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
