# Phase 8: 공식 OpenCR / RC-100 소스 분석

검토일: 2026-09-30

이 검토를 먼저 수행한 뒤 상태 머신 코드를 작성한다. firmware 및 `turtlebot3_node` 패치는 아직 없다.

## 검토한 공식 버전

- ROBOTIS TurtleBot3 tag `2.3.6`, commit `da785b7201d317e6e2a662e41bb3d3fd50ebd503`
- ROBOTIS OpenCR commit `68ec75d8a400949580ecf263e0105ea9743b878e`
- ROBOTIS Dynamixel2Arduino tag `0.6.1`, commit `06c06f94edfc749749ee33396e4166873df9833e`; OpenCR's `turtlebot3.h` says this firmware requires Dynamixel2Arduino 0.6.1 or newer.
- OpenCR sparse checkout에는 `RC100`과 `turtlebot3_ros2` 공식 라이브러리 경로만 포함했다.

## RC-100 수신 및 버튼 의미

`RC100.h`의 공식 상수는 U/D/L/R=`1/2/4/8`, 버튼 1–6=`16/32/64/128/256/512`다. 따라서 우측 1번은 mask `16`, 우측 4번은 mask `128`이다. 펌웨어 파서는 `0xFF 0x55` 헤더, 값과 bitwise complement 쌍 두 개를 검사하고 완전한 6-byte 프레임에 대해서만 `available()`을 true로 반환한다. 이 값들은 구현 전 실제 RC-100/BT-410 입력으로도 확인해야 한다.

## 현재 수동조작 경로 및 상호작용

`Turtlebot3Controller::getRCdata()`는 RC frame을 받았을 때 방향키 U/D/L/R로 누적 속도를 조정하고, `6`은 일정 직진 속도를, `5`는 RC 속도를 0으로 만든다. 현재 코드는 RC 버튼 1–4를 이동 동작에 사용하지 않는다. RC 입력 속도와 ROS `/cmd_vel` 속도는 OpenCR `update_goal_velocity_from_3values()`에서 더해진다. 따라서 host에서 Navigation2 task를 취소하고 `/cmd_vel=0`을 발행하는 것만으로는 이미 누적된 OpenCR RC 속도가 제거되지 않는다. STOP 완료 조건에는 OpenCR RC 속도 처리까지 포함해야 한다.

기존 방향키 분기와 모터 제어 구조는 보존한다. Button 1/4는 별도 이벤트로 전달하고, 기존 방향키 수동주행은 IDLE에서 그대로 유지한다. PATROL 중 수동 방향키 충돌 정책은 구현 전에 명확히 해야 한다. host가 RC 이벤트를 보기 전에 OpenCR에서 이미 적용될 수 있으므로 단순 ROS topic relay만으로 자동 취소와 수동 우선권을 보장하지 못한다.

## 기존 OpenCR ↔ ROS 2 통신

Pi의 `turtlebot3_node`는 OpenCR의 DYNAMIXEL2Arduino `Slave` control table을 USB serial로 읽고 쓴다. ROS 쪽에서 `init_read_memory()`는 address 10부터 182까지의 기존 영역을 요청한다. `/cmd_vel`은 현재 구성에서 `TwistStamped`도 지원하며, 선속도 x와 각속도 z를 기존 cmd velocity control items에 기록한다. 기존 외부 control table에는 RC-100 input field가 없고, node는 RC button event topic을 publish하지 않는다.

기존 테이블의 주소 간격이 있다고 해서 임의로 새 주소를 사용하지 않는다. DYNAMIXEL2Arduino의 address registration/read semantics를 확인하고, 해당 영역이 정상적으로 읽히는지 OpenCR firmware 빌드 및 실제 serial 검증을 통과한 뒤에만 새 control item을 확정한다. 최소 확장 후보는 firmware 내부에서 RC button 1/4 이벤트를 기존 control table 경로로 전달하고, ROS node에서 이를 새 ROS command interface로 발행하는 것이다. 실제 주소, 이벤트 유지/소비 방식, 중복 방지 sequence 또는 latch 처리 방식은 transport 구현 단계에서 검증하여 결정한다.

