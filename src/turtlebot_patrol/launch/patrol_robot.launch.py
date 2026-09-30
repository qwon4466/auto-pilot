"""Launch Nav2 and waypoint patrol on a real TurtleBot3 without Gazebo."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Build the hardware Nav2 and patrol launch description."""
    nav_share = get_package_share_directory('turtlebot3_navigation2')
    patrol_share = get_package_share_directory('turtlebot_patrol')
    map_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    waypoint_file = LaunchConfiguration('waypoints_file')

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            description='Absolute path to the saved map YAML for this robot area',
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(nav_share, 'param', 'waffle_pi.yaml'),
            description='Nav2 parameters for the Waffle Pi',
        ),
        DeclareLaunchArgument(
            'waypoints_file',
            default_value=os.path.join(patrol_share, 'config', 'waypoints.yaml'),
            description='YAML file with the initial pose and patrol waypoints',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav_share, 'launch', 'navigation2.launch.py')
            ),
            launch_arguments={
                'map': map_file,
                'params_file': params_file,
                'use_sim_time': 'false',
            }.items(),
        ),
        Node(
            package='turtlebot_patrol',
            executable='patrol_controller',
            name='patrol_controller',
            output='screen',
            parameters=[
                {'use_sim_time': False},
                {'waypoints_file': waypoint_file},
            ],
        ),
        Node(
            package='turtlebot_patrol',
            executable='patrol_monitor',
            name='patrol_monitor',
            output='screen',
        ),
    ])
