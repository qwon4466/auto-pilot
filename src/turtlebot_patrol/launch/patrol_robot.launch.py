"""Launch the shared odometry patrol on an already-started TurtleBot3 base."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Start the real-robot patrol and monitor without another cmd_vel source."""
    return LaunchDescription([
        Node(
            package='turtlebot_patrol',
            executable='patrol_controller',
            name='patrol_controller',
            output='screen',
            parameters=[{'use_sim_time': False}],
        ),
        Node(
            package='turtlebot_patrol',
            executable='patrol_monitor',
            name='patrol_monitor',
            output='screen',
            parameters=[{'use_sim_time': False}],
        ),
    ])