검토한 DYNAMIXEL2Arduino 0.6.1의 `Slave::processInstRead()`는 요청한 구간과 완전히 포함되는 등록 item의 바이트를 응답에 복사하고, 그 외 바이트는 0으로 채운다. `processInstWrite()`도 요청 구간에 완전히 포함되는 등록 item에 기록한다. 그러므로 Pi host가 이미 읽는 10–182 구간 안 주소라도 OpenCR 쪽에 새 item을 등록해야 값이 전달된다. `addControlItem()`은 중복 item overlap을 거부하고, `CONTROL_ITEM_MAX`는 OpenCR 빌드에서 128이다. 실제 주소 선택 전에 기존 양쪽 테이블의 전체 점유 구간과 host의 수신 데이터 매핑을 맞춰야 한다.

## 구현 결정과 미해결 검증

1. patrol 상태 로직과 mock START/STOP은 RC transport와 독립적으로 구현한다.
2. STOP은 `cancelTask()`와 0속도 발행을 실행하고, 향후 OpenCR RC 속도도 초기화/억제하는 경로를 추가해야 완성이다.
3. 버튼 1/4 이벤트는 OpenCR firmware → 기존 DYNAMIXEL slave table → `turtlebot3_node` → `/patrol_command`로 확장한다. 임의 serial protocol은 추가하지 않는다.
4. firmware와 ROS node는 사용자가 설치한 TurtleBot3 2.3.6과 일치하는 소스로 패치하고, OpenCR build/flash 및 Pi 실기 검증 전까지 RC 연동 완료로 표시하지 않는다.
5. Waffle Pi에 설치된 실제 OpenCR firmware 버전/variant, serial 장치 권한과 연결, Pi의 Nav2 및 `diff_drive_controller` 연결은 사용자가 실기 배포 시 확인해야 한다.

## 공식 소스

- [TurtleBot3 2.3.6 `turtlebot3_node.cpp`](https://github.com/ROBOTIS-GIT/turtlebot3/blob/da785b7201d317e6e2a662e41bb3d3fd50ebd503/turtlebot3_node/src/turtlebot3.cpp)
- [TurtleBot3 2.3.6 external control table](https://github.com/ROBOTIS-GIT/turtlebot3/blob/da785b7201d317e6e2a662e41bb3d3fd50ebd503/turtlebot3_node/include/turtlebot3_node/control_table.hpp)
- [OpenCR `RC100.h`](https://github.com/ROBOTIS-GIT/OpenCR/blob/68ec75d8a400949580ecf263e0105ea9743b878e/arduino/opencr_arduino/opencr/libraries/RC100/RC100.h)
- [OpenCR RC100 parser](https://github.com/ROBOTIS-GIT/OpenCR/blob/68ec75d8a400949580ecf263e0105ea9743b878e/arduino/opencr_arduino/opencr/libraries/RC100/RC100.cpp)
- [OpenCR `getRCdata()`](https://github.com/ROBOTIS-GIT/OpenCR/blob/68ec75d8a400949580ecf263e0105ea9743b878e/arduino/opencr_arduino/opencr/libraries/turtlebot3_ros2/src/turtlebot3/turtlebot3_controller.cpp)
- [OpenCR TurtleBot3 control table and velocity sum](https://github.com/ROBOTIS-GIT/OpenCR/blob/68ec75d8a400949580ecf263e0105ea9743b878e/arduino/opencr_arduino/opencr/libraries/turtlebot3_ros2/src/turtlebot3/turtlebot3.cpp)
- [Dynamixel2Arduino 0.6.1 Slave control table](https://github.com/ROBOTIS-GIT/Dynamixel2Arduino/blob/06c06f94edfc749749ee33396e4166873df9833e/src/utility/slave.cpp)
