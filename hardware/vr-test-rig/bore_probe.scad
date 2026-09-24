use <vr_rig.scad>
which = "motor_mount"; axis = "X"; pz = 60; probe_d = 8;
module part_under_test() { if (which == "motor_mount") motor_mount(); else bearing_block(); }
module probe() {
    if (axis == "X") rotate([0,90,0]) cylinder(d = probe_d, h = 300, center = true);
    else             rotate([-90,0,0]) cylinder(d = probe_d, h = 300, center = true);
}
intersection() { part_under_test(); translate([0,0,pz]) probe(); }
