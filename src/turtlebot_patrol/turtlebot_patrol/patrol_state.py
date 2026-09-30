"""Pure patrol state machine, independent of ROS and Navigation2."""

from dataclasses import dataclass
from enum import auto, Enum


class PatrolState(Enum):
    """States used by the patrol controller."""

    IDLE = auto()
    PATROL = auto()
    STOPPING = auto()
    ERROR = auto()


class PatrolEvent(Enum):
    """Events that can change the patrol state."""

    START = auto()
    STOP = auto()
    TASK_CANCELLED = auto()
    TASK_FAILED = auto()
    RESET = auto()


@dataclass(frozen=True)
class StateTransition:
    """Result of applying one event to the state machine."""

    previous: PatrolState
    current: PatrolState
    event: PatrolEvent

    @property
    def changed(self) -> bool:
        """Whether the event changed the current state."""
        return self.previous is not self.current


class PatrolStateMachine:
    """Enforce patrol state transitions without performing side effects."""

    def __init__(self) -> None:
        self._state = PatrolState.IDLE

    @property
    def state(self) -> PatrolState:
        """Return the current patrol state."""
        return self._state

    def handle(self, event: PatrolEvent) -> StateTransition:
        """Apply an event; duplicate or invalid events leave state unchanged."""
        previous = self._state

        if event is PatrolEvent.START and self._state is PatrolState.IDLE:
            self._state = PatrolState.PATROL
        elif event is PatrolEvent.STOP and self._state is PatrolState.PATROL:
            self._state = PatrolState.STOPPING
        elif event is PatrolEvent.TASK_CANCELLED and self._state is PatrolState.STOPPING:
            self._state = PatrolState.IDLE
        elif event is PatrolEvent.TASK_FAILED and self._state in (
            PatrolState.PATROL,
            PatrolState.STOPPING,
        ):
            self._state = PatrolState.ERROR
        elif event is PatrolEvent.RESET and self._state is PatrolState.ERROR:
            self._state = PatrolState.IDLE

        return StateTransition(previous, self._state, event)
