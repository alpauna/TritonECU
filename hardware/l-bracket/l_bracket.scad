// TritonECU — L bracket
// A right-angle bracket. A module bolts down onto the SHORT (top) leg through
// four holes on Ø5 x 3 standoffs; the TALL leg is the upright, and carries a
// pair of Ø3.5 holes on its midline that fix the bracket to whatever it hangs
// on. Built from the hand drawing of 2026-09-20.
//
//   render one part at a time:  part = "bracket"
//
//              leg_x 30
//     |<--------------------->|
//     +-----------------------+   ---
//     |  I                 I  | |  t   <- short leg, four standoffs on TOP
//     +--------------------+--+   ---
//                          |##|
//                          |##|
//                          |##|
//                  leg_z   |##|  50     <- tall leg, t thick
//                          |o#|             o = the Ø3.5 pair, on the midline
//                          |##|                 of the 50 deep face
//                          |o#|
//                          +--+   ---
//
//   Depth of both legs: 50. Overall 30 x 50 x 50 (53 to the standoff tips).

part = "bracket";

/* Tessellation. Chord error is r*(1-cos(180/n)); a 2 mm hole at fn 32 is off by
   0.0024 mm, three orders below what the printer resolves. Holes are the only
   curved feature, so there is nothing to economise on. */
$fn     = 32;
hole_fn = 32;

/* ---------------------------------------------------------------------------
   FROM THE DRAWING — every number here is dimensioned on the sketch
   --------------------------------------------------------------------------- */
leg_x   = 30.0;  // short leg: outer tip to the OUTER face of the tall leg.
                 // DRAWN 25.8 — raised to 30 on 2026-09-20 because a 23.8
                 // pattern in 25.8 leaves 1 mm to each edge and the bore opens
                 // onto it. See README, "How the drawing was read".
leg_z   = 50.0;  // OVERALL height: top face of the short leg to the free end
deep    = 50.0;  // both legs, the depth of the extrusion

top_dx  = 23.8;  // the four top holes, centre to centre ACROSS the short leg
top_dy  = 44.5;  // the four top holes, centre to centre ALONG the 50
top_d   =  2.0;  // "2 mm holes in the centre of the standoffs"

side_d  =  3.5;  // the pair in the tall leg
side_dz = 25.4;  // centre to centre, up the leg
side_z0 =  8.5;  // LOWER centre, up from the free end

/* ---------------------------------------------------------------------------
   NOT ON THE DRAWING — decisions, change them freely
   --------------------------------------------------------------------------- */

/* Plate and wall thickness. The drawing shows a ribbon of constant thickness
   but never says how thick. 3 mm, the same as hardware/psu-platform. The tall
   leg is the loaded member: as a 50 x 3 plate its section modulus is b*t^2/6 =
   75 mm^3, and a load in the middle of the short leg acts at 15 mm, so at a
   conservative 20 MPa for printed PETG it takes 100 N — about 10 kg. Height
   does not enter that; a vertical load's moment at the root is set by the
   offset, not by how tall the upright is. */
t         = 3.0;

/* Printed bores come out undersize by 0.2-0.4 mm on diameter — the first layer
   of the bore squashes inward. Both hole families are modelled OVERSIZE by this
   so they finish on their nominal: 2.0 -> 2.30, 3.5 -> 3.80. Set it to 0 if you
   would rather model nominal and drill. */
hole_comp = 0.30;

/* Standoffs on the four top holes, so the module sits clear of the plate — the
   usual reason being solder tails under its board. HEIGHT is the defining
   dimension: "3 mm standoff" means 3 mm of lift, not 3 mm of diameter. Ø5 round
   a Ø2.3 bore leaves a 1.35 mm wall; Ø3 would leave 0.35, under two extrusion
   widths, and would neither print nor hold. */
standoff   = true;
standoff_h = 3.0;
standoff_d = 5.0;

/* Hole pattern origins — the centre of the hole nearest the origin. Both
   default to the pattern CENTRED in the face, which is what the sketch shows to
   the accuracy a sketch has. If the real module's pattern is not centred, set
   these and nothing else changes. */
top_x0    = (leg_x - top_dx) / 2;   // 3.10
top_y0    = (deep  - top_dy) / 2;   // 2.75
side_y    = deep / 2;               // 25.00 — "the midline of the longer leg"

/* Optional corner ribs. OFF by default: the drawing has none and the upright
   does not need them (see the 10 kg above). Turn them on if the load is ever
   sideways rather than down — the case a flat plate is poor at. */
gusset    = false;
gusset_n  = 2;      // ribs, spread along the 50
gusset_t  = 2.4;    // 3 perimeters at 0.4 mm line width, solid
gusset_l  = 12;     // how far each rib reaches along each leg

/* ---------------------------------------------------------------------------
   Geometry
   --------------------------------------------------------------------------- */
top_r  = (top_d  + hole_comp) / 2;
side_r = (side_d + hole_comp) / 2;
wall_x = leg_x - t;              // 27.00 — inner face of the tall leg
top_z  = leg_z - t;              // 47.00 — underside of the short leg

