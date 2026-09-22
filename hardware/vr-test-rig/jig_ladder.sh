#!/bin/bash
# Print a LADDER of hole jigs, one per degree, and see which one seats.
#
# A round 6.10 pin in a 6.35 hole tolerates +/-0.24 deg. The angle is known to
# about +/-3. So a single jig at nominal is a coin toss on a perfect wheel, and
# the ladder is not belt-and-braces - it is the measurement. The rung that seats
# reports the angle to +/-0.24, finer than any one tolerant part could manage.
#
#   ./jig_ladder.sh            # 92..98, the range agreed off the photo
#   ./jig_ladder.sh 88 102     # wider, if none of the first set seats
cd "$(dirname "$0")" || exit 1
lo=${1:-92}; hi=${2:-98}
mkdir -p stl/ladder
one() {
    openscad --export-format binstl -o "stl/ladder/jig_$1.stl" \
             -D 'part="hole_jig"' -D "aux_hole_ang=$1" vr_rig.scad 2>&1 \
      | grep -iE '^ERROR' | sed "s/^/  $1: /"
    printf '  jig_%s.stl  %8s B\n' "$1" "$(stat -c%s "stl/ladder/jig_$1.stl" 2>/dev/null || echo FAIL)"
}
export -f one
seq "$lo" "$hi" | xargs -P "$(nproc)" -I{} bash -c 'one {}'
echo
echo "Print all of them. The one that drops in is the angle, +/-0.24 deg."
echo "If none seats, the angle is outside $lo..$hi - widen and rerun."
echo "If NONE of a wide sweep seats, suspect the radius (29.3695) before the angle."
