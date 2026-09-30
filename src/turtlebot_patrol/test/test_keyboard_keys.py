"""Tests for top-row and numeric keypad command decoding."""

from turtlebot_patrol.keyboard_keys import extract_patrol_keys


def test_top_row_and_numlock_keys_are_recognized():
    keys, remaining = extract_patrol_keys('1x4')

    assert keys == ['1', '4']
    assert remaining == ''


def test_xterm_keypad_sequences_are_recognized_across_reads():
    keys, remaining = extract_patrol_keys('\x1bO')
    assert keys == []
    assert remaining == '\x1bO'

    keys, remaining = extract_patrol_keys(remaining + 'q\x1bOt')
    assert keys == ['1', '4']
    assert remaining == ''
