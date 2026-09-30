# TurtleBot3 Waffle Pi Patrol

ROS 2 Jazzy package for repeating a configured Nav2 waypoint route on a TurtleBot3 Waffle Pi. RC-100 Button 1 requests START and Button 4 requests STOP. The existing RC direction-key mapping remains available while the robot is IDLE; firmware suppresses those manual velocity contributions while PATROL owns motion.

The mock command path and Gazebo simulation run on Ubuntu 24.04. Optional hardware input forwards only `/patrol_command` from the physical robot's ROS domain to an isolated simulation domain. The reverse bridge forwards only `/patrol_state` so the OpenCR can suppress manual wheel input during PATROL. Simulator `/cmd_vel` is never bridged to the physical robot's ROS domain.

## Current status

Phases 1–8 are complete and recorded under `docs/`. Phase 9 source patches are prepared for the official OpenCR and TurtleBot3 2.3.6 repositories. The ROS package, simulation, tests, and domain-separated RC workflow are in progress. The OpenCR patch still requires compilation and flashing, and the host node patch requires an overlay build on the Raspberry Pi before the real RC-100 can be tested. GitHub remote setup and Pi deployment are tracked in Phase 11 and 12.

Do not treat RC hardware integration or physical robot STOP behavior as validated until the patched firmware is compiled, flashed, and tested on the actual Waffle Pi.

## Build and test on the desktop

```bash
cd ~/bellingham
source /opt/ros/jazzy/setup.bash
rosdep check --from-paths src --ignore-src
colcon build --symlink-install
source install/setup.bash
colcon test --packages-select turtlebot_patrol
colcon test-result --verbose
```

The desktop already has ROS 2 Jazzy, Nav2, TurtleBot3 simulation, Gazebo Sim 8, and RViz. Install `ros-jazzy-domain-bridge` only if using the physical RC-100 input path:

```bash
sudo apt install ros-jazzy-domain-bridge
```

## Run the Gazebo patrol

One terminal:

```bash
cd ~/bellingham
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
ros2 launch turtlebot_patrol patrol_sim.launch.py
```

The launch starts the Waffle Pi world, the official TurtleBot3 Navigation2 launch, the patrol controller, and the console monitor. The simulator uses ROS domain 42 by default. In a second terminal, send mock commands in that domain:

```bash
source /opt/ros/jazzy/setup.bash
source ~/bellingham/install/setup.bash
export ROS_DOMAIN_ID=42
ros2 topic pub --once /patrol_command std_msgs/msg/String "{data: START}"
ros2 topic pub --once /patrol_command std_msgs/msg/String "{data: STOP}"
```

To use a different route, pass an absolute YAML path:

```bash
ros2 launch turtlebot_patrol patrol_sim.launch.py waypoints_file:=/absolute/path/waypoints.yaml
```

The default route is a 0.6 m square in the stock Gazebo world. Real deployment coordinates must be measured in the actual map frame.

If Gazebo's GTK plugins conflict with the VS Code Snap environment, start the launch with the inherited GTK variables cleared:

```bash
env -u GTK_PATH -u GTK_EXE_PREFIX -u GTK_MODULES \
  -u GDK_PIXBUF_MODULEDIR -u GDK_PIXBUF_MODULE_FILE \
  -u GTK_IM_MODULE_FILE -u GIO_MODULE_DIR \
  ros2 launch turtlebot_patrol patrol_sim.launch.py
```

## Use the RC-100 connected to the physical robot

The physical TurtleBot3 is in ROS domain 0 by default; the desktop simulation is in domain 42. The launch's optional bridge forwards `/patrol_command` from the robot domain to the simulator and `/patrol_state` back to the robot. It does not bridge velocity, odometry, scan, or TF topics.

After applying and deploying the Phase 9 OpenCR and TurtleBot3 node patches, build the simulation on the desktop with the bridge enabled:

```bash
source /opt/ros/jazzy/setup.bash
source ~/bellingham/install/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
ros2 launch turtlebot_patrol patrol_sim.launch.py enable_rc100_bridge:=true robot_domain_id:=0 simulation_domain_id:=42
```

On the Raspberry Pi, keep the normal TurtleBot3 ROS graph in domain 0, install the patched `turtlebot3_node` overlay, and start normal bringup. The host node publishes RC commands in domain 0 and subscribes to the bridged patrol state. Do not start the PC simulation in domain 0: Nav2 velocity commands must remain isolated from the robot hardware.

While the bridged simulator state is PATROL, the patched OpenCR ignores RC direction-key velocity contributions. Direction-key manual control remains enabled in IDLE. Button 4 is the intended stop control. This policy has not been validated on the physical robot yet.

## Topics

| Topic | Type | Purpose |
| --- | --- | --- |
| `/patrol_command` | `std_msgs/msg/String` | START, STOP, RESET |
| `/patrol_state` | `std_msgs/msg/String` | IDLE, PATROL, STOPPING, ERROR |
| `/patrol_cycle_count` | `std_msgs/msg/UInt32` | Number of successful complete waypoint loops |
| `/cmd_vel` | `geometry_msgs/msg/TwistStamped` | Nav2 velocity command (simulation domain only during PC testing) |

The monitor currently displays state and completed cycle count. Current pose and current/next waypoint dashboard fields are not implemented.

## Source patches and deployment

The exact upstream revisions and apply/build instructions are in `docs/phase9-12-controller-test.md`. Patches are stored under `firmware/patches/` and can be applied with:

```bash
tools/apply_phase9_patches.sh /path/to/OpenCR /path/to/turtlebot3-2.3.6
```

The script rejects source revisions that do not match the reviewed official commits. Phase 10–12 documentation covers manual-control policy, GitHub setup, and Raspberry Pi overlay deployment. No GitHub remote is configured yet.

## Project records

- `PROJECT_SUMMARY_AND_RUNBOOK.txt`: consolidated project status and user runbook
- `docs/phase1-installation.md`: environment setup
- `docs/phase2-package.md` through `docs/phase7-monitor.md`: ROS package and simulation milestones
- `docs/phase8-opencr-rc100-analysis.md`: official source audit and RC transport findings
- `docs/phase9-12-controller-test.md`: source patches, domain isolation, controller test, GitHub and Pi deployment steps
- `tools/pi4_build_overlay.sh`: build a minimal Pi overlay with the patched TurtleBot3 host node
- `tools/compile_opencr.sh`: compile the patched Waffle/Waffle Pi sketch without flashing
