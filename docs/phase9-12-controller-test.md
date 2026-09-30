# Phases 9–12: RC-100, manual-mode policy, GitHub, and Raspberry Pi

Updated: 2026-09-30

This document records the hardware transport patch and the test path for the user's
RC-100 + BT-410 currently connected to the TurtleBot3 OpenCR/Pi. The desktop
simulator must use a different ROS domain from the physical robot. Do not start the
simulation in the robot's domain: Nav2 publishes `/cmd_vel` and that could be
consumed by the real base.

## Phase 9 — RC-100 event transport

The official firmware source audit confirmed that RC-100 Button 1 and Button 4
have masks `16` and `128`; existing U/D/L/R movement branches are preserved.
This patch uses the ROBOTIS OpenCR DYNAMIXEL Slave protocol rather than a new serial
format.

Pinned upstream sources:

- OpenCR commit `68ec75d8a400949580ecf263e0105ea9743b878e`
- TurtleBot3 tag `2.3.6`, commit `da785b7201d317e6e2a662e41bb3d3fd50ebd503`

Changes stored in `firmware/patches/`:

- OpenCR caches the latest valid RC-100 data frame and detects Button 1/4 rising
  edges. It exposes wrapping 8-bit event sequence counters at control-table bytes
  24 and 25. DYNAMIXEL Slave reads already cover address 10–182. Button 1 also
  clears any latched manual velocity before Nav2 takes over.
- The OpenCR field at byte 52 indicates whether PATROL owns the wheels. While set,
  RC direction keys do not contribute velocity. On IDLE the existing manual
  direction mapping is active again.
- The TurtleBot3 2.3.6 host node reads the sequence counters every 50 ms and emits
  `START` or `STOP` on `/patrol_command`. If Button 1 and Button 4 counters change
  in one poll, STOP wins.
- The host node subscribes to transient-local `/patrol_state` and writes the
  PATROL/IDLE ownership byte back to OpenCR.

Patch application script validates both exact upstream commits and supports
re-running after patches are applied:

```bash
tools/apply_phase9_patches.sh /path/to/OpenCR /path/to/turtlebot3-2.3.6
```

Patch verification performed locally:

```bash
git -C /path/to/OpenCR apply --check /path/to/bellingham/firmware/patches/opencr-rc100-patrol.patch
git -C /path/to/turtlebot3-2.3.6 apply --check /path/to/bellingham/firmware/patches/turtlebot3-node-rc100-patrol.patch
```

The TurtleBot3 2.3.6 `turtlebot3_node` patched source compiled successfully as a
ROS 2 Jazzy overlay on the desktop. The Pi overlay script also completed on the
desktop against a temporary test workspace: `turtlebot3_node` and
`turtlebot_patrol` both built. This validates the script's source selection,
patching, rosdep and colcon steps but is not a Raspberry Pi test. An isolated
Arduino CLI 1.5.1 and OpenCR board core 1.5.3 were installed under `/tmp` for the
firmware build attempt, with Dynamixel2Arduino 0.6.1 selected per OpenCR source.
Compilation currently stops before compiling the sketch because the OpenCR
compiler bundled with that core is a 32-bit executable and this desktop lacks its
i386 runtime loader. Firmware flash, RC packets, and byte 24/25 readback still
require the physical OpenCR.

For Waffle Pi, ROBOTIS identifies the OpenCR sketch as `turtlebot3_waffle` (Waffle
and Waffle Pi use this sketch). Build and flash it from the PC with the OpenCR
board package; the official manual does not support installing the OpenCR Arduino
board manager on Raspberry Pi ARM. Use the patched OpenCR `turtlebot3_ros2`
library when compiling, then flash the resulting firmware to the board. The
patched TurtleBot3 ROS node belongs in a Pi colcon overlay; firmware and host
software must both be patched for the new control fields to agree.

On an Ubuntu x86_64 desktop, install the 32-bit compatibility runtime required by
the ROBOTIS OpenCR toolchain (package availability can differ by Ubuntu release):

```bash
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install libncurses5-dev:i386
```

Then install Arduino CLI/OpenCR core/Dynamixel2Arduino through the official CLI,
apply the pinned OpenCR patch, and compile without flashing:

