"""Launch the shared odometry patrol on an already-started TurtleBot3 base."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Start the real-robot patrol and monitor without another cmd_vel source."""
    cmd_vel_type = LaunchConfiguration('cmd_vel_type')
    return LaunchDescription([
        DeclareLaunchArgument(
            'cmd_vel_type',
            default_value='geometry_msgs/msg/TwistStamped',
            description=(
                'Use geometry_msgs/msg/TwistStamped or geometry_msgs/msg/Twist '
                'to match the active TurtleBot3 /cmd_vel subscriber'),
        ),
        Node(
            package='turtlebot_patrol',
            executable='patrol_controller',
            name='patrol_controller',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'target_distance': 0.15,
                'linear_speed': 0.05,
                'angular_speed': 0.4,
                'turn_slow_speed': 0.10,
                'cmd_vel_type': cmd_vel_type,
            }],
        ),
        Node(
            package='turtlebot_patrol',
            executable='patrol_monitor',
            name='patrol_monitor',
            output='screen',
            parameters=[{'use_sim_time': False}],
        ),
    ])
