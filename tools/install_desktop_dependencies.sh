#!/usr/bin/env bash
set -euo pipefail

# Install the Ubuntu/ROS binary dependencies documented for the desktop
# simulator. ROS 2 Jazzy's Ubuntu repository must already be configured.
if ! dpkg-query -W -f='${Status}' ros2-apt-source 2>/dev/null | grep -q 'install ok installed'; then
  echo 'ROS APT source is missing. Follow docs/phase1-installation.md first.' >&2
  exit 1
fi

sudo apt update
sudo apt install -y \
  ros-jazzy-desktop \
  ros-dev-tools \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-yaml \
  python3-pytest \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-simple-commander \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-turtlebot3 \
  ros-jazzy-turtlebot3-simulations \
  ros-jazzy-domain-bridge

echo 'Desktop ROS dependencies installed. Build this workspace with colcon.'
