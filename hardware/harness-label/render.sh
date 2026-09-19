#!/bin/bash
# Export the label to stl/. Binary STL: ~3x smaller than ASCII and the repo
# has to carry it. Text geometry makes this slow - a minute or two is normal.
cd "$(dirname "$0")" && mkdir -p stl
for p in label; do
    openscad --export-format binstl -o "stl/$p.stl" -D "part=\"$p\"" harness_label.scad 2>&1 \
      | grep -iE 'error|warning|ECHO' | sed "s/^/$p: /"
    printf '%-12s %8s B\n' "$p" "$(stat -c%s "stl/$p.stl" 2>/dev/null || echo FAIL)"
done
