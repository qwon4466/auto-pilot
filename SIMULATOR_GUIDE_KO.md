# TurtleBot3 반복 순찰 시뮬레이터 사용 설명서

이 시뮬레이터는 실제 TurtleBot3 Waffle Pi와 RC-100 없이 Ubuntu 데스크톱에서
반복 순찰 제어를 확인하기 위한 개발 환경이다. Gazebo의 Waffle Pi가 `/odom`을
내고, 공통 `patrol_controller`가 `/cmd_vel`을 발행한다. 키보드 `1`은 시작,
`4`는 정지다. 기본 동작은 `/odom`에서 측정한 약 15cm 전진과 quaternion yaw로
계산한 오른쪽 90도 회전을 네 번 이어 작은 사각 경로 한 바퀴를 만든다.

## 1. 준비 환경과 설치 확인

이 workspace는 현재 `~/bellingham`에 있다. 지시서 예시의
`~/turtlebot_patrol_ws`는 이 컴퓨터의 실제 경로와 다르다.

- Ubuntu 24.04 amd64
- ROS 2 Jazzy
- TurtleBot3 Waffle Pi Gazebo 모델
- Gazebo Sim Harmonic (현재 확인 버전 8.15.0)
- RViz2
- `colcon`, `rosdep`

새 터미널에서 ROS가 설치됐는지 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
echo "$ROS_DISTRO"
ros2 pkg prefix turtlebot3_gazebo
ros2 pkg prefix rviz2
gz sim --versions
```

정상이라면 `jazzy`, ROS 패키지 경로 `/opt/ros/jazzy`, Gazebo 8.x 버전이
표시된다. 의존성을 다시 설치해야 하는 새 데스크톱에서는 ROS Jazzy APT 저장소를
먼저 설정한 뒤 다음 설치 스크립트를 실행한다.

```bash
cd ~/bellingham
./tools/install_desktop_dependencies.sh
```

`requirements.txt`는 pip 설치 가능한 Python 패키지 목록이다. ROS, Gazebo,
Nav2, TurtleBot3, colcon 같은 시스템 패키지는 pip로 설치되지 않으므로 APT
설치 스크립트를 사용한다.

## 2. 빌드와 환경 적용

프로젝트 루트에서 dependency를 확인하고 빌드한다.

```bash
cd ~/bellingham
source /opt/ros/jazzy/setup.bash
rosdep check --from-paths src --ignore-src
colcon build --symlink-install
source install/setup.bash
```

`rosdep check`가 모두 충족됐고 `colcon build`가 성공해야 실행할 수 있다. 소스
파일을 변경한 뒤에는 다시 `colcon build --symlink-install`하고 새 셸마다
`source` 두 줄을 실행한다.

## 3. 시뮬레이터 실행: 터미널 하나

VS Code 통합 터미널이나 일반 Ubuntu 터미널 한 개에서 다음을 실행한다.

```bash
cd ~/bellingham
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
ros2 launch turtlebot_patrol demo.launch.py
```

이 launch 하나가 Gazebo world와 Waffle Pi, `/odom`·`/scan`·`/cmd_vel` bridge,
공통 patrol controller, 키보드 입력, Patrol Monitor, RViz를 시작한다. 처음에는
Gazebo와 RViz 준비에 시간이 걸릴 수 있다. 터미널에 keyboard 메뉴와 controller의
`Ready` 로그가 나오면 입력할 준비가 된 것이다.

VS Code가 Snap으로 설치되어 있고 Gazebo GUI가 GTK 관련 오류로 열리지 않을 때는
같은 명령의 앞에 `env -u` 옵션을 넣는다.

```bash
env -u GTK_PATH -u GTK_EXE_PREFIX -u GTK_MODULES \
  -u GDK_PIXBUF_MODULEDIR -u GDK_PIXBUF_MODULE_FILE \
  -u GTK_IM_MODULE_FILE -u GIO_MODULE_DIR \
  ros2 launch turtlebot_patrol demo.launch.py
