// TritonECU — PSU pad
// A flat plate, not a bracket. Stepped outline: a full-width body with a raised
// centre section. The module bolts onto it through four Ø5 x 3 standoffs; two
// Ø3.5 holes at the bottom corners fix the pad down. Built from the hand
// drawing of 2026-09-20.
//
//   render one part at a time:  part = "pad"
//
//     |<-45->|<------ 108 ------>|<-11.4->|
//            +-------------------+           ---
//            |  I             I  |            |     <- raised section
//     +------+                   +--------+   |   71.5
//     |                                   |  50.8
//     |  o   I             I           o  |   |     <- o = Ø3.5, I = standoff
//     +-----------------------------------+  ---
//     |<-------------- 164.4 ------------>|
//
//   standoffs: 100 across x 63.5 along, centred in the RAISED SECTION and in
//   the 71.5. Ø3.5 pair: 152.4 apart, 6.4 up from the bottom edge.

part = "pad";

/* Tessellation. Chord error is r*(1-cos(180/n)); a 3.5 mm hole at fn 32 is off
   by 0.0042 mm, orders below what the printer resolves. */
$fn     = 32;
hole_fn = 32;

/* ---------------------------------------------------------------------------
   FROM THE DRAWING — every number here is dimensioned on the sketch
   --------------------------------------------------------------------------- */
pad_w    = 164.4;  // overall width
pad_h    =  71.5;  // overall height, bottom edge to the top of the raised part
shoulder =  50.8;  // height of the full-width body — where the step happens
step_l   =  45.0;  // left edge to the raised section
step_w   = 108.0;  // width of the raised section
step_r_g =  11.4;  // raised section to the right edge  (45 + 108 + 11.4 = 164.4)

fix_dx   = 152.4;  // the Ø3.5 pair, centre to centre
fix_y    =   6.4;  // their centres, up from the bottom edge
fix_d    =   3.5;

pat_dx   = 100.0;  // the four standoff holes, across
pat_dy   =  63.5;  // the four standoff holes, along
pat_d    =   2.0;  // "2 mm hole" in the centre of each standoff

/* ---------------------------------------------------------------------------
   NOT ON THE DRAWING — decisions, change them freely
   --------------------------------------------------------------------------- */

/* Thickness. The drawing gives none. 3 mm, the same as every other plate in
   this repo. A pad is not a bracket: it carries the module in COMPRESSION into
   whatever it is screwed to, so the 3 mm is about handling and screw seats
   rather than bending. */
t         = 3.0;

/* Printed bores come out undersize by 0.2-0.4 mm on diameter. Both hole
   families are modelled OVERSIZE by this so they finish on nominal:
   2.0 -> 2.30 and 3.5 -> 3.80. Set to 0 to model nominal and drill. */
hole_comp = 0.30;

/* Standoffs, same as hardware/l-bracket and hardware/psu-platform: 3 mm of
   LIFT, Ø5 so a Ø2.3 bore keeps a 1.35 mm wall. */
standoff   = true;
standoff_h = 3.0;
standoff_d = 5.0;

/* Fillet in the two re-entrant corners of the step. OFF (0) because the drawing
   shows square corners and a pad is not a loaded part. A few mm here is free
   insurance if it ever gets flexed: those corners are the only stress risers in
   the outline. */
step_fill = 0.0;

/* Hole pattern origin. The sketch centres the 100 x 63.5 pattern in the RAISED
   SECTION across, and in the 71.5 along — measured off the drawing, the pattern
   centre lands within 1 mm of the raised section's centre and nowhere near the
   plate's. Set these two if the real module says otherwise. */
pat_x0    = step_l + (step_w - pat_dx) / 2;   // 49.00
pat_y0    = (pad_h - pat_dy) / 2;             // 4.00

/* ---------------------------------------------------------------------------
   Geometry
   --------------------------------------------------------------------------- */
pat_r  = (pat_d + hole_comp) / 2;
fix_r  = (fix_d + hole_comp) / 2;
step_x = step_l + step_w;                     // 153.00, right edge of the step
fix_x0 = (pad_w - fix_dx) / 2;                // 6.00

module outline() {
    pts = [[0, 0], [pad_w, 0], [pad_w, shoulder], [step_x, shoulder],
           [step_x, pad_h], [step_l, pad_h], [step_l, shoulder], [0, shoulder]];
    if (step_fill > 0)
        // dilate then erode: rounds the CONCAVE corners, leaves the rest sharp
        offset(r = -step_fill) offset(r = step_fill) polygon(pts);
    else
        polygon(pts);
}

