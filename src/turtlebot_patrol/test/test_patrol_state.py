"""Tests for the pure patrol state machine."""

from turtlebot_patrol.patrol_state import (
    PatrolEvent,
    PatrolState,
    PatrolStateMachine,
)


def test_start_is_accepted_once_and_duplicate_is_ignored_in_motion_states():
    machine = PatrolStateMachine()

    started = machine.handle(PatrolEvent.START)
    duplicate = machine.handle(PatrolEvent.START)

    assert started.current is PatrolState.FORWARD
    assert started.changed
    assert duplicate.current is PatrolState.FORWARD
    assert not duplicate.changed

    turning = machine.handle(PatrolEvent.DISTANCE_REACHED)
    ignored_start = machine.handle(PatrolEvent.START)
    assert turning.current is PatrolState.TURN_RIGHT
    assert ignored_start.current is PatrolState.TURN_RIGHT
    assert not ignored_start.changed


def test_stop_transitions_through_stopping_to_idle():
    machine = PatrolStateMachine()
    machine.handle(PatrolEvent.START)

    machine.handle(PatrolEvent.DISTANCE_REACHED)
    stopping = machine.handle(PatrolEvent.STOP)
    repeated_stop = machine.handle(PatrolEvent.STOP)
    stopped = machine.handle(PatrolEvent.TASK_CANCELLED)

    assert stopping.current is PatrolState.STOPPING
    assert repeated_stop.current is PatrolState.STOPPING
    assert not repeated_stop.changed
    assert stopped.current is PatrolState.IDLE


def test_idle_stop_is_ignored_and_task_failure_requires_reset():
    machine = PatrolStateMachine()

    idle_stop = machine.handle(PatrolEvent.STOP)
    assert idle_stop.current is PatrolState.IDLE
    assert not idle_stop.changed

    machine.handle(PatrolEvent.START)
    failed = machine.handle(PatrolEvent.TASK_FAILED)
    ignored_start = machine.handle(PatrolEvent.START)
    reset = machine.handle(PatrolEvent.RESET)

    assert failed.current is PatrolState.ERROR
    assert ignored_start.current is PatrolState.ERROR
    assert reset.current is PatrolState.IDLE


def test_motion_cycles_forward_turn_forward_and_stop_from_either_motion_state():
    machine = PatrolStateMachine()
    assert machine.handle(PatrolEvent.START).current is PatrolState.FORWARD
    assert machine.handle(PatrolEvent.DISTANCE_REACHED).current is PatrolState.TURN_RIGHT
    assert machine.handle(PatrolEvent.TURN_REACHED).current is PatrolState.FORWARD
    assert machine.handle(PatrolEvent.STOP).current is PatrolState.STOPPING
    assert machine.handle(PatrolEvent.TASK_CANCELLED).current is PatrolState.IDLE
