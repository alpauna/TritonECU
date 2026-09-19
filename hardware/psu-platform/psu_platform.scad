// TritonECU — PSU mounting platform
// A Z-bracket. The module bolts down onto the UPPER flange (the one carrying
// the four 2 mm holes); the LOWER flange is the foot that fixes the bracket to
// whatever it stands on. Built from the hand drawing of 2026-09-19.
//
//   render one part at a time:  part = "platform"
//
//                     up_w 44.5
//            |<------------------------>|
//            +---------------------------+   ---
//            |  o                     o  | |  t     <- upper flange, holes here
//            +------------------------+--+   ---
//                                     |##|
//                                     |##|         <- web, t thick
//                              height |##| 51
//                                     |##|
//                                  +--+--+--------------+   ---
//                                  |                    | |  t  <- lower flange
//                                  +--------------------+   ---
//                                  |<------------------>|
//                                        lo_w 30
//
//   Total width  = up_w + lo_w = 74.5.  The web is the last t of up_w, which is
//   the only reading under which the two rectangles in the top view meet at one
//   line AND sum to the outside width. See README.md.

part = "platform";

/* Tessellation. Chord error is r*(1-cos(180/n)); a 2 mm hole at fn 32 is off by
   0.0024 mm, which is three orders below what the printer resolves. Holes are
   the only curved feature in the part, so there is nothing to economise on. */
$fn      = 32;
hole_fn  = 32;

/* ---------------------------------------------------------------------------
   FROM THE DRAWING — every number here is dimensioned on the sketch
   --------------------------------------------------------------------------- */
up_w    = 44.5;  // upper flange: outer tip to the OUTER face of the web
lo_w    = 30.0;  // lower flange: outer face of the web to its outer tip
height  = 51.0;  // OVERALL: top of the upper flange to the bottom of the lower
deep    = 92.0;  // both flanges, the depth of the extrusion

hole_d  =  2.0;  // "2 mm holes", dimensioned to hole CENTRES
hole_dx = 34.9;  // centre-to-centre, across the upper flange
hole_dy = 73.1;  // centre-to-centre, along the 92

/* ---------------------------------------------------------------------------
   NOT ON THE DRAWING — decisions, change them freely
   --------------------------------------------------------------------------- */

/* Plate and web thickness. The drawing shows a ribbon of constant thickness but
   never says how thick. 3 mm is the same as this repo's other printed plate.
   The web is the part that carries load: as a 92 x 3 plate its section modulus
   is b*t^2/6 = 138 mm^3, and a load on the middle of the upper flange acts at
   22.25 mm, so at a conservative 20 MPa for printed PETG it takes 124 N — about
   12 kg. The height does not enter that: a vertical load's moment at the root is
   set by the offset, not by how tall the web is. 3 mm is not the weak part. */
t         = 3.0;

/* Printed holes come out undersize by 0.2-0.4 mm on diameter — the first layer
   of the bore squashes inward. Same compensation as hardware/carrier-template.
   Set this to 0 if you want the model to carry the nominal 2.0 and intend to
   drill. A 2.0 mm hole modelled at 2.0 prints at roughly 1.7 and a 2 mm screw
   will not pass it. */
hole_comp = 0.30;

/* Hole pattern origin — the centre of the hole nearest the origin. The default
   centres the 34.9 x 73.1 pattern in the 44.5 x 92 flange, which is what the
   sketch shows to the accuracy a sketch has. If the real module's pattern is not
   centred, set these two and nothing else changes. */
hole_x0   = (up_w - hole_dx) / 2;   // 4.80
hole_y0   = (deep - hole_dy) / 2;   // 9.45

/* Optional corner ribs. OFF by default because the drawing has none and the
   web does not need them (see the 12 kg above). Turn them on if the load is
   ever sideways rather than down — that is the case the flat web is poor at. */
gusset    = false;
gusset_n  = 2;      // ribs per corner, spread along the 92
gusset_t  = 2.4;    // 3 perimeters at 0.4 mm line width, solid
gusset_l  = 12;     // how far the rib reaches along each leg

/* ---------------------------------------------------------------------------
   Geometry
   --------------------------------------------------------------------------- */
hole_r = (hole_d + hole_comp) / 2;
web_x  = up_w - t;          // inner face of the web
total_w = up_w + lo_w;

module ribs(x, z, dx, dz) {
    // A right triangle in X-Z, extruded along Y, repeated along the depth.
    for (i = [0 : gusset_n - 1]) {
        y = deep * (i + 0.5) / gusset_n - gusset_t / 2;
        translate([x, y, z])
            rotate([90, 0, 0])
                rotate([0, 0, 0])
                    translate([0, 0, -gusset_t])
                        linear_extrude(gusset_t)
                            polygon([[0, 0], [dx, 0], [0, dz]]);
    }
}

module platform() {
    difference() {
        union() {
            // upper flange — overlaps the web, so the union is solid, not a
            // pair of coincident faces
            translate([0, 0, height - t])   cube([up_w, deep, t]);
            // web, full height: it has to reach z=0, or its joint to the lower
            // flange is a line of zero area
            translate([web_x, 0, 0])        cube([t, deep, height]);
            // lower flange — starts at the web's INNER face for the same reason
            translate([web_x, 0, 0])        cube([lo_w + t, deep, t]);

            if (gusset) {
                // under the upper flange, reaching inboard along its underside
                ribs(web_x, height - t, -gusset_l, -gusset_l);
                // above the lower flange, reaching outboard
                ribs(up_w, t, gusset_l, gusset_l);
            }
        }
        // the four 2 mm holes, through the upper flange only
        for (i = [0, 1], j = [0, 1])
            translate([hole_x0 + i * hole_dx, hole_y0 + j * hole_dy, height - t - 1])
                cylinder(h = t + 2, r = hole_r, $fn = hole_fn);
    }
}

if (part == "platform") platform();

/* ---------------------------------------------------------------------------
   Checks — these print on every render, so they follow the parameters rather
   than the README
   --------------------------------------------------------------------------- */
echo(str("outside              ", total_w, " x ", deep, " x ", height, " mm"));
echo(str("upper flange         ", up_w, " x ", deep, ", holes in this one"));
echo(str("lower flange         ", lo_w, " x ", deep, " (", lo_w + t, " incl. web)"));
echo(str("plate/web thickness   ", t));
echo(str("hole modelled dia     ", hole_d + hole_comp, "  (nominal ", hole_d,
         " + ", hole_comp, " print compensation)"));
echo(str("hole centres  x       ", hole_x0, " and ", hole_x0 + hole_dx));
echo(str("hole centres  y       ", hole_y0, " and ", hole_y0 + hole_dy));
echo(str("edge margin to tip    ", hole_x0 - hole_r, " mm"));
echo(str("edge margin in y      ", hole_y0 - hole_r, " mm"));
echo(str("CLEARANCE, inboard hole to web face  ",
         web_x - (hole_x0 + hole_dx + hole_r),
         " mm  <-- a screw HEAD will not fit here, see README"));
echo(str("bed footprint, printed on end  ", total_w, " x ", height,
         "  and ", deep, " tall"));
