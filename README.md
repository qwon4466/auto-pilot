# TurtleBot3 Waffle Pi 반복 순찰

ROS 2 Jazzy 프로젝트다. 공통 `patrol_controller`는 `/odom` 거리와 quaternion yaw를
사용해 1m 직진 후 우측 90도 회전을 반복한다. 데스크톱 Gazebo에서는 키보드
`1`이 START, `4`가 STOP이고, 실물 Waffle Pi에서는 준비된 OpenCR/host 확장이
RC-100 Button 1/4 이벤트를 같은 `/patrol_command`로 연결한다. 실제 OpenCR
firmware는 아직 빌드·플래시·실기 검증이 필요하다.

## Desktop quickstart

실제 workspace 위치는 `~/bellingham`이다.

```bash
cd ~/bellingham
source /opt/ros/jazzy/setup.bash
rosdep check --from-paths src --ignore-src
colcon build --symlink-install
source install/setup.bash
ros2 launch turtlebot_patrol demo.launch.py
```

한 launch에서 Gazebo, RViz, controller, keyboard node, monitor를 실행한다.
launch 터미널에 포커스를 둔 채 `1`로 시작하고 `4`로 정지한다. 상세 설치,
화면 조작, topic과 문제 해결은 [한국어 시뮬레이터 안내서](SIMULATOR_GUIDE_KO.md)를
참조한다.

ROS/Gazebo 등 시스템 의존성은 `tools/install_desktop_dependencies.sh`가 Ubuntu
APT로 설치한다. `requirements.txt`는 pip 설치 가능한 Python 패키지만 열거하며
ROS 패키지를 설치하지 않는다.

## Patrol behavior

- IDLE에서 START를 받으면 `FORWARD`로 전환한다.
- `/odom`으로 1.0m 이동량을 측정한 뒤 `TURN_RIGHT`에서 -π/2 yaw 회전을 측정한다.
- 네 번의 직진과 회전이 끝나면 loop count를 올리고 다음 loop를 시작한다.
- STOP은 즉시 zero `TwistStamped`를 발행한 뒤 `STOPPING → IDLE`로 복귀한다.
- 중복 START는 무시한다. odometry가 stale 되거나 motion safety timeout에 도달하면
  ERROR로 가며 로봇 정지 명령을 낸다.

시뮬레이션은 ROS domain 42, 실물 TurtleBot은 기본 domain 0을 사용한다. 실제 RC를
시뮬레이터에 연결하는 optional bridge는 `/patrol_command`와 `/patrol_state`만
전달하며 `/cmd_vel`, `/odom`, `/scan`, `/tf`는 전달하지 않는다.

## Verification and deployment

현재 workspace에서 빌드와 테스트가 통과했다. 개발 PC Gazebo에서 키보드 시작/정지,
1.0m 이동(실측 0.995–1.000m), 90도 회전(실측 89.5–89.8°), monitor, 두 번의
연속 loop count 증가, FORWARD/TURN_RIGHT 중 STOP, STOP 후 재시작을 확인했다.
직진속도는 0.05→0.15m/s, 회전 최대속도는 0.4→0.8rad/s로 조정했으며 목표에
가까우면 0.12rad/s로 감속한다. ROS 테스트는 20개 통과, 1개 skip이다. RC host
patch는 pinned TurtleBot3 2.3.6 source에서 컴파일했다. OpenCR firmware 빌드/플래시,
Pi 배포, 실물 RC/manual-control 회귀시험은 남아 있다.

- [Phase 9–12 controller 및 Raspberry Pi 절차](docs/phase9-12-controller-test.md)
- [전체 진행 기록과 실행 요약](PROJECT_SUMMARY_AND_RUNBOOK.txt)
- [OpenCR/host patch 적용 스크립트](tools/apply_phase9_patches.sh)
- [실제 robot launch](src/turtlebot_patrol/launch/patrol_robot.launch.py)
