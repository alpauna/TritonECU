// TritonECU — 36-1 VR trigger wheel test rig
// Printed parts only. The toothed wheel itself MUST be steel (see README.md).
//
//   render one part at a time:  part = "bearing_block" | "motor_mount"
//                                      | "wheel_hub" | "cam_target" | "sensor_mount"
//                                      | "crank_gear" | "cam_gear"
//                                      | "base" | "assembly"

part = "assembly";

/* Tessellation. $fn = 64 everywhere costs minutes in CGAL for no benefit: the
   base's 192-hole M4 grid alone was 12288 facets of subtraction. Chord error is
   r*(1-cos(180/n)), so a 4.4 mm clearance hole at fn 16 is off by 0.04 mm --
   below what the printer resolves. Spend the facets only where a fit depends on
   them. */
$fn      = 32;   // general
hole_fn  = 16;   // M3/M4 clearance holes -- 0.04 mm chord error
fit_fn   = 64;   // bearing pocket, shaft and sensor bores: real fits
root_fn  = 120;  // gear root circle

/* ---------------------------------------------------------------------------
   MEASURE THESE THREE before printing — everything else follows from them
   --------------------------------------------------------------------------- */
wheel_od        = 150.0;  // MEASURE: trigger wheel outside diameter
wheel_thk       =   5.0;  // MEASURE: wheel thickness
wheel_bore      =  24.0;  // wheel centre bore — 24 mm, keyed
key_w           =   8.0;  // MEASURE: keyway width  (DIN 6885 for 24 mm is 8 mm)
key_d           =   3.3;  // MEASURE: keyway depth into the bore
key_to_gap      =   0;    // degrees from keyway to the MISSING TOOTH.
                          // 0 on this wheel: the keyway is inline with the gap.
                          // The index flute on the flange OD is cut at this angle,
                          // so the flute always points at the gap.
sensor_dia      =  19.0;  // MEASURE: VR sensor barrel diameter (Ford CKP)
sensor_flat     =   0;    // set >0 if the sensor body has a flat, for anti-rotation

/* --- cam channel (CMP) — 2:1 gear driven, see README ----------------------- */
cam_target_od   =  60.0;  // printed disc; only the insert needs to be steel
cam_bolt        =   8.0;  // M8 shank — this is the face the sensor sees, head inward
cam_head_af     =  13.0;  // M8 hex across flats, for the captive pocket
cam_head_thk    =   5.5;  // M8 head height
/* Counterweight, cancelling the M8 trigger bolt's ~480 g.mm.
   The pocket is a slip fit on 14 mm brass rod, deliberately DEEPER than needed:
   you balance by cutting the rod to length, not by trusting this arithmetic.
   Expect roughly 15 mm of rod — the printed boss is itself 4.8 g at r 19.5 and
   already does about a fifth of the job.
   Capacity is 29 g brass / 39 g lead, so either material reaches balance.
   The fill must be NON-FERROUS: the boss reaches r 29.7 against a 30 mm rim, so
   it passes the sensor every revolution and steel would be a second VR trigger. */
cw_r            =  19.5;  // pocket centre radius
cw_dia          =  14.4;  // slip fit on 14 mm rod stock — CUT THE ROD TO BALANCE
cw_depth        =  21.0;  // deeper than needed, so there is length to trim
cw_boss          = 20.4;  // spans r 9.3..29.7, inside the 30 mm rim
cw_h            =  23.0;
cam_gear_teeth  =  40;    // 2 : 1 against crank_gear_teeth
crank_gear_teeth=  20;
gear_module     =   2.0;  // centre distance = module*(20+40)/2 = 60 mm.
                          // NOT module 1: a 0.4 mm nozzle cannot render a
                          // 1.57 mm pitch-circle tooth accurately. See README.
gear_pa         =  20;    // pressure angle
gear_w          =  10;    // face width

/* --- stock parts, change only if you buy different ones -------------------- */
shaft_dia       =   8.0;  // 8 mm ground steel rod
brg_od          =  22.0;  // 608ZZ
brg_id          =   8.0;
brg_w           =   7.0;
nema            =  42.3;  // NEMA 17 body
nema_bolt       =  31.0;  // bolt circle (square pattern)
nema_boss       =  22.0;
nema_shaft      =   5.0;

