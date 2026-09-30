"""Console dashboard for odometry-based patrol state and progress."""

import json
import math
from typing import Any

from nav_msgs.msg import Odometry
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String, UInt32

from turtlebot_patrol.motion_math import quaternion_to_yaw


class PatrolMonitor(Node):
    """Display command source, motion progress, odometry, and loop count."""

    def __init__(self) -> None:
        super().__init__('patrol_monitor')
        self.declare_parameter('state_topic', '/patrol_state')
        self.declare_parameter('cycle_count_topic', '/patrol_cycle_count')
        self.declare_parameter('telemetry_topic', '/patrol_telemetry')
        self.declare_parameter('odom_topic', '/odom')
        self._state = 'UNKNOWN'
        self._cycle_count = 0
        self._telemetry: dict[str, Any] = {}
        self._odom = (None, None, None)
        status_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._state_sub = self.create_subscription(
            String,
            self.get_parameter('state_topic').value,
            self._on_state,
            status_qos,
        )
        self._cycle_sub = self.create_subscription(
            UInt32,
            self.get_parameter('cycle_count_topic').value,
            self._on_cycle_count,
            status_qos,
        )
        self._telemetry_sub = self.create_subscription(
            String,
            self.get_parameter('telemetry_topic').value,
            self._on_telemetry,
            status_qos,
        )
        self._odom_sub = self.create_subscription(
            Odometry,
            self.get_parameter('odom_topic').value,
            self._on_odom,
            20,
        )
        self._display_timer = self.create_timer(1.0, self._display_status)

    def _on_state(self, message: String) -> None:
        self._state = message.data

    def _on_cycle_count(self, message: UInt32) -> None:
        self._cycle_count = message.data

    def _on_telemetry(self, message: String) -> None:
        try:
            value = json.loads(message.data)
        except json.JSONDecodeError:
            self.get_logger().warning('Ignoring malformed /patrol_telemetry JSON')
            return
        if isinstance(value, dict):
            self._telemetry = value

    def _on_odom(self, message: Odometry) -> None:
        position = message.pose.pose.position
        orientation = message.pose.pose.orientation
        yaw = quaternion_to_yaw(
            orientation.x, orientation.y, orientation.z, orientation.w)
        self._odom = (position.x, position.y, yaw)

    def _display_status(self) -> None:
        data = self._telemetry
        mode = str(data.get('mode', 'UNKNOWN'))
        source = str(data.get('input_device', 'UNKNOWN'))
        command = str(data.get('last_command', 'NONE'))
        phase = str(data.get('state', self._state))
        phase_number = int(data.get('phase_number', 0))
        target_distance = float(data.get('target_distance', 0.15))
        current_distance = float(data.get('current_distance', 0.0))
        target_turn = math.degrees(float(data.get('target_turn', math.pi / 2.0)))
        current_turn = math.degrees(float(data.get('current_turn', 0.0)))
        x, y, yaw = self._odom
        pose_lines = (
            f'X             : {x:.3f}\nY             : {y:.3f}\n'
            f'YAW           : {math.degrees(yaw):.1f} deg'
            if x is not None and y is not None and yaw is not None
            else 'Waiting for /odom'
        )
        text = (
            '========================================\n'
            ' TurtleBot Patrol Monitor\n'
            '========================================\n'
            f'MODE          : {mode}\n'
            f'STATE         : {phase}\n'
            f'INPUT DEVICE  : {source}\n'
            f'LAST COMMAND  : {command}\n'
            f'FORWARD       : #{phase_number} | {current_distance:.3f} / '
            f'{target_distance:.3f} m\n'
            f'TURN RIGHT    : {current_turn:.1f} / {target_turn:.1f} deg\n'
            f'LOOP COUNT    : {self._cycle_count}\n'
            'ODOM\n'
            f'{pose_lines}\n'
            '========================================'
        )
        self.get_logger().info(f'\n{text}')


def main(args=None) -> None:
    """Start the patrol monitor console node."""
    rclpy.init(args=args)
    node = PatrolMonitor()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
