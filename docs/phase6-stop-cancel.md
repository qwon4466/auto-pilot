# Phase 6: STOP 즉시 취소와 정지

`PatrolController`는 `PATROL` 중 STOP을 받으면 `STOPPING`으로 바꾸고 `BasicNavigator.cancelTask()`를 기다린 뒤 `geometry_msgs/msg/TwistStamped`의 0속도 명령을 `/cmd_vel`에 발행한다. 취소가 끝난 뒤 `TASK_CANCELLED`를 적용해 `IDLE`로 돌아간다. IDLE STOP과 중복 START는 상태 머신에서 무시한다. Ctrl+C 종료 시에도 진행 중인 Nav2 task를 취소하고 0속도를 발행한다.

Gazebo 테스트 중 두 번째 FollowWaypoints task에서 STOP을 보냈다. 상태 topic은 `STOPPING`, `IDLE`을 발행했고 로그에는 `Canceling current task`, Nav2 action cancel success, `TASK_CANCELLED: STOPPING -> IDLE`가 기록됐다. 이전 mock velocity echo에서도 STOP 직후 zero `TwistStamped`를 확인했다.

실제 OpenCR에서는 RC 방향키 속도가 `/cmd_vel`과 합산되므로 host의 zero command만으로 RC 누적 속도가 없어지지 않는다. 실기 STOP이 완전한 정지가 되려면 Phase 9의 OpenCR/`turtlebot3_node` 확장에서 RC 속도 clear/override 정책도 구현하고 실제 Waffle Pi에서 확인해야 한다.
