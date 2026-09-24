use <vr_rig.scad>
axis = "X"; probe_d = 8; pz = 60;
echo(str("probe axis=", axis, " at z=", pz));
module probe() {
    if (axis == "X") rotate([0,90,0]) cylinder(d = probe_d, h = 200, center = true);
    else             rotate([-90,0,0]) cylinder(d = probe_d, h = 200, center = true);
}
intersection() { bearing_block(); translate([0,0,pz]) probe(); }
