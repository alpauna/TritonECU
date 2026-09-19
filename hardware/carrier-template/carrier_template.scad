// Carrier board template — a measurement jig for the donor ECU case
//
// This is NOT a check of a finished layout. It is the instrument that
// CAPTURES the numbers the layout is waiting on, because the one thing we do
// not have is where the case's mounting bosses sit relative to the board
// outline. Drop it in the case floor, read the boss centres off the grid,
// and the carrier can be drawn.
//
//   ./render.sh          ->  stl/template.stl, stl/ring.stl
//
// PRINT IN PLA. The opposite of the harness label: this is a room-temperature
// jig, and PLA is the least warp-prone thing for a 158 x 174 flat plate. PETG
// and ABS will curl at the corners and a curled datum is worthless.

part = "template";         // template | ring

/* ---- the envelope, known ------------------------------------------------ */
plate_w   = 158;           // donor PCB width   - carrier-envelope.md
plate_l   = 174;           // donor PCB length
plate_t   = 2.0;           // thick enough not to flex, thin enough to print fast
undersize = 0.5;           // shrink per side so it DROPS IN rather than jams

/* ---- grid --------------------------------------------------------------- */
grid      = 10;            // pitch, mm
grid_w    = 0.6;           // engraved line width
grid_d    = 0.6;           // engraved depth
major     = 50;            // bolder line every this many mm
major_w   = 1.2;
label_ev  = 20;            // number the axes every this many mm
label_sz  = 4.0;

/* ---- EEC-V connector pin field ------------------------------------------ */
// Geometry is KNOWN (rusEFI, verified) - connector-sourcing.md.
// POSITION on the board is ESTIMATED and is one of the things to check.
pin_w     = 101.4;         // pin field width   KNOWN
pin_h     = 9.0;           // pin field depth   KNOWN
pin_x     = 0;             // offset from board centreline   ** ESTIMATED **
pin_edge  = 8.0;           // pin field centre to board edge ** ESTIMATED **

/* ---- edge cooling band -------------------------------------------------- */
// The zone where power devices MUST sit to reach the case rails.
band      = 12;            // carrier-envelope.md, edge cooling
band_d    = 0.4;

/* ---- ring variant ------------------------------------------------------- */
ring_w    = 16;            // frame width - wide enough to span the rails

W = plate_w - 2*undersize;
L = plate_l - 2*undersize;

/* ---- verification before any geometry ----------------------------------- */
assert(pin_w < W - 10, "pin field is wider than the plate allows");
assert(pin_edge - pin_h/2 > 1, "pin field runs off the board edge");
assert(band*2 < min(W,L), "edge band would meet in the middle");
assert(ring_w > band, "ring is narrower than the edge-cooling band it must show");
assert(grid_d < plate_t - 0.8, "grid engraving leaves too little plate under it");

module engrave(x0,y0,x1,y1,w) {
    hull() for (p = [[x0,y0],[x1,y1]])
        translate([p[0], p[1], plate_t - grid_d])
            cylinder(d = w, h = grid_d + 1, $fn = 12);
}

module grid_lines() {
    for (x = [-floor(W/2/grid)*grid : grid : W/2])
        engrave(x, -L/2, x, L/2, abs(x) % major == 0 ? major_w : grid_w);
    for (y = [-floor(L/2/grid)*grid : grid : L/2])
        engrave(-W/2, y, W/2, y, abs(y) % major == 0 ? major_w : grid_w);
}

module axis_labels() {
    for (x = [-floor(W/2/label_ev)*label_ev : label_ev : W/2])
        translate([x, -L/2 + 4, plate_t - grid_d])
            linear_extrude(grid_d + 1)
                text(str(x), size = label_sz, halign = "center",
                     valign = "baseline", font = "Liberation Sans", $fn = 16);
    for (y = [-floor(L/2/label_ev)*label_ev : label_ev : L/2])
        translate([-W/2 + 4, y, plate_t - grid_d])
            linear_extrude(grid_d + 1)
                text(str(y), size = label_sz, halign = "left",
                     valign = "center", font = "Liberation Sans", $fn = 16);
}

module edge_band() {
    difference() {
        translate([0,0,plate_t-band_d]) cube([W, L, band_d+1], center = true);
        translate([0,0,plate_t-band_d-0.5])
            cube([W-2*band, L-2*band, band_d+2], center = true);
    }
}

// Orientation key: a corner chamfer that cannot be mistaken, at +X +Y.
// Without it the plate reads the same rotated 180 and the grid signs invert.
module key() {
    translate([W/2, L/2, -1]) rotate([0,0,45])
        cube([14, 14, plate_t+2], center = true);
}

module plate_body(ring = false) {
    difference() {
        translate([0,0,plate_t/2]) cube([W, L, plate_t], center = true);
        if (ring)
            translate([0,0,-1]) cube([W-2*ring_w, L-2*ring_w, plate_t+2], center = true);
        key();
        // connector pin field, through - check it against the case opening
        translate([pin_x, L/2 - pin_edge, -1])
            cube([pin_w, pin_h, plate_t+2], center = true);
    }
}

if (part == "template") {
    difference() { plate_body(false); grid_lines(); axis_labels(); edge_band(); }
} else if (part == "ring") {
    difference() { plate_body(true); grid_lines(); edge_band(); }
} else assert(false, str("unknown part: ", part));

echo(str("template ", W, " x ", L, " x ", plate_t,
         "  pin field ", pin_w, " x ", pin_h,
         " at x=", pin_x, ", ", pin_edge, " mm from the +Y edge  [ESTIMATED]"));
