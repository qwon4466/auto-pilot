"""Publish patrol commands from the desktop keyboard's 1 and 4 keys."""

import os
import select
import termios
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from turtlebot_patrol.keyboard_keys import extract_patrol_keys


class KeyboardControl(Node):
    """Read keys from the controlling terminal and publish START/STOP."""

    def __init__(self) -> None:
        super().__init__('keyboard_control')
        self.declare_parameter('command_topic', '/patrol_command')
        self.declare_parameter('state_topic', '/patrol_state')
        self.declare_parameter('input_source_topic', '/patrol_input_source')
        self._state = 'IDLE'
        self._sequence_buffer = ''
        self._command_pub = self.create_publisher(
            String, self.get_parameter('command_topic').value, 10)
        self._source_pub = self.create_publisher(
            String, self.get_parameter('input_source_topic').value, 10)
        self._state_sub = self.create_subscription(
            String,
            self.get_parameter('state_topic').value,
            self._on_state,
            10,
        )

    def _on_state(self, message: String) -> None:
        self._state = message.data

    def read_terminal(self) -> int:
        """Process keys until ROS shuts down; restore terminal mode on exit."""
        descriptor = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY)
        previous_settings = termios.tcgetattr(descriptor)
        print(
            '\n========================================\n'
            ' TurtleBot Patrol Keyboard Controller\n'
            '========================================\n'
            '[1] 자동 반복순찰 시작\n'
            '[4] 자동 반복순찰 종료\n'
            f'현재 상태 : {self._state}\n\n'
            '숫자 1 또는 숫자패드 1을 누르세요.\n'
            '숫자 4 또는 숫자패드 4를 누르면 정지합니다.\n'
            '종료: Ctrl+C\n'
            '========================================',
            flush=True,
        )
        try:
            tty.setraw(descriptor, termios.TCSANOW)
            while rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0.02)
                readable, _, _ = select.select([descriptor], [], [], 0.02)
                if not readable:
                    continue
                self._sequence_buffer += os.read(descriptor, 16).decode(
                    'utf-8', errors='ignore')
                if '\x03' in self._sequence_buffer:
                    self._sequence_buffer = self._sequence_buffer.replace('\x03', '')
                    break
                keys, self._sequence_buffer = extract_patrol_keys(
                    self._sequence_buffer)
                for key in keys:
                    self._handle_key(key)
        finally:
            termios.tcsetattr(descriptor, termios.TCSANOW, previous_settings)
            os.close(descriptor)
        return 0

    def _handle_key(self, key: str) -> None:
        if key == '1':
            self.get_logger().info('[INPUT] KEY 1')
            if self._state in ('FORWARD', 'TURN_RIGHT'):
                self.get_logger().info('[PATROL] Already running. START ignored.')
                return
            command = 'START'
            self.get_logger().info('[PATROL] START REQUEST')
        else:
            self.get_logger().info('[INPUT] KEY 4')
            command = 'STOP'
            self.get_logger().info('[PATROL] STOP REQUEST')

        source_message = String()
        source_message.data = 'KEYBOARD'
        self._source_pub.publish(source_message)
        command_message = String()
        command_message.data = command
        self._command_pub.publish(command_message)


def main(args=None) -> None:
    """Run the keyboard input node while preserving terminal settings."""
    rclpy.init(args=args)
    node = KeyboardControl()
    try:
        node.read_terminal()
    except OSError as error:
        node.get_logger().error(
            f'Cannot read keyboard input without an interactive terminal: {error}')
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
