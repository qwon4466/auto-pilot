# Phase 3: 순찰 상태 머신

## 동작

`turtlebot_patrol/patrol_state.py`에는 ROS와 Navigation2에 독립적인 순수 상태 머신을 추가했다.

| 현재 상태 | 이벤트 | 다음 상태 | 의미 |
| --- | --- | --- | --- |
| IDLE | START | PATROL | 순찰 시작 요청 수락 |
| PATROL | START | PATROL | 중복 시작 무시 |
| PATROL | STOP | STOPPING | 취소 및 정지 처리 대기 |
| IDLE | STOP | IDLE | 무동작 |
| STOPPING | TASK_CANCELLED | IDLE | 작업 취소 완료 |
| PATROL / STOPPING | TASK_FAILED | ERROR | Nav 작업 오류 |
| ERROR | RESET | IDLE | 오류 상태 초기화 |

상태 전이는 부작용 없이 `StateTransition`으로 보고된다. 따라서 후속 ROS 노드는 PATROL 진입 때 waypoint task를 한 번만 시작하고, STOPPING 진입 때 cancel/zero-velocity 동작을 수행할 수 있다. `ERROR`에서 START를 무시하며 RESET이 필요하다.

## 변경 파일

- `src/turtlebot_patrol/turtlebot_patrol/patrol_state.py`
- `src/turtlebot_patrol/test/test_patrol_state.py`
- `docs/phase3-state-machine.md`

## 검증

```bash
source /opt/ros/jazzy/setup.bash
python3 -m pytest -q src/turtlebot_patrol/test/test_patrol_state.py
colcon build --symlink-install
```

테스트는 START 중복, IDLE STOP, STOPPING 완료, task failure 및 reset을 검증한다. 이 단계에서는 아직 ROS 입력, Nav2 task, 속도 publish, 순찰 반복을 연결하지 않는다.

패키지 테스트 결과: `colcon test --packages-select turtlebot_patrol` 성공. 총 6개, 실패 0개이며, 생성 scaffold의 copyright 확인은 헤더 미설정으로 skip 처리됐다.