```bash
arduino-cli config add board_manager.additional_urls https://raw.githubusercontent.com/ROBOTIS-GIT/OpenCR/master/arduino/opencr_release/package_opencr_index.json
arduino-cli core update-index
arduino-cli core install OpenCR:OpenCR@1.5.3
arduino-cli lib install Dynamixel2Arduino@0.6.1
tools/compile_opencr.sh /path/to/OpenCR
```

`compile_opencr.sh` builds the Waffle/Waffle Pi sketch and explicitly reports that
it did not flash the board. The ROBOTIS PC workflow selects OpenCR > OpenCR,
opens the `turtlebot3_waffle` sketch from the patched source, and uploads after
reviewing the build.

Before the hardware test:

1. Save a copy of the current OpenCR firmware/configuration and note the USB device
   path. The user's current Pi reports OpenCR at `/dev/ttyACM0`.
2. Apply the firmware patch and build the Waffle sketch. Do not flash a binary
   built from a different OpenCR/TurtleBot3 source revision.
3. Apply the host patch and build an overlay containing `turtlebot3_node`.
4. Reconnect OpenCR to Pi, source the overlay before starting TurtleBot3 bringup,
   and confirm that the existing `/cmd_vel`, `/odom`, `/scan`, IMU, and manual
   direction behavior still appear as before.
5. Observe `/patrol_command` on the robot's ROS domain while pressing only Button
   1 and Button 4. Expect `START` and `STOP` once per press.

Do not test RC direction keys while the robot is on the floor during the isolated
simulator test: those keys remain real manual controls whenever the physical
`/patrol_state` is IDLE. The simulation isolation protects the real base from the
simulator's `/cmd_vel`; it does not change the original RC manual-drive wiring.

## Phase 10 — manual control and ownership policy

The controller policy is:

- IDLE: preserve the official U/D/L/R, Button 5 clear, and Button 6 constant-speed
  behavior.
- PATROL: Nav2 owns the wheels; firmware clears any previously latched manual
  velocity and suppresses directional RC velocity contributions.
- Button 4: request STOP immediately through the same patrol command state machine.
- PATROL state is written back to OpenCR. STOPPING, IDLE, or ERROR relinquishes
  patrol ownership and restores manual RC movement.

The code-level diff preserves the existing direction mapping and introduces the
ownership check around its application. The actual controller test is still
pending. After firmware/host installation, manually verify direction keys in IDLE
in a controlled test area, then verify they cannot add wheel speed during PATROL.
Finally press Button 4 and confirm IDLE plus manual control availability. Do not
claim this phase's physical test as passed before observing these results on the
actual Waffle Pi.

## Domain-isolated simulation with the physical remote

The physical Pi is expected to keep its existing ROS domain, currently assumed to
be the default `0`. The desktop simulation uses domain `42`. `patrol_sim.launch.py`
can start two one-way ROBOTIS-free `domain_bridge` topic relays:

- Robot domain → simulation domain: `/patrol_command` only.
- Simulation domain → robot domain: `/patrol_state` only.

No velocity, odometry, scan, or TF topic is bridged. `domain_bridge` uses the ROS 2
official implementation. Install the desktop relay package:

```bash
sudo apt install ros-jazzy-domain-bridge
```

On the desktop, launch simulation and both command/state relays:

```bash
cd ~/bellingham
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
ros2 launch turtlebot_patrol patrol_sim.launch.py enable_rc100_bridge:=true robot_domain_id:=0 simulation_domain_id:=42
```

To send mock commands instead, use `ROS_DOMAIN_ID=42` in the terminal that sends
the command. With the physical remote bridge enabled, press Button 1, observe the
Gazebo robot run the four waypoint loop, then press Button 4 and observe Nav2
cancel to IDLE. Watch the physical robot remain unaffected by simulator velocity.

If the Pi has a non-default domain, pass that value as `robot_domain_id:=N`. Keep
the simulation on a different ID. The Pi's ROS 2 processes must remain in the same
robot domain. If the Pi and desktop are not on the same LAN/VPN or DDS discovery
cannot pass through the network, configure ROS 2 discovery/networking before
testing; this project has not installed a custom network protocol.

## Phase 11 — GitHub repository

