# Phase 2: ROS workspace and package scaffold

## Workspace

The repository root `~/bellingham` is also the ROS 2 workspace root. ROS packages live under `src/`; generated `build/`, `install/`, and `log/` files are ignored by Git.

```text
bellingham/
├── .gitignore
├── docs/
└── src/
    └── turtlebot_patrol/
        ├── package.xml
        ├── setup.py
        ├── setup.cfg
        ├── resource/turtlebot_patrol
        └── turtlebot_patrol/__init__.py
```

## Scaffold created

`turtlebot_patrol` is an `ament_python`, package format 3 package. Its initial manifest declares the ROS runtime dependencies needed for upcoming stages: `rclpy`, `std_msgs`, `geometry_msgs`, `nav_msgs`, `sensor_msgs`, `nav2_simple_commander`, `ament_index_python`, `launch`, `launch_ros`, and `python3-yaml`.

This phase adds packaging metadata only. The patrol state machine, command nodes, YAML settings, launch files, monitoring and RC integration are left for their corresponding phases after the official control path review.

## Validation

Commands, from the workspace root:

```bash
source /opt/ros/jazzy/setup.bash
rosdep update
rosdep check --from-paths src --ignore-src
colcon build --symlink-install
source install/setup.bash
ros2 pkg prefix turtlebot_patrol
```

Results:

- `rosdep update`: exit code 0; Jazzy was added and the cache was updated.
- `rosdep check`: after sourcing `/opt/ros/jazzy/setup.bash`, `All system dependencies have been satisfied`. An unsourced shell did not know the `launch_ros` rosdep key.
- `colcon build --symlink-install`: one package finished successfully, no warnings on the final run.
- Package prefix: `~/bellingham/install/turtlebot_patrol`.

The first generated manifest used an invalid placeholder maintainer email and colcon warned during package discovery. The XML and setuptools metadata now use the configured Git maintainer identity; a clean rebuild completed without that warning.

## Files changed

- Added the ament Python package scaffold under `src/turtlebot_patrol/`.
- Added `.gitignore` entries for generated ROS build output, Python cache files, and local VS Code settings.
- Added this phase record.

## Next phase gate

The official source review is recorded in [Phase 8 analysis](phase8-opencr-rc100-analysis.md). Phase 3 will define the patrol states and transitions; keep RC transport and the existing manual drive mapping separate from the state machine.
