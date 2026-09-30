# Phase 7: 순찰 상태 monitor

`patrol_controller`는 현재 상태를 `/patrol_state` (`std_msgs/msg/String`), 성공적으로 완료한 전체 cycle 수를 `/patrol_cycle_count` (`std_msgs/msg/UInt32`)로 발행한다. 두 topic은 transient-local QoS를 사용해 늦게 시작한 monitor도 마지막 상태와 count를 받을 수 있다.

`patrol_monitor` 노드는 두 topic을 구독하고 변경 때마다 다음 형식으로 로그를 출력한다.

```text
Patrol state: PATROL | completed cycles: 0
Patrol state: PATROL | completed cycles: 1
Patrol state: IDLE | completed cycles: 1
```

`patrol_sim.launch.py`는 controller와 monitor를 함께 실행한다. 별도 실행은 다음과 같다.

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run turtlebot_patrol patrol_monitor
```

테스트용 `patrol_state_node`와 연결해 initial `IDLE/0`, mock START의 PATROL, STOP 후 IDLE을 monitor 로그에서 확인했다. Gazebo/RViz는 map, robot pose, Nav2 visualization을 보여 주고 console monitor는 상태와 cycle count를 제공한다.
