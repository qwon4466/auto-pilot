"""Console monitor for patrol state and completed waypoint cycles."""

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import String, UInt32


class PatrolMonitor(Node):
    """Display the latest patrol state and successful cycle count."""

    def __init__(self) -> None:
        super().__init__('patrol_monitor')
        self.declare_parameter('state_topic', '/patrol_state')
        self.declare_parameter('cycle_count_topic', '/patrol_cycle_count')
        self._state = 'UNKNOWN'
        self._cycle_count = 0
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

    def _on_state(self, message: String) -> None:
        self._state = message.data
        self._display_status()

    def _on_cycle_count(self, message: UInt32) -> None:
        self._cycle_count = message.data
        self._display_status()

    def _display_status(self) -> None:
        self.get_logger().info(
            f'Patrol state: {self._state} | completed cycles: {self._cycle_count}')


def main(args=None) -> None:
    """Spin the patrol monitor node."""
    rclpy.init(args=args)
    node = PatrolMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
