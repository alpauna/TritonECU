#!/bin/bash
# Export the template parts to stl/.
cd "$(dirname "$0")" && mkdir -p stl
render() {
    openscad --export-format binstl -o "stl/$1.stl" -D "part=\"$1\"" carrier_template.scad 2>&1 \
      | grep -iE 'error|warning|ECHO' | sed "s/^/$1: /"
    printf '%-10s %9s B\n' "$1" "$(stat -c%s "stl/$1.stl" 2>/dev/null || echo FAIL)"
}
export -f render
printf "%s\n" template ring conn_gauge | xargs -P "$(nproc)" -I{} bash -c 'render {}'
