"""ROS text-command interface for exercising the patrol state machine."""

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String, UInt32

from turtlebot_patrol.patrol_state import (
    PatrolEvent,
    PatrolState,
    PatrolStateMachine,
)
from turtlebot_patrol.remote_command import parse_command


class PatrolStateNode(Node):
    """Apply mock patrol commands and publish the resulting state."""

    def __init__(self) -> None:
        super().__init__('patrol_state_node')
        self.declare_parameter('command_topic', '/patrol_command')
        self.declare_parameter('state_topic', '/patrol_state')
        self.declare_parameter('cycle_count_topic', '/patrol_cycle_count')
        command_topic = self.get_parameter('command_topic').value
        state_topic = self.get_parameter('state_topic').value
        cycle_count_topic = self.get_parameter('cycle_count_topic').value

        self._machine = PatrolStateMachine()
        status_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._state_pub = self.create_publisher(String, state_topic, status_qos)
        self._cycle_pub = self.create_publisher(UInt32, cycle_count_topic, status_qos)
        self._command_sub = self.create_subscription(
            String,
            command_topic,
            self._on_command,
            10,
        )
        self._publish_state()
        self._publish_cycle_count()
        self.get_logger().info(
            f'Listening on {command_topic}; publishing state on {state_topic}')

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

        # Until Nav2 is connected, there is no task to cancel during STOP.
        if event is PatrolEvent.STOP and self._machine.state is PatrolState.STOPPING:
            self._machine.handle(PatrolEvent.TASK_CANCELLED)
            self._publish_state()

    def _publish_state(self) -> None:
        message = String()
        message.data = self._machine.state.name
        self._state_pub.publish(message)

    def _publish_cycle_count(self) -> None:
        message = UInt32()
        message.data = 0
        self._cycle_pub.publish(message)


def main(args=None) -> None:
    """Spin the ROS state and mock-command node."""
    rclpy.init(args=args)
    node = PatrolStateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
