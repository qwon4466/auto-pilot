"""Translate text commands into patrol state-machine events."""

from turtlebot_patrol.patrol_state import PatrolEvent


def parse_command(command: str) -> PatrolEvent | None:
    """Return the matching event for a supported command, if any."""
    normalized = command.strip().upper()
    commands = {
        'START': PatrolEvent.START,
        'STOP': PatrolEvent.STOP,
        'RESET': PatrolEvent.RESET,
    }
    return commands.get(normalized)