module ribs() {
    // A right triangle in X-Z, extruded along Y, repeated along the depth.
    for (i = [0 : gusset_n - 1])
        translate([wall_x, deep * (i + 0.5) / gusset_n + gusset_t / 2, top_z])
            rotate([90, 0, 0])
                linear_extrude(gusset_t)
                    polygon([[0, 0], [-gusset_l, 0], [0, -gusset_l]]);
}

module bracket() {
    difference() {
        union() {
            // short leg — overlaps the upright, so the union is solid rather
            // than a pair of coincident faces
            translate([0, 0, top_z])     cube([leg_x, deep, t]);
            // tall leg, full height: it has to reach the top face, or its joint
            // to the short leg is a line of zero area
            translate([wall_x, 0, 0])    cube([t, deep, leg_z]);

            // standoffs, on TOP of the short leg, bored through below
            if (standoff)
                for (i = [0, 1], j = [0, 1])
                    translate([top_x0 + i * top_dx, top_y0 + j * top_dy, leg_z])
                        cylinder(h = standoff_h, d = standoff_d, $fn = hole_fn);

            if (gusset) ribs();
        }
        // the four 2 mm bores — through the short leg AND any standoff on it
        for (i = [0, 1], j = [0, 1])
            translate([top_x0 + i * top_dx, top_y0 + j * top_dy, top_z - 1])
                cylinder(h = t + (standoff ? standoff_h : 0) + 2, r = top_r,
                         $fn = hole_fn);

        // the Ø3.5 pair — through the tall leg, on its midline, axis along X
        for (k = [0, 1])
            translate([wall_x - 1, side_y, side_z0 + k * side_dz])
                rotate([0, 90, 0])
                    cylinder(h = t + 2, r = side_r, $fn = hole_fn);
    }
}

if (part == "bracket") bracket();

/* ---------------------------------------------------------------------------
   Checks — these print on every render, so they follow the parameters rather
   than the README
   --------------------------------------------------------------------------- */
echo(str("outside              ", leg_x, " x ", deep, " x ", leg_z, " mm"));
echo(str("short leg (platform) ", leg_x, " x ", deep, ", the four top holes"));
echo(str("tall leg  (upright)  ", leg_z, " x ", deep, ", t = ", t,
         ", inner face at x ", wall_x));
echo(str("TOP holes  modelled dia ", top_d + hole_comp, "  (", top_d,
         " nominal + ", hole_comp, " print compensation)"));
echo(str("  centres  x       ", top_x0, " and ", top_x0 + top_dx));
echo(str("  centres  y       ", top_y0, " and ", top_y0 + top_dy));
echo(str("  plate to the tip     ", top_x0 - top_r, " mm"));
echo(str("  plate in y           ", top_y0 - top_r, " mm"));
echo(str("SIDE holes modelled dia ", side_d + hole_comp, "  (", side_d,
         " nominal + ", hole_comp, ")"));
echo(str("  centres  z       ", side_z0, " and ", side_z0 + side_dz,
         "  up from the free end,  y ", side_y, " (midline)"));
echo(str("  plate below the lower  ", side_z0 - side_r, " mm"));
echo(str("  plate above the upper  ", top_z - (side_z0 + side_dz + side_r),
         " mm to the short leg's underside"));
echo(str("  plate either side      ", side_y - side_r, " mm"));
echo(str("INBOARD top bore vs the upright's inner face (x ", wall_x, "): centre ",
         wall_x - (top_x0 + top_dx), " mm outboard, bore reaches ",
         (top_x0 + top_dx + top_r) - wall_x,
         " mm INTO the upright's plan area"));
echo("  -> below that plate there is upright, not air: a NUT or SCREW HEAD");
echo("     cannot go under the inboard pair. Tap the plate (see README) or");
echo("     fasten those two from above into the module's own threads.");
if (standoff) {
    echo(str("standoffs             4 x ", standoff_d, " dia x ", standoff_h,
             " tall, on the short leg's TOP face"));
    echo(str("  wall around bore    ", (standoff_d - (top_d + hole_comp)) / 2,
             " mm",
             ((standoff_d - (top_d + hole_comp)) / 2 < 0.8)
               ? "  <-- UNDER 2 extrusion widths, raise standoff_d" : "  (ok)"));
    echo(str("  boss to the tip     ", top_x0 - standoff_d / 2, " mm",
             (top_x0 - standoff_d / 2 < 0) ? "  <-- OVERHANGS the edge" : ""));
    echo(str("  boss to the y edge  ", top_y0 - standoff_d / 2, " mm",
             (top_y0 - standoff_d / 2 < 0) ? "  <-- OVERHANGS the edge" : ""));
    echo(str("  thread stack        ", t + standoff_h,
             " mm of plate + standoff — ", (t + standoff_h) / top_d,
             " diameters of M2 if tapped"));
    echo(str("  overall height      ", leg_z + standoff_h,
             " mm to the standoff tips (part itself is still ", leg_z, ")"));
}
echo(str("bed footprint, printed on end  ", leg_x, " x ", leg_z,
         "  and ", deep, " tall"));
