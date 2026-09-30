# Phase 1: 단계별 설치 안내

대상은 현재 Ubuntu 24.04 amd64 데스크탑이다. Pi4용 최소 런타임 설치 절차는 Phase 12에서 별도로 작성한다.

설치 명령은 한 단계씩 실행하고 바로 확인한다. 오류가 나면 해당 단계에서 원인을 해결한 뒤 계속한다.

Phase 1 완료 (2026-09-30). `rosdep init`, `rosdep update`, `rosdep db`, Gazebo/RViz GUI 및 ROS 통신 검증이 통과했다. Phase 2 package scaffold/build 결과는 [Phase 2 기록](phase2-package.md)에 정리한다.

## 완료한 단계: TurtleBot3 및 시뮬레이션 설치

사용자의 package prefix 결과와 `dpkg-query`를 확인했다. TurtleBot3 core/bringup/node/description/navigation 2.3.6, simulation/Gazebo 2.3.7, messages 2.4.0 설치가 통과했다. 의존성 계획은 28개 신규 패키지, 제거 0개였다.

PC 터미널에서 실행한다.

```bash
sudo apt install ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-simulations
```

설치가 끝난 후 패키지 상태를 확인한다.

```bash
dpkg-query -W -f='${Package} ${Status} ${Version}\n' ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-bringup ros-jazzy-turtlebot3-node ros-jazzy-turtlebot3-description ros-jazzy-turtlebot3-navigation2 ros-jazzy-turtlebot3-simulations ros-jazzy-turtlebot3-gazebo ros-jazzy-turtlebot3-msgs
```

모든 패키지에서 `install ok installed`여야 한다. core 및 bringup은 2.3.6, simulation과 Gazebo는 2.3.7, messages는 2.4.0 계열이다.

같은 터미널에서 setup을 읽고 Gazebo 및 로봇 모델 package prefix를 확인한다.

```bash
source /opt/ros/jazzy/setup.bash
ros2 pkg prefix nav2_bringup
ros2 pkg prefix turtlebot3_gazebo
ros2 pkg prefix turtlebot3_description
gz sim --versions
```

실제 결과: prefix 세 곳은 `/opt/ros/jazzy`, Gazebo는 `8.15.0`을 출력했다.

Waffle Pi world launch 중 VS Code Snap에서 물려받은 GTK 경로로 Gazebo GUI가 시작되지 않았다. GTK 관련 환경 변수를 제거하자 GUI가 열렸고 `Entity creation successful`을 확인했다. 다음은 GUI를 여는 명령이다.

```bash
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
env -u GTK_PATH -u GTK_EXE_PREFIX -u GTK_MODULES -u GDK_PIXBUF_MODULEDIR -u GDK_PIXBUF_MODULE_FILE -u GTK_IM_MODULE_FILE -u GIO_MODULE_DIR ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

이 시뮬레이션에서 `/clock`, `/odom`, `/scan` 메시지를 확인했다. `/cmd_vel`은 `geometry_msgs/msg/TwistStamped`다. C++ talker 메시지를 Python listener가 수신했고 RViz는 OpenGL 4.5로 실행됐다. GUI 검증 뒤 두 프로그램을 종료했다.

## 완료한 단계: Nav2 설치

사용자가 Nav2 세 패키지, `ros-gz-sim`, `ros-gz-bridge` 설치를 마쳤다. 다섯 항목 모두 설치 상태였으며 `nav2_bringup` prefix는 `/opt/ros/jazzy`, `BasicNavigator` import 성공이었다. `gz sim --versions`는 `8.15.0`을 출력했다. 설치 의존성 계획은 5개 업그레이드, 276개 신규 설치, 제거 0개였다.

```bash
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-nav2-simple-commander
```

## 완료한 단계: Jazzy desktop 및 개발 도구 설치

사용자가 실행한 설치 및 확인 결과가 통과했다. desktop, dev tools, colcon, rosdep 모두 `install ok installed`였고 `ROS_DISTRO=jazzy`, RViz prefix `/opt/ros/jazzy`, 명령 경로 `/opt/ros/jazzy/bin/ros2`, `/usr/bin/colcon`, `/usr/bin/rosdep`를 확인했다.

설치 명령:

```bash
sudo apt install ros-jazzy-desktop ros-dev-tools
```

의존성 계획은 3개 업그레이드, 1022개 신규 설치, 제거 0개였다. RViz, colcon 및 rosdep도 사용할 수 있음을 확인했다.

## 완료한 단계: APT 목록 갱신

ROS APT 저장소 등록은 완료했다. PC 터미널에서 실행한다.

```bash
sudo apt update
```

정상 결과는 ROS 저장소의 noble 패키지 목록을 가져오고 패키지 목록 읽기를 완료하는 것이다. `NO_PUBKEY`, `Failed to fetch`, `Err:`, 서명 검증 오류가 있으면 다음 설치 단계로 넘어가지 않는다.

설치 후보 확인:

```bash
apt-cache policy ros-jazzy-desktop
```

예상 결과:

```text
ros-jazzy-desktop:
  Installed: (none)
  Candidate: <버전>
