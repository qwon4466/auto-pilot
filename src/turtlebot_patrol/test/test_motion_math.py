"""Tests for angle wrapping and odometry orientation conversion."""

import math

from turtlebot_patrol.motion_math import (
    normalize_angle,
    planar_distance,
    quaternion_to_yaw,
    right_turn_progress,
)


def test_normalize_angle_wraps_across_positive_pi():
    wrapped = normalize_angle(math.radians(-179.0) - math.radians(179.0))

    assert math.isclose(wrapped, math.radians(2.0), abs_tol=1e-9)


def test_normalize_angle_wraps_across_negative_pi():
    wrapped = normalize_angle(math.radians(179.0) - math.radians(-179.0))

    assert math.isclose(wrapped, math.radians(-2.0), abs_tol=1e-9)


def test_quaternion_to_yaw_for_right_angle():
    angle = -math.pi / 2.0

    yaw = quaternion_to_yaw(0.0, 0.0, math.sin(angle / 2.0), math.cos(angle / 2.0))

    assert math.isclose(yaw, angle, abs_tol=1e-9)


def test_planar_distance_is_euclidean():
    assert math.isclose(planar_distance(0.0, 0.0, 0.09, 0.12), 0.15)


def test_right_turn_progress_wraps_across_negative_pi():
    progress = right_turn_progress(math.radians(-179.0), math.radians(179.0))

    assert math.isclose(progress, math.radians(2.0), abs_tol=1e-9)
