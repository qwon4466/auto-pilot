# Phase 1: 개발 환경 점검

점검일: 2026-09-30 (Asia/Seoul)

상태: 완료. ROS/Jazzy, TurtleBot3/Nav2, RViz/Gazebo, ROS 통신, rosdep 데이터베이스를 확인했다.

## 실제 점검 결과

| 항목 | 결과 | 판정 |
| --- | --- | --- |
| OS | Ubuntu 24.04.3 LTS, noble | ROS 2 Jazzy 지원 환경 |
| 아키텍처 | x86_64 / amd64 | Jazzy deb 지원 |
| Python | 3.12.3 | 설치됨 |
| Git | 2.43.0 | 설치됨 |
| VS Code | 1.138.0, `/snap/bin/code`, x64 | 버전 확인 |
| 로케일 | `LANG=ko_KR.UTF-8`, `LC_ALL=C.UTF-8` | UTF-8 사용 가능 |
| Ubuntu Universe | `ubuntu.sources`의 Components에 포함 | 활성화됨 |
| Ubuntu updates/security | noble-updates, noble-security 포함 | 설정됨 |
| ROS APT 저장소 | `ros2-apt-source 1.3.0~noble`, noble/main | 등록 및 APT 갱신 완료 |
| ROS 2 Jazzy desktop | `ros-jazzy-desktop 0.11.0-1noble.20260905.070740` | 설치 및 setup 확인 통과 |
| colcon / rosdep | `python3-colcon-common-extensions 0.3.0-100`, `python3-rosdep 0.27.0-1` | 설치와 명령 경로 확인 통과 |
| TurtleBot3 | core 2.3.6, simulations 2.3.7, msgs 2.4.0 설치됨 | 설치 및 모델 prefix 확인 통과 |
| Nav2 / Simple Commander | Navigation2, Nav2 bringup, Simple Commander 1.3.13 | 설치 및 `BasicNavigator` import 통과 |
| RViz | desktop과 함께 설치됨 | GUI 실행, OpenGL 4.5 확인 |
| Gazebo | `gz sim --versions` → 8.15.0 | Waffle Pi world GUI, 모델 생성 및 `/clock`, `/odom`, `/scan` 확인 |
| 디스크 | 루트 99GB, 최근 확인 시 가용 약 42GB | 확인됨 |
| 메모리 | RAM 7.7GiB, Swap 3.8GiB | 시뮬레이션 실행 후 부하 확인 필요 |
| 그래픽 세션 | Wayland, `DISPLAY=:0` | GUI 세션 존재; 렌더링은 미검증 |
| 현재 작업 폴더 | `~/bellingham` | 작업 시작 시 비어 있었음 |
| ROS workspace 및 저장소 | `~/bellingham` | Phase 2 package scaffold 생성/빌드 확인 |
| 시스템 설치 권한 | `sudo -n true` → `sudo: a password is required` | 사용자 터미널에서 인증 필요 |

Python, Git, VS Code는 추가 설치가 필요하지 않다. ROS 설치 권한 부족은 OS 비호환 문제가 아니다.

## APT 갱신 및 설치 의존성 확인

사용자가 실행한 `sudo apt update`에서 ROS 저장소의 noble 목록을 가져왔으며 다운로드/서명 오류가 없었다. 갱신은 약 11분 27초가 걸렸다. `150 패키지를 업그레이드할 수 있습니다`는 갱신 실패가 아닌 업데이트 알림이다.

로컬 `apt-cache policy`로 다음 후보를 재확인했다.

| 패키지 | 설치 후보 |
| --- | --- |
| ros-jazzy-desktop | 0.11.0-1noble.20260905.070740 |
| ros-dev-tools | 1.0.3 |
| python3-colcon-common-extensions | 0.3.0-100 |
| python3-rosdep | 0.27.0-1 |

`apt-get -s install ros-jazzy-desktop ros-dev-tools` 의존성 검사는 종료 코드 0으로 통과했다. 계획은 3개 업그레이드, 1022개 신규 설치, 제거 0개이다. colcon, rosdep, RViz도 의존성에 포함되어 있다. 이 검사는 실제 설치가 아니다. 계획 기록: `/tmp/turtlebot_patrol_phase1/jazzy-install-plan.txt`.

사용자가 desktop, dev tools, colcon, rosdep 설치를 완료했다. `dpkg-query`에서 모두 `install ok installed`였고, setup 이후 `ROS_DISTRO=jazzy`, RViz prefix `/opt/ros/jazzy`, 명령 경로 `/opt/ros/jazzy/bin/ros2`, `/usr/bin/colcon`, `/usr/bin/rosdep`를 확인했다.

