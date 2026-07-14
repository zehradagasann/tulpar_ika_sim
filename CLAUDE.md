# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a ROS 2 / Gazebo Harmonic simulation package for the **Tulpar IKA** — a 4-wheeled differential-drive ground robot (62 kg, 1200×600×240 mm chassis, Ø330 mm wheels). The package name is `tulpar_description`.

## Build & Run

The colcon workspace root is `~/tulpar_ws`. The repo lives at `~/tulpar_ws/src/tulpar_ika_sim`.

```bash
# Build
cd ~/tulpar_ws
colcon build --packages-select tulpar_description

# Source the workspace (required before ros2 commands)
source ~/tulpar_ws/install/setup.bash

# Launch Gazebo with the default world (S-01 terrain course)
ros2 launch tulpar_description gazebo.launch.py

# Launch with a specific world
ros2 launch tulpar_description gazebo.launch.py world:=/path/to/world.sdf

# Send velocity commands manually (while simulation runs)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3}}" --once

# Run a test script (Gazebo must be running first)
python3 test_kanit/S01/s01_rampa_testi.py
python3 test_kanit/E02/hizlanma_testi.py
python3 test_kanit/S02/s02_hedef_testi.py
```

## Architecture

### Robot model (`urdf/robot.urdf.xacro`)
- Frame hierarchy: `base_footprint` → `base_link` → wheels (FL/RL/FR/RR), `lidar_link`, `camera_link`
- `base_link` sits 0.165 m above ground (wheel radius); `base_footprint` is at ground level
- Visual mesh: `meshes/tulpar_yeni.stl` (scaled 0.001 — file is in mm)
- Gazebo plugins embedded in URDF: `DiffDrive` (subscribes `/cmd_vel`, publishes `/odom`), `JointStatePublisher` (publishes `/joint_states`)
- Sensors: RPLidar S2 on `lidar_link` (topic `scan`, 800 samples, 30 m range), RealSense D455 on `camera_link` (topic `camera/depth`, 848×480, 0.4–6 m)

### Launch file (`launch/gazebo.launch.py`)
Starts three nodes:
1. `robot_state_publisher` — processes the xacro and publishes `/robot_description` + TF
2. `gz_sim` — Gazebo Harmonic with `--render-engine ogre`
3. `parameter_bridge` — bridges ROS ↔ Gazebo topics: `/cmd_vel` (ROS→GZ), `/odom`, `/joint_states`, `/scan`, `/camera/depth` (GZ→ROS)

### Worlds (`worlds/`)
| File | Purpose |
|------|---------|
| `s01_robotlu_world.sdf` | S-01 terrain course: 10-step staircase ramp (~45% grade), 20% side-slope platform, 15 cm block, 5 cm speed bumps. **Includes robot spawn.** |
| `s02_hedef_world.sdf` | S-02 target detection: flat ground with A3 target board at 10 m |
| `e02_duz_world.sdf` | E-02 acceleration: flat 30+ m track with distance markers |
| `test.world` | Basic smoke-test world |

`s01_robotlu_world.sdf` embeds the full robot model (converted from URDF) so the robot spawns automatically. The other worlds require the robot to be spawned separately via the launch file.

### Test scripts (`test_kanit/`)
Each test is a standalone ROS 2 node that publishes `/cmd_vel` and subscribes `/odom`. Pattern:
1. Wait up to 5 s for `/odom` (abort if none received — check Gazebo is running)
2. Execute movement sequence, collecting timestamped data
3. Write results to a CSV next to the script
4. Companion `*_grafik.py` scripts read the CSV and produce matplotlib plots

| Directory | Tests |
|-----------|-------|
| `S01/` | Ramp stop/brake, side slope, 15 cm block, flat ground, full course |
| `S02/` | Target detection & lock (geometric simulation using camera FoV math) |
| `E02/` | 30 m straight-line acceleration at 0.5 m/s |

### Behavior Tree (`behavior_trees/`)
`ana_tree.xml` — main Behavior Tree draft (BehaviorTree.CPP v4, `BTCPP_format="4"`, Groot2-openable). Sequence: wait for system ready → repeat until course end → ReactiveFallback between (sign-detected shoot flow: stop Nav2, lock target, fire laser, resume Nav2) and default autonomous driving (Nav2 `NavigateToPose` placeholder). All action/condition nodes (`TabelaAlgılandiMi`, `HedefTespitYap`, `AtisYap`, etc.) are unimplemented placeholders — real C++ node registrations land on Day 2.

## Proje Bağlamı

- **Yarışma**: TEKNOFEST 2026 İnsansız Kara Aracı (İKA) — Araç: TULPAR
- **Kullanıcı**: Talha Dağ — Otonom Akış & Entegrasyon Sorumlusu; yazılım ekibi: Emin (görüntü işleme), Zehra (parkur algoritmaları / haberleşme)
- **Sprint**: 13–27 Temmuz 2026 (15 günlük yoğun uygulama sprinti)
- **KRİTİK DEADLINE**: Araç Kanıt Videosu (AKV) teslimi **20 Temmuz 2026 17:00** (şartname §4.4) — bu tarihe yaklaşan görevlerde uyar
- **Talha'nın görev alanları**: BT (Behavior Tree) mimarisi, Nav2 entegrasyonu, yer istasyonu (Electron + React + rclnodejs), EKF / sensör füzyonu, Watchdog/Failsafe, ELRS RC override, ağ altyapısı (Bullet M5)
- **Git kuralı**: Her zaman `talha_gelistirme` branch'inde çalış; `main` ve `yazilim_gelistirme`'ye direkt commit atma. Gün sonunda commit + push + PR'ı hatırlat.
- **Test kodları ↔ parkur eşleşmesi**: S-01 (arazi), S-02 (hedef tespit), S-03 (su geçişi), S-04 (slalom/kayar engel), S-05 (tam parkur), E-02 (hızlanma), E-03 (BMS), E-04 (failsafe), B-04 (boyut kontrolü)
- **Donanım**: Jetson Orin NX + Teensy 4.1 (CAN → 4× VESC 75100), RPLidar S2, RealSense D435if, WT901C-RS485 IMU, ZED-F9P RTK GNSS

## Key Physical Parameters
- Wheel separation: 1.04 m; wheel radius: 0.165 m
- Max linear velocity: 0.785 m/s; max angular velocity: 7.854 rad/s
- Max wheel torque: 50 Nm (in SDF world); 21.6 Nm (in URDF plugin — SDF takes precedence when robot is embedded in world)
- Physics: ODE solver, 1 ms step, 1000 Hz update rate, 100 iterations
