"""Load and validate patrol poses from a YAML configuration file."""

import math
from pathlib import Path

import yaml


def load_patrol_plan(path: str | Path) -> tuple[dict[str, float], list[dict[str, float]]]:
    """Return validated initial pose and ordered waypoint dictionaries."""
    with Path(path).open(encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError('Patrol YAML root must be a mapping')

    initial_pose = _pose(config.get('initial_pose'), 'initial_pose')
    waypoints = config.get('waypoints')
    if not isinstance(waypoints, list) or not waypoints:
        raise ValueError('waypoints must be a non-empty list')

    return initial_pose, [
        _pose(item, f'waypoints[{index}]') for index, item in enumerate(waypoints)
    ]


def _pose(value: object, name: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f'{name} must be a mapping with x, y, and yaw')

    pose: dict[str, float] = {}
    for axis in ('x', 'y', 'yaw'):
        try:
            coordinate = float(value[axis])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f'{name}.{axis} must be a finite number') from error
        if not math.isfinite(coordinate):
            raise ValueError(f'{name}.{axis} must be a finite number')
        pose[axis] = coordinate
    return pose