설치 전에 `apt-get -s install` 의존성 검사는 5개 업그레이드, 276개 신규 설치, 제거 0개로 통과했다. 사용자는 Nav2 및 Gazebo 연동용 `ros-gz-sim`, `ros-gz-bridge` 설치를 완료했다. 당시 계획 파일은 `/tmp/turtlebot_patrol_phase1/nav2-install-plan.txt`다.

사용자는 위 Nav2 세 패키지, `ros-jazzy-ros-gz-sim`, `ros-jazzy-ros-gz-bridge`를 설치했다. `nav2_bringup` prefix는 `/opt/ros/jazzy`이며 `BasicNavigator` import가 성공했다. `gz sim --versions`는 `8.15.0`을 출력했다.

설치 후보는 core `2.3.6-1noble.20260907.024758`, bringup `2.3.6-1noble.20260905.072136`, navigation2 `2.3.6-1noble.20260907.024720`, messages `2.4.0-1noble.20260902.041925`, simulation meta `2.3.7-1noble.20260905.090529`, Gazebo `2.3.7-1noble.20260905.085915`였다. ROS Jazzy에서 시뮬레이션 패키지 버전은 TurtleBot3 core와 다르다. 공식 git tag core `2.3.6` 및 simulation `2.3.7` commit을 확인했다. 설치 전 `apt-get -s install ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-simulations` 계획은 28개 신규 설치, 제거 0개로 통과했다. 사용자는 TurtleBot3 설치와 Waffle Pi Gazebo 검증을 완료했다. 당시 계획 파일은 `/tmp/turtlebot_patrol_phase1/turtlebot3-install-plan.txt`다.

사용자 PC에 TurtleBot3 패키지 설치를 확인했다. `dpkg-query` 버전은 위 후보와 일치했고 bringup, node, navigation, description, Gazebo package prefix 모두 `/opt/ros/jazzy`였다. Waffle Pi world launch 중 `Entity creation successful` 로그와 GUI의 `Gazebo Sim` 창을 확인했다. SDF/QML 경고가 있었으나 GUI와 entity는 정상 실행되었다.

VS Code가 Snap 패키지라 integrated terminal이 Snap GTK 경로 변수를 내보낸다. 기본 launch는 Snap의 `libpthread`를 로드하면서 실패했다. 새 패키지를 설치하지 않고 GTK 관련 변수만 지우고 재실행하자 GUI가 정상 열렸다. 실행 명령은 [설치/실행 안내](phase1-installation.md)에 기록한다.

시뮬레이션에서 `/clock`, `/odom`, `/scan` topic의 실제 메시지와 타입을 확인했다. `/cmd_vel` 타입은 `geometry_msgs/msg/TwistStamped`였다. C++ talker의 `Hello World: 4` 메시지를 Python listener가 받아 ROS 2 통신을 확인했다. RViz GUI도 실행됐으며 로그에 OpenGL 4.5가 표시되었다. 사용한 Gazebo/RViz 프로세스는 확인 후 종료했다.

사용자가 `sudo rosdep init`을 완료하고 `20-default.list` 생성을 확인했다. 이어서 `rosdep update`와 `rosdep db`가 성공했다. `rosdep check --from-paths src --ignore-src`는 새 셸에서 먼저 `source /opt/ros/jazzy/setup.bash`를 실행해야 Jazzy 배포 키를 정상 해석한다. ROS 환경 없이 실행한 첫 확인에서 `launch_ros` 키 오류가 출력됐지만, Jazzy setup 이후 재실행은 `All system dependencies have been satisfied`로 통과했다. VS Code Snap의 GTK 환경 문제는 GUI 프로세스를 시작할 때 관련 변수를 제거해 우회했다.

## 공식 자료 확인

