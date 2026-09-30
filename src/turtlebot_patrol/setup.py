from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'turtlebot_patrol'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='qwon4466',
    maintainer_email='hkl929242@gmail.com',
    description='TurtleBot3 Waffle Pi patrol package',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'patrol_controller = turtlebot_patrol.patrol_controller:main',
            'patrol_monitor = turtlebot_patrol.patrol_monitor:main',
            'patrol_state_node = turtlebot_patrol.patrol_state_node:main',
        ],
    },
)