/* --- fit and print tuning -------------------------------------------------- */
brg_press       =  -0.05; // bearing OD interference; loosen toward +0.10 if it will not seat
clr             =   0.25; // general clearance
wall            =   4.0;
base_t          =   8.0;
plate_w         = 100.0;

/* --- derived --------------------------------------------------------------- */
shaft_h  = wheel_od/2 + 12;          // shaft centreline above the base top
blk_w    = brg_od + 2*wall;
blk_h    = shaft_h + brg_od/2 + wall;
gap_slot = 14;                       // sensor air-gap adjustment travel

/* ===========================================================================
   BEARING BLOCK  x2 — 608 bearings, shaft through
   =========================================================================== */
module bearing_block() {
    difference() {
        union() {
            // upright
            translate([-blk_w/2, -brg_w/2 - wall, 0]) cube([blk_w, brg_w + 2*wall, blk_h]);
            // foot
            translate([-blk_w/2 - 8, -brg_w/2 - wall, 0]) cube([blk_w + 16, brg_w + 2*wall, base_t]);
            // gussets — a printed upright this tall WILL flex without them
            for (s = [-1, 1]) scale([s,1,1])
                translate([blk_w/2, -brg_w/2 - wall, 0])
                    rotate([90,0,90]) linear_extrude(wall)
                        polygon([[0,0],[14,0],[0,blk_h*0.6]]);
        }
        // bearing pocket, through
        translate([0, -brg_w/2 - wall - 1, shaft_h])
            rotate([-90,0,0]) cylinder(d = brg_od + brg_press, h = brg_w + 2*wall + 2, $fn = fit_fn);
        // shaft relief either side so the bearing seats on its outer race only
        translate([0, -brg_w/2 - wall - 2, shaft_h])
            rotate([-90,0,0]) cylinder(d = brg_od - 4, h = brg_w + 2*wall + 4);
        // M4 feet
        for (x = [-blk_w/2 - 4, blk_w/2 + 4])
            translate([x, 0, -1]) cylinder(d = 4.4, $fn = hole_fn, h = base_t + 2);
    }
}

/* ===========================================================================
   MOTOR MOUNT — NEMA 17 face plate
   =========================================================================== */
module motor_mount() {
    h = shaft_h + nema/2 + wall;
    difference() {
        union() {
            translate([-nema/2 - wall, -wall, 0]) cube([nema + 2*wall, wall, h]);
            translate([-nema/2 - wall - 8, -wall, 0]) cube([nema + 2*wall + 16, wall + 14, base_t]);
            for (s = [-1,1]) scale([s,1,1])
                translate([nema/2 + wall, -wall, 0])
                    rotate([90,0,90]) linear_extrude(wall)
                        polygon([[0,0],[14,0],[0,h*0.6]]);
        }
        translate([0, -wall - 1, shaft_h]) rotate([-90,0,0]) {
            cylinder(d = nema_boss + 1, h = wall + 2);          // boss clearance
            for (a = [45:90:315])                                // M3 pattern
                rotate([0,0,a]) translate([nema_bolt/sqrt(2), 0, 0])
                    translate([0,0,-1]) cylinder(d = 3.4, $fn = hole_fn, h = wall + 4);
        }
        for (x = [-nema/2 - wall - 4, nema/2 + wall + 4])
            translate([x, 3, -1]) cylinder(d = 4.4, $fn = hole_fn, h = base_t + 2);
    }
}

/* ===========================================================================
   HUB — clamps the steel wheel to the shaft.
   Split clamp, NOT a grub screw: 0.7 kg of steel must not be able to walk off.
   =========================================================================== */