module pad() {
    difference() {
        union() {
            linear_extrude(t) outline();
            if (standoff)
                for (i = [0, 1], j = [0, 1])
                    translate([pat_x0 + i * pat_dx, pat_y0 + j * pat_dy, t])
                        cylinder(h = standoff_h, d = standoff_d, $fn = hole_fn);
        }
        // four 2 mm bores, through plate and standoff together
        for (i = [0, 1], j = [0, 1])
            translate([pat_x0 + i * pat_dx, pat_y0 + j * pat_dy, -1])
                cylinder(h = t + (standoff ? standoff_h : 0) + 2, r = pat_r,
                         $fn = hole_fn);
        // the Ø3.5 pair
        for (i = [0, 1])
            translate([fix_x0 + i * fix_dx, fix_y, -1])
                cylinder(h = t + 2, r = fix_r, $fn = hole_fn);
    }
}

if (part == "pad") pad();

/* ---------------------------------------------------------------------------
   Checks — these print on every render, so they follow the parameters rather
   than the README
   --------------------------------------------------------------------------- */
echo(str("outline              ", pad_w, " x ", pad_h, " x ", t, " mm"));
echo(str("  body (full width)  0 .. ", shoulder, ",  raised section ", shoulder,
         " .. ", pad_h, " over x ", step_l, " .. ", step_x));
echo(str("  WIDTH CHECK        ", step_l, " + ", step_w, " + ", step_r_g, " = ",
         step_l + step_w + step_r_g, "  vs overall ", pad_w,
         (abs(step_l + step_w + step_r_g - pad_w) < 0.001)
           ? "  (exact — this is what fixes the reading)"
           : "  <-- DOES NOT CLOSE, one of the four is wrong"));
echo(str("standoff holes  dia  ", pat_d + hole_comp, " (", pat_d, " + ",
         hole_comp, ")   pattern ", pat_dx, " x ", pat_dy));
echo(str("  centres  x         ", pat_x0, " and ", pat_x0 + pat_dx));
echo(str("  centres  y         ", pat_y0, " and ", pat_y0 + pat_dy));
echo(str("  top row sits ", pad_h - (pat_y0 + pat_dy),
         " below the top edge, bottom row ", pat_y0, " above the bottom"));
echo(str("  in the raised section, each side  ",
         pat_x0 - step_l, " mm to the step edge"));
echo(str("Ø", fix_d, " pair  dia ", fix_d + hole_comp, "   centres x ", fix_x0,
         " and ", fix_x0 + fix_dx, ",  y ", fix_y));
echo(str("  plate round them   ", fix_x0 - fix_r, " mm to the side edge, ",
         fix_y - fix_r, " mm to the bottom"));
if (standoff) {
    echo(str("standoffs            4 x ", standoff_d, " dia x ", standoff_h,
             " tall, on the TOP face"));
    echo(str("  wall around bore   ", (standoff_d - (pat_d + hole_comp)) / 2,
             " mm",
             ((standoff_d - (pat_d + hole_comp)) / 2 < 0.8)
               ? "  <-- UNDER 2 extrusion widths, raise standoff_d" : "  (ok)"));
    echo(str("  bottom row boss to the bottom edge  ",
             pat_y0 - standoff_d / 2, " mm",
             (pat_y0 - standoff_d / 2 < 0) ? "  <-- OVERHANGS" : ""));
    echo(str("  top row boss to the top edge        ",
             pad_h - (pat_y0 + pat_dy) - standoff_d / 2, " mm",
             (pad_h - (pat_y0 + pat_dy) - standoff_d / 2 < 0)
               ? "  <-- OVERHANGS" : ""));
    echo(str("  boss to the step's side edges       ",
             pat_x0 - step_l - standoff_d / 2, " mm",
             (pat_x0 - step_l - standoff_d / 2 < 0) ? "  <-- OVERHANGS" : ""));
    echo(str("  thread stack       ", t + standoff_h, " mm — ",
             (t + standoff_h) / pat_d, " diameters of M2 if tapped"));
    echo(str("  overall height     ", t + standoff_h, " mm to the tips"));
}
echo(str("bed footprint          ", pad_w, " x ", pad_h,
         "  — flat, every bore vertical"));