```

직접 호출하고 싶다면 `ros2 launch turtlebot_patrol patrol_sim.launch.py`도 동일한
시뮬레이션을 실행한다. 기본 시뮬레이션 ROS domain은 `42`다. 실제 로봇의 기본
domain `0`과 분리해 PC의 Nav2/시뮬레이션 속도 명령이 실물 로봇에 도달하지 않게
한다. 이 patrol demo는 직접 `/odom` 제어를 하므로 다른 Nav2 또는 teleop
controller를 같은 `/cmd_vel`에 동시에 연결하지 않는다.

## 4. 키보드로 순찰 조작

launch를 실행한 **터미널에 포커스를 둔 상태로** 키를 누른다. Gazebo 또는 RViz
창에 포커스가 있으면 해당 창 단축키로 처리되어 keyboard node에 전달되지 않을
수 있다.

- 상단 숫자열 `1` 또는 NumLock이 켜진 숫자패드 `1`: 순찰 시작
- 상단 숫자열 `4` 또는 NumLock이 켜진 숫자패드 `4`: 즉시 정지
- NumLock이 꺼져 숫자패드가 방향키를 보내는 경우에는 상단 숫자열을 사용한다.
- 순찰 중 `1`을 다시 눌러도 두 번째 controller/task를 만들지 않고 무시한다.
- `4`는 FORWARD와 TURN_RIGHT 어느 단계에서 눌러도 zero velocity를 발행하고
  IDLE로 복귀한다. 그 뒤 `1`을 다시 누르면 새 patrol이 시작된다.
- 실행 중 Ctrl+C는 keyboard node를 통해 demo launch 전체를 종료한다.

키 입력 로그 예시는 다음과 같다.

```text
[INPUT] KEY 1
[PATROL] START REQUEST
[PATROL] START: IDLE -> FORWARD
[MOTION] FORWARD #1: target 0.150 m
```

STOP 시에는 아래와 같은 상태 로그가 나온다.

```text
[PATROL] STOP REQUEST RECEIVED
[MOTION] Publishing zero velocity
[PATROL] FORWARD -> STOPPING
[PATROL] PATROL STOPPED: STOPPING -> IDLE
```

## 5. 화면에서 확인할 항목

### Gazebo

- 로봇은 world 바닥 위에 spawn된다. 본체의 앞쪽이 로봇 전방이며 기준 전진축은
  base의 +X 방향이다.
- Gazebo Harmonic 기본 카메라 조작: 마우스 왼쪽 드래그는 장면 이동(pan),
  오른쪽 드래그 또는 휠은 확대/축소, 휠 버튼 드래그 또는 Shift+왼쪽 드래그는
  시점 회전이다.
- 화면 아래 World Control의 Play/Pause 버튼으로 시뮬레이션을 일시정지하거나
  다시 진행한다. 일시정지 중에는 Gazebo 시간이 멈춘다. 재개하면 `/odom` 기반
  제어도 이어진다.
- 로봇이 15cm 정도 직진한 다음 우측으로 90도 회전하는지 확인한다. 네 번의
  전진·회전 후 원점 근처를 지나며 다음 loop를 계속 시작한다.

마우스 조작 및 Play/Pause 위치는 Gazebo Harmonic GUI에 따르며, 화면 배치가
다르면 [Gazebo GUI 안내](https://gazebosim.org/docs/harmonic/gui/)를 참고한다.

### RViz

RViz는 `odom`을 Fixed Frame으로 사용하며 다음 display를 미리 켜 둔다.

- **RobotModel**: TurtleBot3 모델과 링크 배치
- **TF**: `odom`, `base_link`, laser frame 등 좌표계
- **Odometry**: `/odom` 위치·방향 화살표
- **LaserScan**: `/scan` LDS-03 거리점
- **Patrol Path**: 순찰 중 odometry로 기록한 `/patrol_path` 궤적

RViz Display 목록에서 각 항목의 체크를 끄거나 켤 수 있다. Fixed Frame이
`odom`인지 확인한다. 센서가 시작되는 동안 TF timestamp 경고가 잠시 나올 수
있으며, 정상 수신 후에도 계속 표시가 비어 있으면 `/odom`, `/scan`, `/tf`를
확인한다.

## 6. Patrol Monitor와 ROS topic

demo launch 안에서 Patrol Monitor가 1초마다 상태를 출력한다. 확인할 값은 mode,
FORWARD/TURN_RIGHT state, input device, last command, 현재/목표 이동거리, 현재/목표
회전각, loop count, odom x/y/yaw다. 이동거리와 각도는 `/odom`을 기준으로 바뀐다.

| Topic | Type | 의미 |
| --- | --- | --- |
| `/cmd_vel` | `geometry_msgs/msg/TwistStamped` | 로봇 속도 명령. 시뮬레이터 domain에서만 제어 |
| `/odom` | `nav_msgs/msg/Odometry` | 거리와 yaw 계산의 입력 |
| `/scan` | `sensor_msgs/msg/LaserScan` | Gazebo LDS-03 거리 센서 |
| `/patrol_command` | `std_msgs/msg/String` | `START`, `STOP`, `RESET` 명령 |
| `/patrol_state` | `std_msgs/msg/String` | `IDLE`, `FORWARD`, `TURN_RIGHT`, `STOPPING`, `ERROR` |
| `/patrol_telemetry` | `std_msgs/msg/String` | 현재 상태·거리·각도·loop 등의 JSON 요약 |
| `/patrol_cycle_count` | `std_msgs/msg/UInt32` | 완성된 15cm × 15cm 사각 loop 수 |
| `/patrol_path` | `nav_msgs/msg/Path` | 현재 순찰에서 기록한 odometry 궤적 |

토픽을 별도 터미널에서 볼 경우 시뮬레이션 domain을 설정한다.

```bash
source /opt/ros/jazzy/setup.bash
source ~/bellingham/install/setup.bash
export ROS_DOMAIN_ID=42
ros2 topic echo /patrol_state
```

한 번만 상태/거리 측정 정보를 확인하려면 다른 토픽을 선택한다.

```bash
ros2 topic echo /patrol_telemetry
ros2 topic hz /odom
ros2 topic info /cmd_vel --verbose
```

보조 터미널에서 키보드 node를 따로 띄우고 싶다면 동일한 domain에서 아래를
실행한다. 통합 demo에서 이미 keyboard node가 실행 중이면 별도 입력 node를
추가하지 않는다.

```bash
ROS_DOMAIN_ID=42 ros2 run turtlebot_patrol keyboard_control
```

수동 topic 명령으로도 controller를 시험할 수 있다.

```bash
ROS_DOMAIN_ID=42 ros2 topic pub --once /patrol_command std_msgs/msg/String "{data: START}"
ROS_DOMAIN_ID=42 ros2 topic pub --once /patrol_command std_msgs/msg/String "{data: STOP}"
```

## 7. 동작 설정과 허용오차

기본 목표는 0.150m 전진, 우측 π/2 rad 회전이다. 기본 속도는 직선 0.05m/s,
회전 0.4rad/s이며, 움직임 완료 여부를 시간으로 환산하지 않는다. 완료 판단은
`/odom` 거리와 quaternion에서 계산한 yaw 차이로 한다. 기본 완료 허용오차는
전진 0.005m, 회전 약 0.035rad다. `odom_timeout_sec`와 `phase_timeout_sec`은
센서 고장·움직임 정체에 대한 안전 timeout이며 목표 이동량을 정하는 데 사용하지
않는다. Gazebo를 Pause하면 simulation clock도 멈추므로 timeout도 정지한다.

설정 값을 바꾸려면 controller parameter override를 launch에 전달하도록
`patrol_sim.launch.py`를 수정하거나 ROS parameter service를 사용할 수 있다.
실제 Pi에서 값을 변경하기 전에 저속의 안전한 시험 공간에서 확인한다.

## 8. 문제 해결

- `ROS_DISTRO`가 비어 있거나 `ros2: command not found`: 새 터미널에서
  `source /opt/ros/jazzy/setup.bash`를 실행한다.
- `Package 'turtlebot_patrol' not found`: workspace 루트에서 빌드한 다음
  `source install/setup.bash`를 실행한다.
- Gazebo 또는 RViz가 열리지 않음: VS Code Snap GTK 변수 해제 명령을 사용하고,
  `gz sim --versions`, `ros2 pkg prefix turtlebot3_gazebo`, `ros2 pkg prefix rviz2`를
  확인한다.
- `START rejected: waiting for a fresh /odom message`: Gazebo world가 실행됐는지,
  `/odom` topic에 메시지가 있는지 확인한다. 준비 후 `1`을 다시 누른다.
- 키보드가 반응하지 않음: launch 터미널에 포커스를 둔다. GUI 창은 키를 받지
  않는다. 숫자패드 사용 시 NumLock을 켜거나 상단 숫자키를 누른다.
- 이동 중 `ERROR`: `/odom`이 끊겼거나 한 단계가 안전 제한시간 내 끝나지 않은
  것이다. 원인을 해결한 뒤 `ros2 topic pub --once /patrol_command
  std_msgs/msg/String "{data: RESET}"`로 초기화하고 다시 시작한다.
- `/cmd_vel` subscriber가 없음: Gazebo bridge가 뜨는 로그를 확인하고
  `ros2 topic info /cmd_vel --verbose`를 확인한다.
- RC bridge 사용 중에는 Pi domain과 simulator domain이 달라야 한다. 기본은 Pi
  `0`, desktop `42`이며 `/cmd_vel`, `/odom`, `/scan`, `/tf`는 두 domain 사이에서
  전달하지 않는다.

## 9. 현재 검증 범위

개발 PC Gazebo에서 키보드 `1`/`4`, 0.15m odometry 이동, 약 90도 yaw 회전,
FORWARD와 TURN_RIGHT 중 STOP, 중복 START 무시, restart, 네 변 후 LOOP 1 및
Monitor 값을 확인했다. RC-100 host patch는 pinned TurtleBot3 source에서 빌드했다.

실제 OpenCR firmware compile/flash, Pi에서의 bringup, RC Button 1/4 및 방향키
manual-control 회귀시험은 아직 실제 로봇에서 검증되지 않았다. 따라서 이 안내는
데스크톱 시뮬레이터 사용법이며, 실제 로봇에 배포 완료했다는 의미는 아니다.
실물에서는 평탄하고 장애물이 없는 시험 공간과 물리적인 비상정지 수단을 준비하고
RC/manual 동작을 먼저 확인한다. 자세한 실제 장비 절차는
[Phase 9–12 controller 안내](docs/phase9-12-controller-test.md)를 따른다.
