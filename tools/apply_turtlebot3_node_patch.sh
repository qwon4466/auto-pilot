#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 TURTLEBOT3_2_3_6_REPOSITORY" >&2
  exit 2
fi

turtlebot3_repo=$(realpath "$1")
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
patch_file="$script_dir/firmware/patches/turtlebot3-node-rc100-patrol.patch"
expected_commit=da785b7201d317e6e2a662e41bb3d3fd50ebd503
actual_commit=$(git -C "$turtlebot3_repo" rev-parse HEAD)

if [[ "$actual_commit" != "$expected_commit" ]]; then
  echo "TurtleBot3 source revision mismatch: expected $expected_commit, got $actual_commit" >&2
  exit 1
fi

if git -C "$turtlebot3_repo" apply --reverse --check "$patch_file" >/dev/null 2>&1; then
  echo "TurtleBot3 node RC-100 patrol patch is already applied."
  exit 0
fi

git -C "$turtlebot3_repo" apply --check "$patch_file"
git -C "$turtlebot3_repo" apply "$patch_file"
echo "Applied TurtleBot3 node RC-100 patrol patch."