- [ROS 2 Jazzy Ubuntu 설치 문서](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html): Ubuntu Noble 24.04, amd64/arm64 지원 및 `ros2-apt-source` 설치 방식.
- [ROS 공식 문서 저장소의 설치 원문](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Installation/Ubuntu-Install-Debs.rst): 문서 사이트 접근 제한 시 확인할 원문.
- [ROBOTIS PC setup](https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/): Jazzy의 PC 개발 환경, Nav2 및 TurtleBot3 설치.
- [Gazebo 공식 ROS 설치 문서](https://gazebosim.org/docs/harmonic/ros_installation/): Jazzy + Harmonic 조합, `ros-jazzy-ros-gz`를 통한 ROS vendor 패키지 설치.
- [ROS Jazzy 배포 목록](https://github.com/ros/rosdistro/blob/master/jazzy/distribution.yaml): 확인 시 TurtleBot3 release `2.3.6-1`, TurtleBot3 simulations `2.3.7-1`. 배포 등록 버전은 APT 설치 후보 버전과 다를 수 있다.
- [ROBOTIS TurtleBot3 2.3.6 소스](https://github.com/ROBOTIS-GIT/turtlebot3/tree/2.3.6): 공식 태그 확인, commit `da785b7201d317e6e2a662e41bb3d3fd50ebd503`. 이후 통신 구조 분석 기준으로 사용한다.
- [ROBOTIS bringup](https://emanual.robotis.com/docs/en/platform/turtlebot3/bringup/): Jazzy `/cmd_vel`은 `TwistStamped`로 안내된다. 실제 2.3.6 소스 및 Pi topic type과 대조한 뒤 정지 publisher를 구현한다.

공식 OpenCR/RC-100 및 Pi 측 control table 소스 검토 결과는 [Phase 8 공식 소스 분석](phase8-opencr-rc100-analysis.md)에 기록했다. 실기 Pi의 정확한 firmware 설치 버전과 실제 `diff_drive_controller` 연결 상태는 아직 PC에서 확인할 수 없다.

## 준비된 설치 파일

- 원본: [ros-infrastructure 공식 릴리스 1.3.0](https://github.com/ros-infrastructure/ros-apt-source/releases/tag/1.3.0)
- 파일: `/tmp/turtlebot_patrol_phase1/ros2-apt-source_1.3.0.noble_all.deb`
- `dpkg-deb` 확인: Package `ros2-apt-source`, Version `1.3.0~noble`, Architecture `all`
- 로컬 SHA-256: `f31d84adf5054c7d60ded0e82c0f776a77ea33af53d08f40b9ad7c94cca55296`
- GitHub 릴리스 asset의 SHA-256과 로컬 파일 SHA-256 일치 확인.
- 다운로드 및 패키지 메타데이터 확인 성공.
- 사용자 터미널에서 설치 완료. 재점검한 `dpkg-query` 결과: `install ok installed 1.3.0~noble`.

`/tmp` 파일은 재부팅 후 없어질 수 있다. 재다운로드 명령은 설치 안내에 있다.

## 이번 단계의 변경과 검증

1. 변경된 파일: `docs/phase1-environment.md`, `docs/phase1-installation.md`.
2. 구현 내용: 환경 조사와 공식 의존성 확인, 설치 파일 준비. ROS 패키지 구현은 Phase 2 이후다.
3. 실행 명령: [현재 설치 단계](phase1-installation.md)를 따른다.
4. 테스트 방법: ROS 설치, `BasicNavigator` import, Gazebo/RViz GUI, ROS 2 talker-listener, 시뮬레이션 topics, rosdep init/update/db 통과.
5. 결과: rosdep 업데이트 exit 0, Jazzy 인덱스 추가 및 캐시 갱신.
6. Phase 2 진입 조건: 통과. Python package scaffold 생성과 build로 이어갔다.

## Phase 1 완료 조건

- [x] Ubuntu 24.04 / amd64 확인
- [x] UTF-8 및 Universe 설정 확인
- [x] Python / Git / VS Code 확인
- [x] 디스크 및 GUI 세션 확인
- [x] ROS APT 저장소 설정 패키지 설치
- [x] `apt update` 성공 및 Jazzy 설치 후보 확인
- [x] ROS 2 Jazzy desktop, colcon, rosdep 설치 확인
- [x] Nav2 및 `BasicNavigator` import 성공
- [x] TurtleBot3 패키지 설치 버전 기록 (core 2.3.6, sim 2.3.7)
- [x] Gazebo CLI 버전 및 ROS bridge 설치 확인
- [x] ROS C++ talker / Python listener 통신 성공
- [x] RViz / Gazebo 창 및 Waffle Pi spawn 확인
- [x] `sudo rosdep init` 및 `rosdep update` (`rosdep db` 확인 포함)

순찰 START/STOP, waypoint 이동, RC-100, 실제 `/odom` 및 `/scan`, 장애물 회피는 아직 테스트하지 않았다. 해당 항목은 이후 Phase에서 검증한다.
