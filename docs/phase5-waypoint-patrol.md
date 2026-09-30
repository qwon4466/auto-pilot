# Phase 5: Nav2 waypoint 반복 순찰

## 구현

- `patrol_plan.py`가 YAML의 시작 위치와 비어 있지 않은 waypoint 목록을 불러오고 x/y/yaw의 유한 수치 여부를 검증한다.
- `patrol_controller.py`는 `BasicNavigator`의 `followWaypoints()`에 `PoseStamped` 목록을 전달한다. 모든 waypoint가 성공하면 cycle 수를 증가시키고 처음 waypoint부터 새 task를 제출한다.
- Nav2가 active가 되기 전에는 START task를 제출하지 않는다. task가 실패하면 ERROR 상태로 전환하고 zero velocity를 발행한다.
- `[waypoints.yaml]`(../src/turtlebot_patrol/config/waypoints.yaml)은 현재 로봇 시작 위치에 가까운 0.6 m 정사각 순찰 경로를 담는다. 실제 맵을 만든 뒤 좌표를 조정한다.
- `patrol_sim.launch.py`는 Waffle Pi Gazebo world, TurtleBot3 공식 Nav2 launch, waypoint controller를 함께 실행한다. Gazebo/RViz와 Nav2는 `use_sim_time=true`로 동작한다.

## 시뮬레이션 검증

수동 검증용 임시 설정으로 다음 네 점을 실행했다.

```text
P1 (-1.4, -0.5) → P2 (-1.4, 0.1) → P3 (-2.0, 0.1) → P4 (-2.0, -0.5)
```

Nav2 로그에서 각 점이 순서대로 성공했고, P4 이후 `Patrol cycle 1 completed`와 cycle 2의 첫 FollowWaypoints goal을 확인했다. 이때 localization map 및 LDS scan obstacle layer가 활성화됐다. 임시 waypoint YAML은 `/tmp/tb3_short_waypoints.yaml`이었다. 현재 기본 설정도 이 검증 경로로 맞췄다.

## 실행

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
ros2 launch turtlebot_patrol patrol_sim.launch.py
```

The launch assigns the Gazebo/Nav2 ROS nodes to domain 42 to keep optional
communication with the physical TurtleBot3 isolated. In separate test terminals,
set `export ROS_DOMAIN_ID=42` before using `ros2 topic pub` or other CLI commands.
The domain relay is disabled by default.

다른 설정 파일을 사용하려면 `waypoints_file:=/absolute/path/waypoints.yaml` launch argument를 준다. 별도 터미널에서:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
ros2 topic pub --once /patrol_command std_msgs/msg/String "{data: START}"
```

실제 순찰 완료 검증에서는 START 뒤 두 번째 cycle이 시작됐다. 이어서 STOP을 보내 취소 결과를 확인했다.