Repository files now include a user-facing `README.md`, the phase records, source
patches, an apply script, sim and real-robot launch files, and `.gitignore`. This
workspace's local Git repository is on branch `main`; it has no commit and no
remote yet. Publishing cannot be completed without a GitHub repository URL or
authorized `gh` repository creation. Once the remote exists:

```bash
cd ~/bellingham
git add .gitignore README.md PROJECT_SUMMARY_AND_RUNBOOK.txt docs src firmware tools
git diff --cached --check
git commit -m "Add TurtleBot3 waypoint patrol and RC-100 integration"
git remote add origin <GitHub repository URL>
git push -u origin main
```

Before making the repository public, review the maintainer identity in
`src/turtlebot_patrol/setup.py` and the commit contents. Do not add build/install/
log output or board-specific binaries.

## Phase 12 — Raspberry Pi overlay and launch

The Pi should keep the current TurtleBot3 bringup and install only runtime/Nav2
dependencies, not Gazebo simulation packages. From a fresh checkout of this
repository, install dependencies and build the patrol package plus the patched
TurtleBot3 2.3.6 host node in an overlay. The OpenCR source/firmware patch is
compiled and flashed separately from a desktop PC.

Robot bringup terminal (after the overlay has been sourced):

```bash
source /opt/ros/jazzy/setup.bash
source ~/bellingham/install/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
export LDS_MODEL=LDS-03
ros2 launch turtlebot3_bringup robot.launch.py
```

Navigation/patrol terminal; replace both paths with files for the actual mapped
area, and confirm the waypoint YAML uses that map's `map` frame:

```bash
source /opt/ros/jazzy/setup.bash
source ~/bellingham/install/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
ros2 launch turtlebot_patrol patrol_robot.launch.py map:=/absolute/path/to/map.yaml waypoints_file:=/absolute/path/to/waypoints.yaml
```

Start by verifying Nav2 localization and sensor topics, then mock START/STOP from a
third terminal in the robot's domain. Only after this passes, test RC Button 1/4.
Check STOP cancellation, `cmd_vel` zeros, `/odom`, `/scan`, and manual control.

The actual Pi map file, Waffle Pi Navigation2 tuning, hardware startup order,
OpenCR firmware build, and physical tests are not available in this desktop
workspace. Phase 12 stays incomplete until these steps have been run on the Pi.

## Verification status

- [x] TurtleBot3 node patch applies to official 2.3.6 source and compiles on desktop.
- [x] Pi overlay build script tested on desktop using an isolated temporary overlay.
- [x] Simulation launch defaults to ROS domain 42, separate from assumed robot domain 0.
- [x] Optional one-way bridge configuration names only `/patrol_command` and
      `/patrol_state`.
- [x] Built ROS 2 `domain_bridge` 0.5.0 from its official source and tested both
      configured directions locally: `/patrol_command` 0→42 and transient-local
      `/patrol_state` 42→0.
- [ ] Domain bridge tested with actual Pi DDS discovery over the robot's LAN.
- [ ] OpenCR firmware compiles using the OpenCR board package (currently blocked by missing i386 runtime).
- [ ] Patched firmware flashed; OpenCR control bytes 24/25 and 52 verified.
- [ ] Pi overlay built and launched with the patched host node.
- [ ] Physical Button 1 and Button 4 drive the simulated route via the domain relay.
- [ ] Real base stays isolated from simulation `/cmd_vel`.
- [ ] Existing manual drive verified in IDLE and inhibited during PATROL.
- [ ] GitHub remote created/selected, commit pushed.
- [ ] Pi map/waypoint deployment and Nav2 obstacle behavior verified.

## Primary implementation references

- [ROBOTIS OpenCR setup and supported Waffle/Waffle Pi sketch](https://emanual.robotis.com/docs/en/platform/turtlebot3/opencr_setup/)
- [OpenCR official repository](https://github.com/ROBOTIS-GIT/OpenCR/tree/68ec75d8a400949580ecf263e0105ea9743b878e)
- [TurtleBot3 2.3.6 source](https://github.com/ROBOTIS-GIT/turtlebot3/tree/da785b7201d317e6e2a662e41bb3d3fd50ebd503)
- [ROS 2 `domain_bridge` usage and configuration](https://github.com/ros2/domain_bridge)