```

`Candidate`가 `(none)`이면 정상 통과가 아니다. 버전 목록에는 ROS 저장소 `packages.ros.org/ros2/ubuntu`의 `noble/main`이 표시되어야 한다.

실제 후보는 `0.11.0-1noble.20260905.070740`이며 ROS noble/main 저장소에서 제공됨을 확인했다. 다운로드 및 서명 오류 없이 갱신을 완료했다. `150 패키지 업그레이드 가능`은 업데이트 알림이다.

## 완료한 단계: ROS APT 저장소 등록

공식 릴리스 파일 다운로드 및 다음 설치 명령 실행을 완료했다.

```bash
sudo dpkg -i /tmp/turtlebot_patrol_phase1/ros2-apt-source_1.3.0.noble_all.deb
```

Ubuntu 비밀번호는 이 명령을 실행한 터미널에 직접 입력한다.

설치 확인:

```bash
dpkg-query -W -f='${Status} ${Version}\n' ros2-apt-source
```

예상 출력:

```text
install ok installed 1.3.0~noble
```

실제 확인 결과가 위 예상 출력과 일치했다.

다운로드 파일이 없을 때만 다음 준비 명령을 각각 실행한다.

```bash
mkdir -p /tmp/turtlebot_patrol_phase1
```

```bash
curl --fail --location --retry 2 --output /tmp/turtlebot_patrol_phase1/ros2-apt-source_1.3.0.noble_all.deb https://github.com/ros-infrastructure/ros-apt-source/releases/download/1.3.0/ros2-apt-source_1.3.0.noble_all.deb
```

메타데이터 확인:

```bash
dpkg-deb -f /tmp/turtlebot_patrol_phase1/ros2-apt-source_1.3.0.noble_all.deb Package Version Architecture
```

예상 출력:

```text
Package: ros2-apt-source
Version: 1.3.0~noble
Architecture: all
```

## 이후 설치 순서

저장소 등록과 APT 갱신은 완료했다. 나머지는 계획이며 아직 설치되지 않았다. 각 단계의 명령은 선행 단계가 통과한 뒤 실행한다.

| 순서 | 설치 / 작업 | 확인 방법 |
| --- | --- | --- |
| 1 (완료) | ROS 저장소 설정 패키지 | 위 `dpkg-query` 결과 통과 |
| 2 (완료) | APT 인덱스 갱신 및 설치 후보 확인 | 서명/저장소 오류 없음, `apt-cache policy` 후보 확인 통과 |
| 3 (완료) | Jazzy desktop, `ros-dev-tools`, colcon, rosdep | 설치 상태와 경로 확인 통과 |
| 4 (완료) | Nav2, bringup, Simple Commander | 설치 상태, prefix, BasicNavigator import 통과 |
| 5 (완료) | TurtleBot3 desktop 및 Gazebo simulation | 설치 버전, prefix, Waffle Pi spawn 확인 |
| 6 (Nav2 의존성으로 설치됨) | Gazebo Harmonic ROS vendor와 bridge | `ros-gz-sim`, `ros-gz-bridge`, `gz sim --versions` 확인 |
| 7 (완료) | rosdep 초기화 / 갱신 | `20-default.list` 생성 확인, `rosdep update` 및 `rosdep db` 통과 |
| 8 (완료) | ROS 통신 및 GUI 시험 | talker/listener, RViz/Gazebo 창, sim topics 확인 |

TurtleBot3 후보가 2.3.6과 다르면 그 버전을 기록하고 공식 2.3.6 소스와 호환성을 확인한다. 기존 Pi 패키지를 자동으로 교체하거나 펌웨어를 덮어쓰지 않는다.

Universe와 UTF-8, curl, CA 인증서, Git, Python, VS Code는 현재 이미 준비되어 있다.

## 공식 근거

- [ROS Jazzy Ubuntu deb 설치](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
- [ros2-apt-source 공식 릴리스](https://github.com/ros-infrastructure/ros-apt-source/releases/tag/1.3.0)
- [ROBOTIS PC setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/)
- [ROBOTIS simulation](https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/)
- [Gazebo와 ROS의 기본 버전 조합 및 vendor 설치](https://gazebosim.org/docs/harmonic/ros_installation/)
