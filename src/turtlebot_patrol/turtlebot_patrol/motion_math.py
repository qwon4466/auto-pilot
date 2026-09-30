"""Small geometry helpers for odometry-driven patrol motion."""

import math


def normalize_angle(angle: float) -> float:
    """Wrap an angle in radians to [-pi, pi]."""
    return math.atan2(math.sin(angle), math.cos(angle))


def quaternion_to_yaw(x: float, y: float, z: float, w: float) -> float:
    """Extract planar yaw from an orientation quaternion."""
    sin_yaw = 2.0 * (w * z + x * y)
    cos_yaw = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(sin_yaw, cos_yaw)


def planar_distance(start_x: float, start_y: float, x: float, y: float) -> float:
    """Return Euclidean planar displacement from a segment's start pose."""
    return math.hypot(x - start_x, y - start_y)


def right_turn_progress(start_yaw: float, current_yaw: float) -> float:
    """Return non-negative clockwise yaw progress with wrap-around handled."""
    return max(0.0, -normalize_angle(current_yaw - start_yaw))
