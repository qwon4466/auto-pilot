"""Odometry-controlled 1 m forward and 90 degree right-turn patrol."""

import json
import math
import signal
from typing import Any

from geometry_msgs.msg import PoseStamped, TwistStamped
from nav_msgs.msg import Odometry, Path
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import String, UInt32

from turtlebot_patrol.motion_math import (
    normalize_angle,
    planar_distance,
    quaternion_to_yaw,
    right_turn_progress,
)
from turtlebot_patrol.patrol_state import (
    PatrolEvent,
    PatrolState,
    PatrolStateMachine,
)
from turtlebot_patrol.remote_command import parse_command


class PatrolController(Node):
    """Drive a repeating small square using odometry feedback."""

    def __init__(self) -> None:
        super().__init__('patrol_controller')
        self.declare_parameter('command_topic', '/patrol_command')
        self.declare_parameter('state_topic', '/patrol_state')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('cycle_count_topic', '/patrol_cycle_count')
        self.declare_parameter('telemetry_topic', '/patrol_telemetry')
        self.declare_parameter('input_source_topic', '/patrol_input_source')
        self.declare_parameter('path_topic', '/patrol_path')
        self.declare_parameter('target_distance', 1.0)
        self.declare_parameter('target_turn', math.pi / 2.0)
        self.declare_parameter('linear_speed', 0.15)
        self.declare_parameter('angular_speed', 0.8)
        self.declare_parameter('turn_slow_speed', 0.12)
        self.declare_parameter('turn_slowdown_angle', math.radians(20.0))
        self.declare_parameter('heading_gain', 1.5)
        self.declare_parameter('distance_tolerance', 0.005)
        self.declare_parameter('angle_tolerance', math.radians(0.5))
        self.declare_parameter('odom_timeout_sec', 2.0)
        self.declare_parameter('phase_timeout_sec', 30.0)

        self._machine = PatrolStateMachine()
        self._cycle_count = 0
        self._turn_count = 0
        self._phase_number = 0
        self._current_distance = 0.0
        self._current_turn = 0.0
        self._x: float | None = None
        self._y: float | None = None
        self._yaw: float | None = None
        self._last_odom_clock_ns: int | None = None
        self._phase_started_clock_ns: int | None = None
        self._forward_start: tuple[float, float] | None = None
        self._forward_yaw = 0.0
        self._turn_start_yaw = 0.0
        self._input_device = 'UNKNOWN'
        self._last_command = 'NONE'
        self._commanded_linear_speed = 0.0
        self._commanded_angular_speed = 0.0
        self._path_poses: list[PoseStamped] = []

        self._state_pub = self.create_publisher(
            String, self.get_parameter('state_topic').value, self._status_qos())
        self._cycle_pub = self.create_publisher(
            UInt32, self.get_parameter('cycle_count_topic').value, self._status_qos())
        self._telemetry_pub = self.create_publisher(
            String, self.get_parameter('telemetry_topic').value, self._status_qos())
        self._cmd_vel_pub = self.create_publisher(
            TwistStamped, self.get_parameter('cmd_vel_topic').value, 10)
        self._path_pub = self.create_publisher(
            Path, self.get_parameter('path_topic').value, self._status_qos())
        self._command_sub = self.create_subscription(
            String, self.get_parameter('command_topic').value, self._on_command, 10)
        self._odom_sub = self.create_subscription(
            Odometry, self.get_parameter('odom_topic').value, self._on_odom, 20)
        self._input_source_sub = self.create_subscription(
            String,
            self.get_parameter('input_source_topic').value,
            self._on_input_source,
            10,
        )
        self._control_timer = self.create_timer(1.0 / 30.0, self._control_step)
        self._telemetry_timer = self.create_timer(0.2, self._publish_telemetry)

        self._publish_state()
        self._publish_cycle_count()
        self._publish_telemetry()
        self.get_logger().info(
            'Ready: odometry-controlled 1.000 m forward, then 90 deg right; '
            'four sides per loop')

    @staticmethod
    def _status_qos() -> QoSProfile:
        return QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

    @property
    def _state(self) -> PatrolState:
        return self._machine.state

    def _on_command(self, message: String) -> None:
        event = parse_command(message.data)
        if event is None:
            self.get_logger().warning(f'Ignoring unknown patrol command: {message.data!r}')
            return
        self._last_command = event.name
        if event is PatrolEvent.START:
            self._start_patrol()
        elif event is PatrolEvent.STOP:
            self._stop_patrol()
        elif event is PatrolEvent.RESET and self._state is PatrolState.ERROR:
            self._machine.handle(PatrolEvent.RESET)
            self._publish_state()
            self._publish_telemetry()

    def _start_patrol(self) -> None:
        if self._state in (PatrolState.FORWARD, PatrolState.TURN_RIGHT):
            self.get_logger().info('[PATROL] Already running. START ignored.')
            return
        if self._state is PatrolState.STOPPING:
            self.get_logger().info('[PATROL] STOP is completing. START ignored.')
            return
        if self._state is PatrolState.ERROR:
            self.get_logger().warning('[PATROL] ERROR state; send RESET before START.')
            return
        if not self._odom_is_fresh():
            self.get_logger().error('START rejected: waiting for a fresh /odom message')
            return

        self._turn_count = 0
        self._cycle_count = 0
        self._phase_number = 1
        self._path_poses.clear()
        self._set_forward_origin()
        transition = self._machine.handle(PatrolEvent.START)
        self.get_logger().info(
            f'[PATROL] START: {transition.previous.name} -> {transition.current.name}')
        target_distance = float(self.get_parameter('target_distance').value)
        self.get_logger().info(
            f'[MOTION] FORWARD #1: target '
            f'{target_distance:.3f} m')
        self._publish_state()
        self._publish_cycle_count()
        self._publish_path()
        self._publish_telemetry()

    def _stop_patrol(self) -> None:
        self.get_logger().info('[PATROL] STOP REQUEST RECEIVED')
        self._publish_zero_velocity()
        if self._state is PatrolState.IDLE:
            self.get_logger().info('[PATROL] Already IDLE; zero velocity published')
            self._publish_telemetry()
            return
        if self._state is PatrolState.STOPPING:
            return
        transition = self._machine.handle(PatrolEvent.STOP)
        self.get_logger().info(
            f'[PATROL] {transition.previous.name} -> STOPPING; zero velocity published')
        self._publish_state()
        finished = self._machine.handle(PatrolEvent.TASK_CANCELLED)
        self.get_logger().info(
            f'[PATROL] PATROL STOPPED: {finished.previous.name} -> {finished.current.name}')
        self._publish_state()
        self._publish_telemetry()

    def _shutdown_safely(self) -> None:
        """Publish zero velocity and release OpenCR patrol ownership."""
        self._publish_zero_velocity()
        if self._state in (
            PatrolState.FORWARD,
            PatrolState.TURN_RIGHT,
            PatrolState.ERROR,
        ):
            self._machine.handle(PatrolEvent.STOP)
            self._publish_state()
        if self._state is PatrolState.STOPPING:
            self._machine.handle(PatrolEvent.TASK_CANCELLED)
            self._publish_state()
        self._publish_telemetry()

    def _on_odom(self, message: Odometry) -> None:
        position = message.pose.pose.position
        orientation = message.pose.pose.orientation
        self._x = float(position.x)
        self._y = float(position.y)
        self._yaw = quaternion_to_yaw(
            orientation.x, orientation.y, orientation.z, orientation.w)
        self._last_odom_clock_ns = self.get_clock().now().nanoseconds
        if self._state in (PatrolState.FORWARD, PatrolState.TURN_RIGHT):
            self._append_path_pose(message)

    def _on_input_source(self, message: String) -> None:
        source = message.data.strip().upper()
        if source:
            self._input_device = source

    def _control_step(self) -> None:
        if self._state not in (PatrolState.FORWARD, PatrolState.TURN_RIGHT):
            return
        if not self._odom_is_fresh():
            self._fail('Odometry timed out; stopped for safety')
            return
        if (self._phase_started_clock_ns is not None and
                (self.get_clock().now().nanoseconds - self._phase_started_clock_ns) / 1e9 >
                float(self.get_parameter('phase_timeout_sec').value)):
            self._fail('Motion phase safety timeout; stopped for safety')
            return

        if self._state is PatrolState.FORWARD:
            self._step_forward()
        else:
            self._step_turn_right()

    def _step_forward(self) -> None:
        assert self._x is not None and self._y is not None
        assert self._forward_start is not None and self._yaw is not None
        start_x, start_y = self._forward_start
        self._current_distance = planar_distance(start_x, start_y, self._x, self._y)
        target = float(self.get_parameter('target_distance').value)
        tolerance = float(self.get_parameter('distance_tolerance').value)
        if self._current_distance >= target - tolerance:
            self._publish_zero_velocity()
            self._machine.handle(PatrolEvent.DISTANCE_REACHED)
            self._turn_start_yaw = self._yaw
            self._current_turn = 0.0
            self._phase_started_clock_ns = self.get_clock().now().nanoseconds
            self.get_logger().info(
                f'[MOTION] FORWARD #{self._phase_number} complete: '
                f'{self._current_distance:.3f} m; TURN_RIGHT 90 deg')
            self._publish_state()
            self._publish_telemetry()
            return

        yaw_error = normalize_angle(self._forward_yaw - self._yaw)
        heading_gain = float(self.get_parameter('heading_gain').value)
        max_angular = float(self.get_parameter('angular_speed').value)
        angular = max(-max_angular, min(max_angular, heading_gain * yaw_error))
        self._publish_velocity(
            float(self.get_parameter('linear_speed').value), angular)

    def _step_turn_right(self) -> None:
        assert self._yaw is not None
        self._current_turn = right_turn_progress(self._turn_start_yaw, self._yaw)
        target = float(self.get_parameter('target_turn').value)
        tolerance = float(self.get_parameter('angle_tolerance').value)
        if self._current_turn >= target - tolerance:
            completed_turn = self._current_turn
            self._publish_zero_velocity()
            self._turn_count += 1
            if self._turn_count % 4 == 0:
                self._cycle_count += 1
                self._publish_cycle_count()
                self.get_logger().info(f'[PATROL] LOOP {self._cycle_count} COMPLETE')
            self._phase_number = self._turn_count % 4 + 1
            self._machine.handle(PatrolEvent.TURN_REACHED)
            self._set_forward_origin()
            target_distance = float(self.get_parameter('target_distance').value)
            self.get_logger().info(
                f'[MOTION] TURN_RIGHT complete: {math.degrees(completed_turn):.1f} deg; '
                f'FORWARD #{self._phase_number} target '
                f'{target_distance:.3f} m')
            self._publish_state()
            self._publish_telemetry()
            return
        remaining = max(0.0, target - self._current_turn)
        slowdown_angle = float(self.get_parameter('turn_slowdown_angle').value)
        fast_speed = float(self.get_parameter('angular_speed').value)
        slow_speed = float(self.get_parameter('turn_slow_speed').value)
        turn_speed = slow_speed if remaining <= slowdown_angle else fast_speed
        self._publish_velocity(0.0, -turn_speed)

    def _set_forward_origin(self) -> None:
        assert self._x is not None and self._y is not None and self._yaw is not None
        self._forward_start = (self._x, self._y)
        self._forward_yaw = self._yaw
        self._current_distance = 0.0
        self._current_turn = 0.0
        self._phase_started_clock_ns = self.get_clock().now().nanoseconds

    def _odom_is_fresh(self) -> bool:
        return (
            self._last_odom_clock_ns is not None
            and (self.get_clock().now().nanoseconds - self._last_odom_clock_ns) / 1e9
            <= float(self.get_parameter('odom_timeout_sec').value)
            and self._x is not None
            and self._y is not None
            and self._yaw is not None
        )

    def _fail(self, reason: str) -> None:
        self._publish_zero_velocity()
        transition = self._machine.handle(PatrolEvent.TASK_FAILED)
        self.get_logger().error(
            f'{reason}: {transition.previous.name} -> {transition.current.name}')
        self._publish_state()
        self._publish_telemetry()

    def _publish_velocity(self, linear: float, angular: float) -> None:
        self._commanded_linear_speed = linear
        self._commanded_angular_speed = angular
        message = TwistStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'base_link'
        message.twist.linear.x = linear
        message.twist.angular.z = angular
        self._cmd_vel_pub.publish(message)

    def _publish_zero_velocity(self) -> None:
        self._publish_velocity(0.0, 0.0)
        self.get_logger().info('[MOTION] Publishing zero velocity')

    def _append_path_pose(self, odom: Odometry) -> None:
        pose = PoseStamped()
        pose.header = odom.header
        pose.pose = odom.pose.pose
        if not self._path_poses or self._path_poses[-1].header.stamp != pose.header.stamp:
            self._path_poses.append(pose)
        if len(self._path_poses) > 4000:
            del self._path_poses[:1000]
        self._publish_path()

    def _publish_path(self) -> None:
        message = Path()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'odom'
        message.poses = self._path_poses.copy()
        self._path_pub.publish(message)

    def _publish_state(self) -> None:
        message = String()
        message.data = self._state.name
        self._state_pub.publish(message)

    def _publish_cycle_count(self) -> None:
        message = UInt32()
        message.data = self._cycle_count
        self._cycle_pub.publish(message)

    def _telemetry(self) -> dict[str, Any]:
        state = self._state.name
        return {
            'mode': 'PATROL' if state in ('FORWARD', 'TURN_RIGHT') else state,
            'state': state,
            'input_device': self._input_device,
            'last_command': self._last_command,
            'target_distance': float(self.get_parameter('target_distance').value),
            'current_distance': self._current_distance,
            'target_turn': float(self.get_parameter('target_turn').value),
            'current_turn': self._current_turn,
            'linear_speed': float(self.get_parameter('linear_speed').value),
            'angular_speed': float(self.get_parameter('angular_speed').value),
            'turn_slow_speed': float(self.get_parameter('turn_slow_speed').value),
            'commanded_linear_speed': self._commanded_linear_speed,
            'commanded_angular_speed': self._commanded_angular_speed,
            'phase_number': self._phase_number,
            'loop_count': self._cycle_count,
            'x': self._x,
            'y': self._y,
            'yaw': self._yaw,
        }

    def _publish_telemetry(self) -> None:
        message = String()
        message.data = json.dumps(self._telemetry(), separators=(',', ':'))
        self._telemetry_pub.publish(message)


def main(args=None) -> None:
    """Run the shared odometry-based patrol controller."""
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = PatrolController()

    def stop_before_shutdown(_signal_number, _frame) -> None:
        if rclpy.ok():
            node._shutdown_safely()
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, stop_before_shutdown)
    signal.signal(signal.SIGTERM, stop_before_shutdown)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node._publish_zero_velocity()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
