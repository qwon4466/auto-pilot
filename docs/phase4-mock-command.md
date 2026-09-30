# Phase 4: Mock START / STOP 명령

`patrol_state_node`는 `/patrol_command`의 `std_msgs/msg/String`을 받아 Phase 3 상태 머신에 전달하고, 현재 상태를 `/patrol_state`로 발행한다. 명령은 대소문자와 앞뒤 공백을 무시한다. 허용 값은 `START`, `STOP`, `RESET`이며 알 수 없는 명령은 경고 후 무시한다.

## 실행과 확인

터미널 1:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run turtlebot_patrol patrol_state_node
```

터미널 2:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 topic echo /patrol_state
```

터미널 3:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic pub --once /patrol_command std_msgs/msg/String "{data: START}"
ros2 topic pub --once /patrol_command std_msgs/msg/String "{data: STOP}"
```

상태 topic에서 `PATROL` 다음 `STOPPING`, `IDLE`을 확인한다. START를 두 번 보내도 `PATROL` 상태가 유지된다. 현재는 Nav2와 연결 전이므로 STOPPING을 거쳐 곧 IDLE로 전이하며, 실제 task 취소와 zero velocity는 Nav2 연결 단계에서 구현한다. 이 노드는 실기 이동 기능이 아니다.

## 변경 및 검증

- 추가: `remote_command.py`, `patrol_state_node.py`, `test_remote_command.py`, 본 문서
- 변경: `setup.py`에 `patrol_state_node` console script 등록
- 단위 테스트: command parsing, 상태 전이 테스트
- ROS 통합 확인: `patrol_state_node`를 실행해 START가 `IDLE → PATROL`, STOP이 `PATROL → STOPPING → IDLE`을 발행함을 확인했다.
- 패키지 검증: 전체 테스트 8개 통과, 실패 0개 (생성 scaffold copyright 1개 skip).
