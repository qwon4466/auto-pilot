"""Launch Gazebo, direct odometry patrol, keyboard, monitor, and RViz."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Build a self-contained desktop patrol demonstration."""
    gazebo_share = get_package_share_directory('turtlebot3_gazebo')
    patrol_share = get_package_share_directory('turtlebot_patrol')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    simulation_domain_id = LaunchConfiguration('simulation_domain_id')
    robot_domain_id = LaunchConfiguration('robot_domain_id')
    enable_rc100_bridge = LaunchConfiguration('enable_rc100_bridge')
    enable_keyboard = LaunchConfiguration('enable_keyboard')
    show_rviz = LaunchConfiguration('show_rviz')

    keyboard_node = Node(
        package='turtlebot_patrol',
        executable='keyboard_control',
        name='keyboard_control',
        output='screen',
        emulate_tty=True,
        condition=IfCondition(enable_keyboard),
    )

    return LaunchDescription([
        DeclareLaunchArgument('spawn_x', default_value='-2.0'),
        DeclareLaunchArgument('spawn_y', default_value='-0.5'),
        DeclareLaunchArgument(
            'simulation_domain_id',
            default_value='42',
            description='ROS domain used by simulator and desktop keyboard',
        ),
        DeclareLaunchArgument(
            'robot_domain_id',
            default_value='0',
            description='ROS domain used by the physical TurtleBot3',
        ),
        DeclareLaunchArgument(
            'enable_rc100_bridge',
            default_value='false',
            description='Bridge only RC patrol command and patrol state topics',
        ),
        DeclareLaunchArgument('enable_keyboard', default_value='true'),
        DeclareLaunchArgument('show_rviz', default_value='true'),
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
        Node(
            package='turtlebot_patrol',
            executable='patrol_controller',
            name='patrol_controller',
            output='screen',
            parameters=[{'use_sim_time': True}],
        ),
        keyboard_node,
        RegisterEventHandler(
            OnProcessExit(
                target_action=keyboard_node,
                on_exit=[EmitEvent(event=Shutdown(reason='Keyboard controller exited'))],
            ),
        ),
        Node(
            package='turtlebot_patrol',
            executable='patrol_monitor',
            name='patrol_monitor',
            output='screen',
            parameters=[{'use_sim_time': True}],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='patrol_rviz',
            arguments=['-d', os.path.join(patrol_share, 'rviz', 'patrol_sim.rviz')],
            parameters=[{'use_sim_time': True}],
            output='screen',
            condition=IfCondition(show_rviz),
        ),
        Node(
            package='domain_bridge',
            executable='domain_bridge',
            name='rc100_command_to_sim_bridge',
            arguments=[
                '--from', robot_domain_id,
                '--to', simulation_domain_id,
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
                '--from', simulation_domain_id,
                '--to', robot_domain_id,
                os.path.join(patrol_share, 'config', 'sim_state_bridge.yaml'),
            ],
            condition=IfCondition(enable_rc100_bridge),
            output='screen',
        ),
    ])
