#!/usr/bin/env python3
"""Measure the rendered STLs. An estimate is not a check.

CHAR_W in the .scad can only approximate glyph widths - OpenSCAD 2021.01 has
no textmetrics() - and it was wrong in the unsafe direction once already,
passing three rows that overran the plate and one that reached into the
zip-tie slots. This measures what actually came out.
"""
import struct, sys, os

PLATE_W, MARGIN_X = 98.0, 7.0
SLOT_IN, SLOT_WID = 4.5, 2.2
PLATE_T, TEXT_H, EMBED = 2.4, 0.8, 0.2
USABLE   = PLATE_W - 2*MARGIN_X
SLOT_IN_EDGE = PLATE_W/2 - SLOT_IN - SLOT_WID/2      # 43.4

def bbox(f):
    d = open(f, 'rb').read(); n = struct.unpack('<I', d[80:84])[0]
    xs=[]; ys=[]; zs=[]
    for i in range(n):
        o = 84 + i*50 + 12
        for v in range(3):
            x,y,z = struct.unpack('<3f', d[o+v*12:o+v*12+12])
            xs.append(x); ys.append(y); zs.append(z)
    return n, (min(xs),max(xs)), (min(ys),max(ys)), (min(zs),max(zs))

fails = []
def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond: fails.append(msg)

here = os.path.dirname(os.path.abspath(__file__))
parts = {}
print(f"{'part':>6} {'tris':>7} {'X range':>21} {'Y range':>21} {'Z range':>15}")
for p in ("plate","text","warn","label"):
    f = os.path.join(here, "stl", f"{p}.stl")
    if not os.path.exists(f):
        print(f"{p:>6}   MISSING - run ./render.sh"); sys.exit(1)
    n,X,Y,Z = bbox(f); parts[p] = (X,Y,Z)
    print(f"{p:>6} {n:>7} {X[0]:>9.2f}..{X[1]:<10.2f} {Y[0]:>9.2f}..{Y[1]:<10.2f} {Z[0]:>6.2f}..{Z[1]:<7.2f}")

P,T,W,L = parts["plate"], parts["text"], parts["warn"], parts["label"]
print(f"\nGeometry ({PLATE_W} wide, {MARGIN_X} margins -> {USABLE} usable,"
      f" slot inner edge at {SLOT_IN_EDGE:.1f}):\n")
check(abs(P[2][0])<1e-3 and abs(P[2][1]-PLATE_T)<1e-3,
      f"plate spans z 0 .. {PLATE_T}")
for nm,G in (("text",T),("warn",W)):
    check(abs(G[2][0]-(PLATE_T-EMBED))<1e-3 and abs(G[2][1]-(PLATE_T+TEXT_H))<1e-3,
          f"{nm} spans z {PLATE_T-EMBED} .. {PLATE_T+TEXT_H} ({EMBED} embed)")

print()
# the rules are drawn exactly usable wide, so text may legitimately reach it
for nm,G,limit in (("text",T,USABLE/2), ("warn",W,USABLE/2)):
    reach = max(abs(G[0][0]), abs(G[0][1]))
    check(reach <= limit + 1e-3,
          f"{nm} reaches x +/-{reach:.2f}, within the {limit:.1f} text column")
for nm,G in (("text",T),("warn",W)):
    reach = max(abs(G[0][0]), abs(G[0][1]))
    check(reach <= SLOT_IN_EDGE,
          f"{nm} clears the zip-tie slots at +/-{SLOT_IN_EDGE:.1f}")
for nm,G in (("text",T),("warn",W)):
    inside = (G[0][0]>=P[0][0] and G[0][1]<=P[0][1] and G[1][0]>=P[1][0] and G[1][1]<=P[1][1])
    check(inside, f"{nm} stays inside the plate footprint")
check(abs(L[0][0]-P[0][0])<1e-3 and abs(L[0][1]-P[0][1])<1e-3,
      "label and plate share an origin")

print("\n  ALL CHECKS PASS\n" if not fails else
      f"\n  *** {len(fails)} CHECK(S) FAILED ***\n")
sys.exit(1 if fails else 0)
