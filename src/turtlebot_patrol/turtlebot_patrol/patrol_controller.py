"""Navigation2 waypoint patrol controller with command cancellation."""

import math
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped, TwistStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String, UInt32

from turtlebot_patrol.patrol_plan import load_patrol_plan
from turtlebot_patrol.patrol_state import (
    PatrolEvent,
    PatrolState,
    PatrolStateMachine,
)
from turtlebot_patrol.remote_command import parse_command


class PatrolController(BasicNavigator):
    """Run the configured waypoint cycle while servicing START and STOP."""

    def __init__(self) -> None:
        super().__init__(node_name='patrol_controller')
        self.declare_parameter('command_topic', '/patrol_command')
        self.declare_parameter('state_topic', '/patrol_state')
        default_config = str(
            Path(get_package_share_directory('turtlebot_patrol'))
            / 'config'
            / 'waypoints.yaml'
        )
        self.declare_parameter('waypoints_file', default_config)

        self._machine = PatrolStateMachine()
        self._task_active = False
        self._cycle_count = 0
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('cycle_count_topic', '/patrol_cycle_count')
        command_topic = self.get_parameter('command_topic').value
        state_topic = self.get_parameter('state_topic').value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        cycle_count_topic = self.get_parameter('cycle_count_topic').value
        status_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._state_pub = self.create_publisher(String, state_topic, status_qos)
        self._cycle_pub = self.create_publisher(UInt32, cycle_count_topic, status_qos)
        self._cmd_vel_pub = self.create_publisher(TwistStamped, cmd_vel_topic, 10)
        self._command_sub = self.create_subscription(
            String,
            command_topic,
            self._on_command,
            10,
        )

        initial_pose, waypoints = load_patrol_plan(
            self.get_parameter('waypoints_file').value
        )
        self._initial_pose = initial_pose
        self._waypoints = waypoints
        self._publish_state()
        self._publish_cycle_count()

    def run(self) -> None:
        """Wait for Nav2, then process commands and repeat waypoint tasks."""
        self.setInitialPose(self._make_initial_pose())
        self.get_logger().info('Waiting for Nav2 and initial localization...')
        self.waitUntilNav2Active()
        self.get_logger().info(
            f'Nav2 ready; {len(self._waypoints)} configured patrol waypoints')

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            if self._machine.state is PatrolState.STOPPING:
                self._cancel_and_stop()
            elif self._machine.state is PatrolState.PATROL:
                if not self._task_active:
                    self._start_cycle()
                elif self.isTaskComplete():
                    self._finish_cycle()

    def stop_immediately(self) -> None:
        """Cancel a running task and publish a zero velocity command."""
        if self._task_active:
            self.cancelTask()
            self._task_active = False
        self._publish_zero_velocity()

    def _on_command(self, message: String) -> None:
        event = parse_command(message.data)
        if event is None:
            self.get_logger().warning(f'Ignoring unknown patrol command: {message.data!r}')
            return

        transition = self._machine.handle(event)
        if transition.changed:
            self.get_logger().info(
                f'{event.name}: {transition.previous.name} -> {transition.current.name}')
        else:
            self.get_logger().info(
                f'{event.name} ignored in {transition.current.name}')
        self._publish_state()

    def _start_cycle(self) -> None:
        self.get_logger().info(f'Starting patrol cycle {self._cycle_count + 1}')
        if self.followWaypoints(self._make_waypoints()):
            self._task_active = True
        else:
            self._machine.handle(PatrolEvent.TASK_FAILED)
            self._publish_state()
            self._publish_zero_velocity()

    def _finish_cycle(self) -> None:
        self._task_active = False
        result = self.getResult()
        if result is TaskResult.SUCCEEDED:
            self._cycle_count += 1
            self._publish_cycle_count()
            self.get_logger().info(
                f'Patrol cycle {self._cycle_count} completed; repeating waypoints')
            return

        self.get_logger().error(f'Patrol task ended with result {result}')
        self._machine.handle(PatrolEvent.TASK_FAILED)
        self._publish_state()
        self._publish_zero_velocity()

    def _cancel_and_stop(self) -> None:
        self.get_logger().info('Canceling patrol task and publishing zero velocity')
        self.stop_immediately()
        transition = self._machine.handle(PatrolEvent.TASK_CANCELLED)
        self.get_logger().info(
            f'TASK_CANCELLED: {transition.previous.name} -> {transition.current.name}')
        self._publish_state()

    def _make_initial_pose(self) -> PoseStamped:
        result = PoseStamped()
        result.header.frame_id = 'map'
        # Let AMCL use its latest odom transform during simulated-time startup.
        result.header.stamp.sec = 0
        result.header.stamp.nanosec = 0
        pose = self._initial_pose
        result.pose.position.x = pose['x']
        result.pose.position.y = pose['y']
        result.pose.orientation.z = math.sin(pose['yaw'] / 2.0)
        result.pose.orientation.w = math.cos(pose['yaw'] / 2.0)
        return result

    def _make_waypoints(self) -> list[PoseStamped]:
        poses = []
        for waypoint in self._waypoints:
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = waypoint['x']
            pose.pose.position.y = waypoint['y']
            pose.pose.orientation.z = math.sin(waypoint['yaw'] / 2.0)
            pose.pose.orientation.w = math.cos(waypoint['yaw'] / 2.0)
            poses.append(pose)
        return poses

    def _publish_state(self) -> None:
        message = String()
        message.data = self._machine.state.name
        self._state_pub.publish(message)

    def _publish_cycle_count(self) -> None:
        message = UInt32()
        message.data = self._cycle_count
        self._cycle_pub.publish(message)

    def _publish_zero_velocity(self) -> None:
        message = TwistStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'base_link'
        self._cmd_vel_pub.publish(message)


def main(args=None) -> None:
    """Start the Nav2 waypoint patrol controller."""
    rclpy.init(args=args)
    controller = None
    try:
        controller = PatrolController()
        controller.run()
    except KeyboardInterrupt:
        pass
    finally:
        if controller is not None:
            controller.stop_immediately()
            controller.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
