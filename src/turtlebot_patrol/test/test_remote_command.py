"""Tests for parsing the mock and remote patrol commands."""

from turtlebot_patrol.patrol_state import PatrolEvent
from turtlebot_patrol.remote_command import parse_command


def test_commands_are_case_and_whitespace_insensitive():
    assert parse_command(' START ') is PatrolEvent.START
    assert parse_command('stop') is PatrolEvent.STOP
    assert parse_command('Reset') is PatrolEvent.RESET


def test_unknown_command_is_rejected():
    assert parse_command('PAUSE') is None
