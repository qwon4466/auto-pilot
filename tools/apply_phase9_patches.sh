#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 OPENCR_REPOSITORY TURTLEBOT3_2_3_6_REPOSITORY" >&2
  exit 2
fi

opencr_repo=$(realpath "$1")
turtlebot3_repo=$(realpath "$2")
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
opencr_patch="$script_dir/firmware/patches/opencr-rc100-patrol.patch"
turtlebot3_patch="$script_dir/firmware/patches/turtlebot3-node-rc100-patrol.patch"
expected_opencr=68ec75d8a400949580ecf263e0105ea9743b878e
expected_turtlebot3=da785b7201d317e6e2a662e41bb3d3fd50ebd503

actual_opencr=$(git -C "$opencr_repo" rev-parse HEAD)
actual_turtlebot3=$(git -C "$turtlebot3_repo" rev-parse HEAD)
if [[ "$actual_opencr" != "$expected_opencr" ]]; then
  echo "OpenCR source revision mismatch: expected $expected_opencr, got $actual_opencr" >&2
  exit 1
fi
if [[ "$actual_turtlebot3" != "$expected_turtlebot3" ]]; then
  echo "TurtleBot3 source revision mismatch: expected $expected_turtlebot3, got $actual_turtlebot3" >&2
  exit 1
fi

if git -C "$opencr_repo" apply --reverse --check "$opencr_patch" >/dev/null 2>&1; then
  opencr_state=applied
else
  git -C "$opencr_repo" apply --check "$opencr_patch"
  opencr_state=pending
fi

if git -C "$turtlebot3_repo" apply --reverse --check "$turtlebot3_patch" >/dev/null 2>&1; then
  turtlebot3_state=applied
else
  git -C "$turtlebot3_repo" apply --check "$turtlebot3_patch"
  turtlebot3_state=pending
fi

if [[ "$opencr_state" == pending ]]; then
  git -C "$opencr_repo" apply "$opencr_patch"
  echo "Applied OpenCR RC-100 patrol patch."
else
  echo "OpenCR RC-100 patrol patch is already applied."
fi

if [[ "$turtlebot3_state" == pending ]]; then
  git -C "$turtlebot3_repo" apply "$turtlebot3_patch"
  echo "Applied TurtleBot3 node RC-100 patrol patch."
else
  echo "TurtleBot3 node RC-100 patrol patch is already applied."
fi
