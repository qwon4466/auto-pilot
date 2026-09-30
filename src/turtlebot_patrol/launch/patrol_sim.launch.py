"""Launch TurtleBot3 Gazebo, Nav2, and the waypoint patrol controller."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Build the Waffle Pi simulation patrol launch description."""
    gazebo_share = get_package_share_directory('turtlebot3_gazebo')
    nav_share = get_package_share_directory('turtlebot3_navigation2')
    patrol_share = get_package_share_directory('turtlebot_patrol')
    waypoint_file = LaunchConfiguration('waypoints_file')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    simulation_domain_id = LaunchConfiguration('simulation_domain_id')
    robot_domain_id = LaunchConfiguration('robot_domain_id')
    enable_rc100_bridge = LaunchConfiguration('enable_rc100_bridge')

    return LaunchDescription([
        DeclareLaunchArgument(
            'waypoints_file',
            default_value=os.path.join(patrol_share, 'config', 'waypoints.yaml'),
            description='YAML file with initial pose and patrol waypoints',
        ),
        DeclareLaunchArgument('spawn_x', default_value='-2.0'),
        DeclareLaunchArgument('spawn_y', default_value='-0.5'),
        DeclareLaunchArgument(
            'simulation_domain_id',
            default_value='42',
            description='ROS_DOMAIN_ID used by the simulator nodes',
        ),
        DeclareLaunchArgument(
            'robot_domain_id',
            default_value='0',
            description='ROS domain used by the physical TurtleBot3 nodes',
        ),
        DeclareLaunchArgument(
            'enable_rc100_bridge',
            default_value='false',
            description='Forward only /patrol_command from the robot domain to simulation',
        ),
        SetEnvironmentVariable('ROS_DOMAIN_ID', simulation_domain_id),
        SetEnvironmentVariable('TURTLEBOT3_MODEL', 'waffle_pi'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_share, 'launch', 'turtlebot3_world.launch.py')
            ),
            launch_arguments={
                'x_pose': spawn_x,
                'y_pose': spawn_y,
                'use_sim_time': 'true',
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav_share, 'launch', 'navigation2.launch.py')
            ),
            launch_arguments={'use_sim_time': 'true'}.items(),
        ),
        Node(
            package='turtlebot_patrol',
            executable='patrol_controller',
            name='patrol_controller',
            output='screen',
            parameters=[
                {'use_sim_time': True},
                {
                    'waypoints_file': waypoint_file,
                },
            ],
        ),
        Node(
            package='domain_bridge',
            executable='domain_bridge',
            name='rc100_command_to_sim_bridge',
            arguments=[
                '--from',
                robot_domain_id,
                '--to',
                simulation_domain_id,
                os.path.join(patrol_share, 'config', 'rc100_command_bridge.yaml'),
            ],
            condition=IfCondition(enable_rc100_bridge),
            output='screen',
        ),
        Node(
            package='domain_bridge',
            executable='domain_bridge',
            name='sim_state_to_rc100_bridge',
            arguments=[
                '--from',
                simulation_domain_id,
                '--to',
                robot_domain_id,
                os.path.join(patrol_share, 'config', 'sim_state_bridge.yaml'),
            ],
            condition=IfCondition(enable_rc100_bridge),
            output='screen',
        ),
        Node(
            package='turtlebot_patrol',
            executable='patrol_monitor',
            name='patrol_monitor',
            output='screen',
        ),
    ])
