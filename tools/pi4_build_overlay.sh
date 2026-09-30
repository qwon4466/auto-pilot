#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
overlay_ws=${TB3_PATROL_OVERLAY_WS:-"$HOME/tb3_patrol_overlay_ws"}
turtlebot3_source="$overlay_ws/src/turtlebot3"
patrol_source="$overlay_ws/src/turtlebot_patrol"
expected_turtlebot3=da785b7201d317e6e2a662e41bb3d3fd50ebd503

if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo "ROS 2 Jazzy was not found at /opt/ros/jazzy." >&2
  exit 1
fi

mkdir -p "$overlay_ws/src"
if [[ ! -e "$patrol_source" ]]; then
  ln -s "$repo_root/src/turtlebot_patrol" "$patrol_source"
fi
if [[ ! -d "$turtlebot3_source/.git" ]]; then
  git clone --filter=blob:none --depth 1 --branch 2.3.6 \
    https://github.com/ROBOTIS-GIT/turtlebot3.git "$turtlebot3_source"
  git -C "$turtlebot3_source" sparse-checkout set turtlebot3_node
fi

actual_turtlebot3=$(git -C "$turtlebot3_source" rev-parse HEAD)
if [[ "$actual_turtlebot3" != "$expected_turtlebot3" ]]; then
  echo "TurtleBot3 source revision mismatch: expected $expected_turtlebot3, got $actual_turtlebot3" >&2
  exit 1
fi

"$repo_root/tools/apply_turtlebot3_node_patch.sh" "$turtlebot3_source"

set +u
source /opt/ros/jazzy/setup.bash
set -u
rosdep install --from-paths "$overlay_ws/src" --ignore-src -r -y
colcon --log-base "$overlay_ws/log" build \
  --base-paths "$overlay_ws/src" \
  --build-base "$overlay_ws/build" \
  --install-base "$overlay_ws/install" \
  --packages-up-to turtlebot_patrol turtlebot3_node \
  --allow-overriding turtlebot3_node

cat <<EOF
Overlay build completed at: $overlay_ws
Before starting TurtleBot3 bringup in each terminal, run:
  source /opt/ros/jazzy/setup.bash
  source $overlay_ws/install/setup.bash
EOF
