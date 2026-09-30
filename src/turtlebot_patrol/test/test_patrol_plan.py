"""Tests for patrol configuration loading and validation."""

from pathlib import Path

import pytest

from turtlebot_patrol.patrol_plan import load_patrol_plan


def test_default_plan_has_four_finite_waypoints():
    config = Path(__file__).parents[1] / 'config' / 'waypoints.yaml'

    initial_pose, waypoints = load_patrol_plan(config)

    assert initial_pose == {'x': -2.0, 'y': -0.5, 'yaw': 0.0}
    assert len(waypoints) == 4


def test_load_patrol_plan(tmp_path):
    config = tmp_path / 'waypoints.yaml'
    config.write_text(
        'initial_pose: {x: -2, y: -0.5, yaw: 0}\n'
        'waypoints:\n  - {x: 1, y: 2, yaw: 1.57}\n',
        encoding='utf-8',
    )

    initial_pose, waypoints = load_patrol_plan(config)

    assert initial_pose == {'x': -2.0, 'y': -0.5, 'yaw': 0.0}
    assert waypoints == [{'x': 1.0, 'y': 2.0, 'yaw': 1.57}]


def test_reject_empty_waypoint_list(tmp_path):
    config = tmp_path / 'waypoints.yaml'
    config.write_text(
        'initial_pose: {x: 0, y: 0, yaw: 0}\nwaypoints: []\n',
        encoding='utf-8',
    )

    with pytest.raises(ValueError, match='non-empty'):
        load_patrol_plan(config)


def test_reject_non_finite_pose_values(tmp_path):
    config = tmp_path / 'waypoints.yaml'
    config.write_text(
        'initial_pose: {x: .nan, y: 0, yaw: 0}\n'
        'waypoints:\n  - {x: 1, y: 2, yaw: 0}\n',
        encoding='utf-8',
    )

    with pytest.raises(ValueError, match='finite'):
        load_patrol_plan(config)
