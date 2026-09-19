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

part = "label";            // label | plate | text | warn
//
// MULTI-COLOUR: render plate, text and warn separately and load all three
// into the slicer as ONE multi-part object - they share an origin, so they
// land aligned. Assign the warning its own filament.
//   plate  the body
//   text   everything except the warning block
//   warn   the three warning lines, meant to be RED
// "label" is all of it in one piece, for a single-colour print or a plain
// filament change at plate_t.

/* ---- plate ------------------------------------------------------------ */
plate_w   = 98;            // long axis
plate_t   = 2.4;           // base thickness
text_h    = 0.8;           // raised height - one filament change at plate_t
embed     = 0.2;           // glyphs sink this far INTO the plate. Exact
                           // coincident faces confuse some slicers; a small
                           // overlap makes the multi-part union unambiguous
                           // and is buried, so it never shows.
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
CHAR_W    = 0.80;          // width per point of size, Liberation Sans Bold.
                           // OpenSCAD 2021.01 has no textmetrics(), so the fit
                           // assert below can only ESTIMATE.
                           //
                           // CALIBRATED, not guessed. This was 0.62 and that
                           // was wrong in the UNSAFE direction: three rows
                           // passed the assert and overran the plate, one of
                           // them into the zip-tie slots. Measured off the
                           // rendered warn.stl - 30 chars at size 4.0 came out
                           // 94.4 mm, so 94.4/(30*4.0) = 0.787. Rounded up.
                           //
                           // AN ESTIMATE IS NOT A CHECK. verify.py measures
                           // the actual STLs and is what now guards this.

// Each row is ["text", size, advance, group], or ["", 0, advance, group]
// for a rule. ADVANCE is the distance to the next row's baseline, so the
// plate height follows the content instead of being guessed.
// GROUP is "t" for ordinary text or "w" for the warning block - it is what
// splits the STLs. The rules stay "t" so they bracket the warning rather
// than joining it.
rows = [
  ["TRITON ECU",                        7.0, 10.0, "t"],
  ["NOT STOCK - 1999 F-150 5.4L",       3.5,  5.6, "t"],
  ["",                                  0,    4.2, "t"],   // rule
  ["! ALWAYS-HOT BATTERY LEAD",         4.0,  6.0, "w"],
  ["2 A FUSE AT THE POST",              3.6,  5.4, "w"],
  ["ECU IS LIVE WITH KEY OFF",          3.6,  5.4, "w"],
  ["",                                  0,    4.2, "t"],   // rule
  ["ADDED PINS - unused by Ford",       3.1,  5.2, "t"],
  ["18 FAN 2      19 FAN 1",            3.6,  5.4, "t"],
  ["48 FRW 391    82 FRW 1138",         3.6,  5.4, "t"],
  ["",                                  0,    4.2, "t"],   // rule
  ["github.com/alpauna/TritonECU",      3.1,  5.0, "t"],
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

// group = "t", "w", or "*" for everything
module engraving(group = "*") {
    for (i = [0 : len(rows) - 1])
        if (group == "*" || rows[i][3] == group) {
            y = plate_h/2 - margin_y - ytop(i) - rows[i][1];
            if (rows[i][0] == "")
                // rule: a thin bar across the text column
                translate([-usable_w/2, y + rows[i][1]/2, plate_t - embed])
                    cube([usable_w, 0.6, text_h + embed]);
            else
                translate([0, y, plate_t - embed])
                    linear_extrude(text_h + embed)
                        text(rows[i][0], size = rows[i][1], font = FONT,
                             halign = "center", valign = "baseline", $fn = 24);
        }
}

function n_in(g, i = 0) = i >= len(rows) ? 0 :
    (rows[i][3] == g ? 1 : 0) + n_in(g, i + 1);

assert(n_in("w") > 0, "no rows are in the warning group - nothing to print red");
assert(n_in("t") > 0, "no rows are in the text group");

if      (part == "label") { body(); engraving(); }
else if (part == "plate")   body();
else if (part == "text")    engraving("t");
else if (part == "warn")    engraving("w");
else assert(false, str("unknown part: ", part,
                       " - expected label, plate, text or warn"));

echo(str("label ", plate_w, " x ", plate_h, " x ", plate_t + text_h,
         "  (widest line ", widest(), " of ", usable_w, " usable; ",
         n_in("t"), " text rows, ", n_in("w"), " warning rows)"));
