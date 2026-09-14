// TritonECU — 36-1 VR trigger wheel test rig
// Printed parts only. The toothed wheel itself MUST be steel (see README.md).
//
//   render one part at a time:  part = "bearing_block" | "motor_mount"
//                                      | "hub" | "cam_target" | "sensor_mount"
//                                      | "base" | "assembly"

part = "assembly";
$fn = 64;

/* ---------------------------------------------------------------------------
   MEASURE THESE THREE before printing — everything else follows from them
   --------------------------------------------------------------------------- */
wheel_od        = 150.0;  // MEASURE: trigger wheel outside diameter
wheel_thk       =   5.0;  // MEASURE: wheel thickness
wheel_bore      =  25.4;  // MEASURE: wheel centre bore
sensor_dia      =  19.0;  // MEASURE: VR sensor barrel diameter (Ford CKP)
sensor_flat     =   0;    // set >0 if the sensor body has a flat, for anti-rotation

/* --- cam channel (CMP) — 2:1 gear driven, see README ----------------------- */
cam_target_od   =  60.0;  // printed disc; only the insert needs to be steel
cam_insert_dia  =   6.0;  // steel dowel or bolt head forming the single lobe
cam_gear_teeth  =  40;    // 2 : 1 against crank_gear_teeth
crank_gear_teeth=  20;
gear_module     =   1.0;  // centre distance = module*(20+40)/2 = 30 mm

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
            rotate([-90,0,0]) cylinder(d = brg_od + brg_press, h = brg_w + 2*wall + 2);
        // shaft relief either side so the bearing seats on its outer race only
        translate([0, -brg_w/2 - wall - 2, shaft_h])
            rotate([-90,0,0]) cylinder(d = brg_od - 4, h = brg_w + 2*wall + 4);
        // M4 feet
        for (x = [-blk_w/2 - 4, blk_w/2 + 4])
            translate([x, 0, -1]) cylinder(d = 4.4, h = base_t + 2);
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
                    translate([0,0,-1]) cylinder(d = 3.4, h = wall + 4);
        }
        for (x = [-nema/2 - wall - 4, nema/2 + wall + 4])
            translate([x, 3, -1]) cylinder(d = 4.4, h = base_t + 2);
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
            cylinder(d = wheel_bore - clr, h = 16 + wheel_thk);   // spigot locates the wheel
        }
        translate([0,0,-1]) cylinder(d = shaft_dia + clr, h = 40); // shaft bore
        translate([-0.9, -hub_od, 8]) cube([1.8, hub_od, 40]);     // clamp slit
        // clamp screw, M4 across the slit
        translate([-hub_od/2 - 1, 0, 24]) rotate([0,90,0]) cylinder(d = 4.4, h = hub_od + 2);
        translate([ 1.5, 0, 24]) rotate([0,90,0]) cylinder(d = 7.6, h = hub_od, $fn = 6); // nut trap
        // wheel bolts — 3 x M4 on a circle, adjust to the wheel you buy
        for (a = [0:120:359]) rotate([0,0,a])
            translate([hub_od/2 - 7, 0, -1]) cylinder(d = 4.4, h = 20);
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
        }
        translate([0,0,-1]) cylinder(d = shaft_dia + clr, h = 40);
        // steel insert, press fit, at the rim — this is the only magnetic feature
        translate([cam_target_od/2 - cam_insert_dia, 0, -1])
            cylinder(d = cam_insert_dia - 0.05, h = 7);
        // split clamp, same pattern as hub()
        translate([-0.9, -hub_od, 6]) cube([1.8, hub_od, 40]);
        translate([-hub_od/2 - 1, 0, 11]) rotate([0,90,0]) cylinder(d = 4.4, h = hub_od + 2);
        translate([ 1.5, 0, 11]) rotate([0,90,0]) cylinder(d = 7.6, h = hub_od, $fn = 6);
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
            cylinder(d = sensor_dia + clr, h = 2*body);
        if (sensor_flat > 0)
            translate([sensor_dia/2 - sensor_flat, -body, shaft_h - sensor_dia/2])
                cube([sensor_flat + 2, 2*body, sensor_dia]);
        // pinch slit + clamp screw so the sensor is gripped, not glued
        translate([-1, -body, shaft_h]) cube([2, body, h]);
        translate([-body, 0, shaft_h + sensor_dia/2 + 5]) rotate([0,90,0])
            cylinder(d = 4.4, h = 2*body);
        // SLOTTED feet — this is the air-gap adjustment
        for (x = [-body/2 - 5, body/2 + 5])
            hull() for (y = [-gap_slot/2, gap_slot/2])
                translate([x, y, -1]) cylinder(d = 4.4, h = base_t + 2);
    }
}

/* ===========================================================================
   BASE — long enough for motor, two bearings, wheel, sensor
   =========================================================================== */
base_l = 200;
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
                translate([x, y, -base_t/2 - 1]) cylinder(d = 4.4, h = base_t + 2);
    }
}

/* =========================================================================== */
if      (part == "bearing_block") bearing_block();
else if (part == "motor_mount")   motor_mount();
else if (part == "hub")           hub();
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
