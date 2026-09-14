#!/bin/bash
# Export every printable part to stl/. Binary STL: ~3x smaller than ASCII and
# the repo has to carry them.
cd "$(dirname "$0")" && mkdir -p stl
render() {
    openscad --export-format binstl -o "stl/$1.stl" -D "part=\"$1\"" vr_rig.scad 2>&1 \
      | grep -iE 'error|warning' | sed "s/^/$1: /"
    printf '%-15s %8s B\n' "$1" "$(stat -c%s "stl/$1.stl" 2>/dev/null || echo FAIL)"
}
export -f render
printf '%s\n' base bearing_block motor_mount wheel_hub \
              crank_gear cam_gear cam_target sensor_mount \
  | xargs -P "$(nproc)" -I{} bash -c 'render {}'
