// Harness modernization label - TritonECU
//
// Affixed to the engine harness beside the EEC-V connector. It exists for one
// reason: this truck now has an ALWAYS-HOT lead straight off the battery post,
// and nothing else in the engine bay says so. Someone working on this vehicle
// in ten years - possibly not the person who built it - has to be able to find
// that out before they start cutting.
//
// Raised text on a flat plate. Every glyph sits in ONE Z plane, so a single
// filament change at `plate_t` prints it two-colour with no other work.
//
//   openscad -D 'part="label"' -o label.stl harness_label.scad
//
// PRINT IT IN PETG, ASA OR ABS. PLA creeps at engine-bay temperatures and a
// label that has slumped off its zip ties is worse than no label, because the
// next person will not know it was ever there.

part = "label";            // label

/* ---- plate ------------------------------------------------------------ */
plate_w   = 98;            // long axis
plate_t   = 2.4;           // base thickness
text_h    = 0.8;           // raised height - one filament change at plate_t
margin_x  = 7;             // side margin - must clear the zip slots, see assert
margin_y  = 6;             // top and bottom margin
corner_r  = 3;
chamfer   = 0.6;           // eases the edge so it is pleasant to handle

/* ---- zip-tie slots ---------------------------------------------------- */
// Obround, running along the plate's SHORT axis so a tie wraps the narrow way
// and pulls the label flat against the loom instead of cocking it.
slot_len  = 6.5;           // along Y - clears a standard 4.8 mm tie
slot_wid  = 2.2;           // along X
slot_in   = 4.5;           // side edge to slot CENTRE

/* ---- type ------------------------------------------------------------- */
FONT      = "Liberation Sans:style=Bold";
CHAR_W    = 0.62;          // width per point of size, Liberation Sans Bold.
                           // OpenSCAD 2021.01 has no textmetrics(), so the fit
                           // assert below estimates. Conservative on purpose.

// Each row is ["text", size, advance] or ["", 0, advance] for a rule.
// ADVANCE is the distance to the next row's baseline, so the plate height
// follows the content instead of being guessed.
rows = [
  ["TRITON ECU",                        7.0, 10.0],
  ["NOT A STOCK PCM - 99 F-150 5.4L",   3.6,  5.6],
  ["",                                  0,    4.2],   // rule
  ["! ALWAYS-HOT LEAD TO BATTERY +",    4.0,  6.0],
  ["2 A FUSE AT THE POST",              3.6,  5.4],
  ["ECU IS LIVE WITH THE KEY OFF",      3.6,  5.4],
  ["",                                  0,    4.2],   // rule
  ["ADDED PINS - unused on a stock truck", 3.1, 5.2],
  ["18 FAN 2      19 FAN 1",            3.6,  5.4],
  ["48 FRW 391    82 FRW 1138",         3.6,  5.4],
  ["",                                  0,    4.2],   // rule
  ["github.com/alpauna/TritonECU",      3.1,  5.0],
];

function sum(v, i = 0) = i >= len(v) ? 0 : v[i][2] + sum(v, i + 1);
function ytop(i, acc = 0, j = 0) = j >= i ? acc : ytop(i, acc + rows[j][2], j + 1);
function widest(i = 0) = i >= len(rows) ? 0 :
    max(len(rows[i][0]) * rows[i][1] * CHAR_W, widest(i + 1));

plate_h  = margin_y * 2 + sum(rows);
usable_w = plate_w - 2 * margin_x;

/* ---- verification before it reaches the plate -------------------------- */
assert(widest() <= usable_w,
       str("text overruns the plate: needs ", widest(), " mm, have ", usable_w));
// exact, not a proxy: the slot's inner edge must clear the text column
assert(plate_w/2 - slot_in - slot_wid/2 >= usable_w/2,
       str("zip slot overlaps the text column by ",
           usable_w/2 - (plate_w/2 - slot_in - slot_wid/2), " mm"));
assert(plate_w/2 - slot_in + slot_wid/2 <= plate_w/2 - 1,
       "zip slot breaks out of the plate edge");
assert(slot_len + 2 <= plate_h, "zip slot is longer than the plate is tall");
assert(text_h < plate_t, "raised text must be thinner than the plate");

module rounded_plate(w, h, t, r) {
    hull() for (x = [r - w/2, w/2 - r], y = [r - h/2, h/2 - r])
        translate([x, y, 0]) cylinder(r = r, h = t, $fn = 32);
}

module body() {
    difference() {
        // chamfer both faces by hulling a slightly inset slab at each end
        hull() {
            translate([0, 0, chamfer])
                rounded_plate(plate_w, plate_h, plate_t - 2*chamfer, corner_r);
            rounded_plate(plate_w - 2*chamfer, plate_h - 2*chamfer, plate_t, corner_r);
        }
        // zip-tie slots, one per end, straight through the plate
        for (s = [-1, 1])
            translate([s * (plate_w/2 - slot_in), 0, -1])
                hull() for (dy = [-(slot_len - slot_wid)/2, (slot_len - slot_wid)/2])
                    translate([0, dy, 0])
                        cylinder(d = slot_wid, h = plate_t + 2, $fn = 20);
    }
}

module engraving() {
    for (i = [0 : len(rows) - 1]) {
        y = plate_h/2 - margin_y - ytop(i) - rows[i][1];
        if (rows[i][0] == "")
            // rule: a thin bar across the text column
            translate([-usable_w/2, y + rows[i][1]/2, plate_t])
                cube([usable_w, 0.6, text_h]);
        else
            translate([0, y, plate_t])
                linear_extrude(text_h)
                    text(rows[i][0], size = rows[i][1], font = FONT,
                         halign = "center", valign = "baseline", $fn = 24);
    }
}

if (part == "label") { body(); engraving(); }
else assert(false, str("unknown part: ", part));

echo(str("label ", plate_w, " x ", plate_h, " x ", plate_t + text_h,
         "  (widest line ", widest(), " of ", usable_w, " usable)"));
