"""Convenience launch alias for the complete desktop simulation demo."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    """Start the full Gazebo patrol and keyboard-control demonstration."""
    package_share = get_package_share_directory('turtlebot_patrol')
    simulation_launch = os.path.join(package_share, 'launch', 'patrol_sim.launch.py')
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(simulation_launch)),
    ])