hub_od = max(wheel_bore + 16, 46);
module hub() {
    difference() {
        union() {
            cylinder(d = hub_od, h = 16);
            cylinder(d = wheel_bore - clr, $fn = fit_fn, h = 16 + wheel_thk);   // spigot locates the wheel
        }
        translate([0,0,-1]) cylinder(d = shaft_dia + clr, $fn = fit_fn, h = 40); // shaft bore
        translate([-0.9, -hub_od, 8]) cube([1.8, hub_od, 40]);     // clamp slit
        // clamp screw, M4 across the slit
        translate([-hub_od/2 - 1, 0, 24]) rotate([0,90,0]) cylinder(d = 4.4, $fn = hole_fn, h = hub_od + 2);
        translate([ 1.5, 0, 24]) rotate([0,90,0]) cylinder(d = 7.6, h = hub_od, $fn = 6); // nut trap
        // wheel bolts — 3 x M4 on a circle, adjust to the wheel you buy
        for (a = [0:120:359]) rotate([0,0,a])
            translate([hub_od/2 - 7, 0, -1]) cylinder(d = 4.4, $fn = hole_fn, h = 20);
    }
}

/* ===========================================================================
   WHEEL HUB — 24 mm keyed spigot to 8 mm shaft, with a gear mounting face.
   Print BORE AXIS VERTICAL: both diameters are then formed by the same X-Y
   motion on every layer, so they are concentric to printer X-Y accuracy rather
   than to layer stacking. Concentricity here is wheel runout, which is air-gap
   modulation.
   =========================================================================== */
wh_flange = wheel_bore + 22;
wh_spig_l = wheel_thk + 3;
module wheel_hub() {
    difference() {
        union() {
            cylinder(d = wh_flange, h = 10);                    // flange + gear face
            translate([0,0,10]) cylinder(d = wheel_bore - clr, $fn = fit_fn, h = wh_spig_l);
            // Integral key, formed in X-Y with the spigot. It must stand PROUD
            // of the spigot by the wheel's keyway depth — the spigot fills the
            // 24 mm bore, and the key fills the slot cut outward from it. The
            // cube runs from the axis so it merges with the spigot; only the
            // part past r = 11.875 does any work.
            translate([0,0,10])
                translate([0, -key_w/2 + clr/2, 0])
                    cube([wheel_bore/2 + key_d - 0.1, key_w - clr, wh_spig_l]);
        }
        translate([0,0,-1]) cylinder(d = shaft_dia + clr, $fn = fit_fn, h = 40);   // shaft bore
        translate([-0.9, -wh_flange, 3]) cube([1.8, wh_flange, 40]); // clamp slit
        translate([-wh_flange/2 - 1, 0, 6]) rotate([0,90,0]) cylinder(d = 4.4, $fn = hole_fn, h = wh_flange + 2);
        translate([ 1.5, 0, 6]) rotate([0,90,0]) cylinder(d = 7.6, h = wh_flange, $fn = 6);
        // wheel retention — bolts through the flange into the wheel, if it has holes
        for (a = [60:120:359]) rotate([0,0,a])
            translate([wheel_bore/2 + 4, 0, -1]) cylinder(d = 4.4, $fn = hole_fn, h = 12);
        // INDEX FLUTE on the flange OD, at key_to_gap from the key. Once the wheel
        // is on, the teeth all look alike and the gap is hard to find by eye. This
        // flute points at it, so the assembled rig has a visible angular zero to
        // set the stepper's home position against.
        rotate([0, 0, key_to_gap])
            translate([wh_flange/2, 0, -1]) cylinder(d = 3, h = 12);
    }
}

/* ===========================================================================
   CAM TARGET HUB — printed disc, one steel insert, adjustable phase.
   The clamp is deliberately separate from the insert so the phase can be
   swept without disturbing the lobe.
   =========================================================================== */
