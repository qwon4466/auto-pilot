#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 OPENCR_REPOSITORY [BUILD_DIRECTORY]" >&2
  exit 2
fi

opencr_repo=$(realpath "$1")
build_dir=$(realpath -m "${2:-/tmp/turtlebot_patrol_opencr_build}")
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cli=${ARDUINO_CLI:-arduino-cli}
expected_commit=68ec75d8a400949580ecf263e0105ea9743b878e
actual_commit=$(git -C "$opencr_repo" rev-parse HEAD)

if [[ "$actual_commit" != "$expected_commit" ]]; then
  echo "OpenCR source revision mismatch: expected $expected_commit, got $actual_commit" >&2
  exit 1
fi
if ! git -C "$opencr_repo" apply --reverse --check \
    "$repo_root/firmware/patches/opencr-rc100-patrol.patch" >/dev/null 2>&1; then
  echo "The patrol patch is not applied to the OpenCR source." >&2
  exit 1
fi

sketch_dir="$opencr_repo/arduino/opencr_arduino/opencr/libraries/turtlebot3_ros2/examples/turtlebot3_waffle"
libraries_dir="$opencr_repo/arduino/opencr_arduino/opencr/libraries"
"$cli" compile \
  --fqbn OpenCR:OpenCR:OpenCR \
  --build-path "$build_dir" \
  --libraries "$libraries_dir" \
  "$sketch_dir"

echo "Firmware build completed. No board was flashed."
