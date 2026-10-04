# TurtleBot3 Auto Pilot

ROS 2 Jazzy 기반 TurtleBot3 Waffle Pi 반복 순찰 프로젝트다. GitHub repository는
`auto-pilot`이며, simulator 검증은 완료했고 Raspberry Pi 4와 실제 로봇의 통합
시험은 남아 있다.

## 기능 및 검증 상태

- 데스크톱 Gazebo에서 키보드 `1`은 START, `4`는 즉시 STOP이다.
- 공통 순찰 코어는 `/odom` 거리와 orientation을 사용해 1m 직진 후 오른쪽 90°를
  반복한다. 시간으로 이동거리나 회전량을 계산하지 않는다.
- STOP은 zero velocity를 발행하고 `STOPPING → IDLE`로 돌아온다. STOP 뒤 다시
  시작할 수 있으며 monitor가 현재/목표 거리, 각도, 속도 및 loop count를 표시한다.
- Simulation에서 연속 두 loop, 직진 0.995–1.000m, 회전 89.5–89.8°,
  FORWARD/TURN_RIGHT 중 STOP 및 재시작을 확인했다. `colcon test`: 20 passed,
  1 skipped.
- 실제 대상은 TurtleBot3 Waffle Pi, Raspberry Pi 4, OpenCR, LDS-03,
  RC-100 + BT-410이다. OpenCR RC-100 연동 patch는 준비되어 있지만 Button 1/4,
  실제 이동 정확도, manual-control 복귀는 Pi/로봇에서 검증해야 한다.

## 개발 환경과 패키지

- Ubuntu 24.04 amd64, ROS 2 Jazzy
- Pi target: Ubuntu 24.04, ROS 2 Jazzy, TurtleBot3 2.3.6 계열
- `src/turtlebot_patrol`: 공통 controller/monitor와 데스크톱 keyboard node
- `launch/patrol_sim.launch.py`: Gazebo/RViz/keyboard/controller/monitor
- `launch/patrol_robot.launch.py`: 실물 controller/monitor만 실행; Gazebo와 keyboard는
  시작하지 않는다.
- `firmware/patches/`, `tools/`: pinned OpenCR/TurtleBot3 패치 및 Pi overlay build

## 데스크톱 빌드 및 시뮬레이션

ROS 2 Jazzy와 데스크톱 의존성을 먼저 설치한다. 새 PC에서는 ROS apt repository를
설정한 뒤 `tools/install_desktop_dependencies.sh`를 사용한다. 이 설치 스크립트는
Gazebo 등 데스크톱 패키지를 설치하므로 Raspberry Pi에서는 실행하지 않는다.

```bash
cd <workspace>
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

시뮬레이터:

```bash
export TURTLEBOT3_MODEL=waffle_pi
ros2 launch turtlebot_patrol demo.launch.py
```

launch terminal에 포커스를 둔 채 `1`로 반복 순찰을 시작하고 `4`로 정지한다.
자세한 GUI 조작과 문제 해결은 [한국어 시뮬레이터 안내서](SIMULATOR_GUIDE_KO.md)를
참고한다. `/cmd_vel`은 simulator에서 `geometry_msgs/msg/TwistStamped`를 사용한다.

## Raspberry Pi 4 배포

Pi에 Gazebo나 desktop dependency를 설치하지 않는다. 먼저 저장공간을 확인한다.
최소 1–2GB 여유를 확보하고, 가능하면 3GB 이상을 권장한다.

```bash
df -h /
cd ~
git clone https://github.com/<GITHUB_OWNER>/auto-pilot.git
cd ~/auto-pilot
tools/pi4_build_overlay.sh
```

Overlay script는 TurtleBot3 `2.3.6` host node를 sparse clone하고 RC-100 host patch와
patrol package를 overlay로 빌드한다. `rosdep`에서 요구하는 런타임 개발 의존성은
설치되며 Gazebo는 포함되지 않는다.

먼저 bringup terminal에서:

```bash
source /opt/ros/jazzy/setup.bash
source ~/tb3_patrol_overlay_ws/install/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
export LDS_MODEL=LDS-03
ros2 launch turtlebot3_bringup robot.launch.py
```

두 번째 terminal에서 bringup을 확인한다. 알려진 Pi 환경에서는 아래 node가
실행된다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/tb3_patrol_overlay_ws/install/setup.bash
ros2 node list
ros2 topic list
ros2 topic type /cmd_vel
ros2 topic type /odom
```

node 목록에서 `/turtlebot3_node`, `/diff_drive_controller`, `/lidar_node`를
확인하고, topic 목록에서 `/cmd_vel`, `/odom`, `/scan`을 확인한다.

`/cmd_vel`의 실제 type이 `geometry_msgs/msg/TwistStamped`이면:

```bash
ros2 launch turtlebot_patrol patrol_robot.launch.py \
  cmd_vel_type:=geometry_msgs/msg/TwistStamped
```

실제 type이 `geometry_msgs/msg/Twist`이면:

```bash
ros2 launch turtlebot_patrol patrol_robot.launch.py \
  cmd_vel_type:=geometry_msgs/msg/Twist
```

controller는 두 message type을 모두 지원하지만, robot launch의 type은 활성
TurtleBot3 subscriber와 일치시켜야 한다. 실물 launch는 목표거리 1m와 90°를
유지하면서 직진속도 0.05m/s, 회전 최대속도 0.4rad/s로 제한한다. Desktop의 빠른
시뮬레이션 속도는 실물 launch에 적용하지 않는다.

## 실제 로봇 시험 순서

1. Bringup 후 `/turtlebot3_node`, drive controller, lidar node와 `/cmd_vel`, `/odom`,
   `/scan`을 확인한다. 실제 graph 결과를 기준으로 `cmd_vel_type`을 선택한다.
2. 바퀴 주변을 비우고 로봇을 들어 올리거나 평탄한 시험공간에서 시작한다. 즉시
   수동 정지할 RC/전원 차단 수단을 준비한다.
3. RC 방향키 수동주행을 확인한 뒤 patrol controller를 실행한다.
4. Button 1 START, 실측 1m 직진과 90° 우회전을 확인하고 Button 4 STOP을 시험한다.
5. STOP 후 RC 방향키 manual-control 복귀를 확인한 뒤 Button 1/4 transport와 반복
   loop를 시험한다.

Pi 4, 실제 1m 이동거리, 실제 90° 각도, RC Button 1/4, manual-control 복귀는 아직
하드웨어에서 검증되지 않았다. simulation 성공을 실물 검증 완료로 간주하지 않는다.

## Python requirements

`requirements.txt`는 pip 패키지만 나열한다. ROS 2, Gazebo, TurtleBot3, colcon 같은
system package는 Ubuntu/ROS apt와 위 스크립트로 설치한다.