module cam_target() {
    difference() {
        union() {
            cylinder(d = cam_target_od, h = 5);
            cylinder(d = hub_od, h = 16);
            // COUNTERWEIGHT BOSS, 180 deg from the trigger bolt. Overlaps the hub
            // (13..30 vs 0..23) so it needs no blending geometry.
            rotate([0,0,180]) translate([cw_r,0,0]) cylinder(d = cw_boss, h = cw_h);
        }
        // Pocket opens AXIALLY, for the same reason the bolt head faces inward:
        // centripetal load presses the lead against the outer wall rather than
        // out of the opening. Fill with lead until the disc balances.
        rotate([0,0,180]) translate([cw_r, 0, 2])
            cylinder(d = cw_dia, h = cw_depth + 1);
        // M3 grub screw through the outer wall, to trap the fill
        rotate([0,0,180]) translate([cw_r, 0, cw_h - 6]) rotate([0,90,0])
            cylinder(d = 2.5, $fn = hole_fn, h = cw_boss/2 + 3);
        translate([0,0,-1]) cylinder(d = shaft_dia + clr, $fn = fit_fn, h = 40);
        // RADIAL bolt, HEAD INWARD. Centripetal load pushes the bolt outward, so
        // the head bears against the pocket and cannot pull through. The feature
        // presented to the sensor is then the 8 mm shank end, not the 13 mm head.
        translate([0, 0, 2.5]) rotate([0,90,0])
            cylinder(d = cam_bolt + 0.4, h = cam_target_od/2 + 1);   // shank clearance
        // hex pocket for the head — anti-rotation, and the load-bearing face
        translate([hub_od/2 - 1, 0, 2.5]) rotate([0,90,0])
            cylinder(d = cam_head_af / cos(30), h = cam_head_thk, $fn = 6);
        // split clamp, same pattern as hub()
        translate([-0.9, -hub_od, 6]) cube([1.8, hub_od, 40]);
        translate([-hub_od/2 - 1, 0, 11]) rotate([0,90,0]) cylinder(d = 4.4, $fn = hole_fn, h = hub_od + 2);
        translate([ 1.5, 0, 11]) rotate([0,90,0]) cylinder(d = 7.6, h = hub_od, $fn = 6);
    }
}

/* ===========================================================================
   INVOLUTE SPUR GEAR — self contained, no library.

   Involute geometry: at radius r the flank sits at polar angle inv(acos(rb/r)),
   where inv(a) = tan(a) - a is the involute function. Offsetting so the flank
   crosses the pitch circle at half a tooth thickness (90/z degrees) puts the
   tooth symmetric about 0.

   Below the base circle the involute does not exist, so the flank runs radially
   from rb down to the root. For z < 41 at 20 degrees PA the root is inside the
   base circle, which is the case for both gears here.
   =========================================================================== */
function inv_deg(a) = (tan(a) - a*PI/180) * 180/PI;

module gear_blank(m, z, w) {
    rp = m*z/2;                 // pitch
    rb = rp*cos(gear_pa);       // base
    ra = rp + m;                // addendum (tip)
    rf = rp - 1.25*m;           // dedendum (root)
    r0 = max(rb, rf);
    half = 90/z;                // half tooth angle at the pitch circle
    n  = 10;
    fl = [for (i = [0:n])
             let(r = r0 + (ra - r0)*i/n,
                 a = inv_deg(acos(rb/r)) - inv_deg(gear_pa) - half)
             [r*cos(a), r*sin(a)]];
    a0 = inv_deg(acos(rb/r0)) - inv_deg(gear_pa) - half;
    linear_extrude(w) union() {
        circle(r = rf, $fn = root_fn);
        for (i = [0:z-1]) rotate([0, 0, i*360/z])
            polygon(concat(
                [[rf*cos(a0), rf*sin(a0)]],
                fl,
                [for (j = [n:-1:0]) [fl[j][0], -fl[j][1]]],
                [[rf*cos(a0), -rf*sin(a0)]]));
    }
}

/* Gear on its own split-clamp boss. The slit stops at the gear face so it never
   cuts a tooth — the boss does the gripping, the gear body is along for the
   ride. Print TEETH FLAT ON THE BED for the same reason the hub prints bore-up:
   the profile is then an X-Y path, not a layer stack. */
module spur_gear(z) {
    rf = gear_module*z/2 - 1.25*gear_module;
    hb = min(2*rf - 8, 30);
    difference() {
        union() {
            gear_blank(gear_module, z, gear_w);
            cylinder(d = hb, h = gear_w + 10);
        }
        translate([0, 0, -1]) cylinder(d = shaft_dia + clr, $fn = fit_fn, h = gear_w + 20);
        translate([-0.9, -hb, gear_w]) cube([1.8, hb, 12]);
        translate([-hb/2 - 1, 0, gear_w + 5]) rotate([0,90,0]) cylinder(d = 4.4, $fn = hole_fn, h = hb + 2);
        translate([ 1.5, 0, gear_w + 5]) rotate([0,90,0]) cylinder(d = 7.6, h = hb, $fn = 6);
    }
}

