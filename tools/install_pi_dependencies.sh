#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
ros_setup=/opt/ros/jazzy/setup.bash

if ! command -v apt-cache >/dev/null 2>&1; then
  echo "This installer requires Ubuntu 24.04 with APT." >&2
  exit 1
fi

ros_base_candidate=$(apt-cache policy ros-jazzy-ros-base | awk '/Candidate:/ {print $2; exit}')
if [[ -z "$ros_base_candidate" || "$ros_base_candidate" == '(none)' ]]; then
  echo "ROS 2 Jazzy APT repository is not configured. Configure it, then rerun this script." >&2
  echo "Official guide: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html" >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y \
  ros-jazzy-ros-base \
  ros-jazzy-turtlebot3-bringup \
  ros-jazzy-turtlebot3-description \
  ros-jazzy-turtlebot3-msgs \
  ros-jazzy-dynamixel-sdk \
  ros-jazzy-hls-lfcd-lds-driver \
  ros-jazzy-xacro \
  git \
  build-essential \
  libboost-system-dev \
  libudev-dev \
  python3-argcomplete \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-yaml \
  python3-pytest

if [[ ! -f "$ros_setup" ]]; then
  echo "ROS 2 Jazzy package installation completed, but $ros_setup was not found." >&2
  exit 1
fi

if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  sudo rosdep init
fi

source "$ros_setup"
rosdep update
rosdep install --from-paths "$repo_root/src" --ignore-src -r -y

cat <<'EOF'
Pi dependencies are installed.
Next, from this repository root, run:
  tools/pi4_build_overlay.sh

The OpenCR RC-100 patrol firmware still needs to be compiled and flashed
separately from a supported PC before RC-100 Button 1/4 can control patrol.
EOF
