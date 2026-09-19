#!/bin/bash
# Export the label to stl/. Binary STL: ~3x smaller than ASCII and the repo
# has to carry it. Text geometry makes this slow - a minute or two per part.
#
#   label              one piece, single colour or a filament change at 2.4 mm
#   plate/text/warn    three pieces sharing an origin, for multi-material.
#                      Load all three as ONE object; warn gets the red.
cd "$(dirname "$0")" && mkdir -p stl
render() {
    openscad --export-format binstl -o "stl/$1.stl" -D "part=\"$1\"" harness_label.scad 2>&1 \
      | grep -iE 'error|warning|ECHO' | sed "s/^/$1: /"
    printf '%-8s %9s B\n' "$1" "$(stat -c%s "stl/$1.stl" 2>/dev/null || echo FAIL)"
}
export -f render
printf "%s\n" label plate text warn | xargs -P "$(nproc)" -I{} bash -c 'render {}'