/* ===========================================================================
   SENSOR MOUNT — the only precision part. Slotted for air-gap adjustment.
   =========================================================================== */
module sensor_mount() {
    body = sensor_dia + 2*wall + 4;
    h    = shaft_h + 6;
    difference() {
        union() {
            translate([-body/2, -body/2, 0]) cube([body, body, h]);
            translate([-body/2 - 10, -body/2, 0]) cube([body + 20, body, base_t]);
            for (s = [-1,1]) scale([1,s,1])
                translate([-body/2, body/2, 0])
                    rotate([90,0,0]) linear_extrude(wall)
                        polygon([[0,0],[body,0],[0,h*0.55]]);
        }
        // sensor bore, horizontal, on the shaft centreline
        translate([0, -body, shaft_h]) rotate([-90,0,0])
            cylinder(d = sensor_dia + clr, $fn = fit_fn, h = 2*body);
        if (sensor_flat > 0)
            translate([sensor_dia/2 - sensor_flat, -body, shaft_h - sensor_dia/2])
                cube([sensor_flat + 2, 2*body, sensor_dia]);
        // pinch slit + clamp screw so the sensor is gripped, not glued
        translate([-1, -body, shaft_h]) cube([2, body, h]);
        translate([-body, 0, shaft_h + sensor_dia/2 + 5]) rotate([0,90,0])
            cylinder(d = 4.4, $fn = hole_fn, h = 2*body);
        // SLOTTED feet — this is the air-gap adjustment
        for (x = [-body/2 - 5, body/2 + 5])
            hull() for (y = [-gap_slot/2, gap_slot/2])
                translate([x, y, -1]) cylinder(d = 4.4, $fn = hole_fn, h = base_t + 2);
    }
}

/* ===========================================================================
   BASE — long enough for motor, two bearings, wheel, sensor
   =========================================================================== */
base_l = 260;   // lengthened for the gear station: the cam shaft needs an axial
                // station of its own, clear of the 150 mm wheel. See README.
module base() {
    difference() {
        union() {
            cube([base_l, plate_w, base_t], center = true);
            for (x = [-1,1], y = [-1,1])                       // feet, lift the wheel clear
                translate([x*(base_l/2 - 14), y*(plate_w/2 - 14), -base_t/2 - 18])
                    cylinder(d = 22, h = 18 + 1);
        }
        // wheel slot — the lower half of the wheel passes through
        translate([base_l/2 - 74, 0, 0])
            cube([wheel_thk + 6, wheel_od + 10, base_t + 2], center = true);
        // M4 grid, 10 mm pitch, for positioning everything
        for (x = [-base_l/2 + 15 : 10 : base_l/2 - 15])
            for (y = [-plate_w/2 + 15 : 10 : plate_w/2 - 15])
                translate([x, y, -base_t/2 - 1]) cylinder(d = 4.4, $fn = hole_fn, h = base_t + 2);
    }
}

/* =========================================================================== */
if      (part == "bearing_block") bearing_block();
else if (part == "motor_mount")   motor_mount();
else if (part == "hub")           hub();
else if (part == "wheel_hub")     wheel_hub();
else if (part == "crank_gear")    spur_gear(crank_gear_teeth);
else if (part == "cam_gear")      spur_gear(cam_gear_teeth);
else if (part == "cam_target")    cam_target();
else if (part == "sensor_mount")  sensor_mount();
else if (part == "base")          base();
else {
    // rough assembly preview — check clearances, do not print
    color("silver") translate([0,0,base_t/2]) base();
    color("lightblue") translate([-70, 0, base_t]) rotate([0,0,0]) motor_mount();
    color("lightgreen") for (x = [-20, 20]) translate([x, 0, base_t]) bearing_block();
    color("orange") translate([26, 0, base_t]) rotate([0,-90,0]) hub();
    color("gray") translate([26, 0, base_t + shaft_h]) rotate([0,90,0])
        cylinder(d = wheel_od, h = wheel_thk, center = true);
    color("red") translate([26, wheel_od/2 + 10, base_t]) sensor_mount();
}
