"""Tests for the pure patrol state machine."""

from turtlebot_patrol.patrol_state import (
    PatrolEvent,
    PatrolState,
    PatrolStateMachine,
)


def test_start_is_accepted_once():
    machine = PatrolStateMachine()

    started = machine.handle(PatrolEvent.START)
    duplicate = machine.handle(PatrolEvent.START)

    assert started.current is PatrolState.PATROL
    assert started.changed
    assert duplicate.current is PatrolState.PATROL
    assert not duplicate.changed


def test_stop_transitions_through_stopping_to_idle():
    machine = PatrolStateMachine()
    machine.handle(PatrolEvent.START)

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
