use <vr_rig.scad>          // modules only - `include` would run the dispatcher
which = "bearing_block"; px = 22; py = -11; pd = 10.5;
base_t = 8; nut_h = 14;    // mirrored locally; `use` does not import variables

/* The if/else MUST be wrapped. As a direct child of intersection() OpenSCAD
   counts both branches, and the untaken empty one intersects everything to
   nothing - which reads exactly like a passing clearance test. */
module part_under_test() {
    if (which == "bearing_block") bearing_block(); else motor_mount();
}
intersection() {
    part_under_test();
    translate([px, py, base_t + 0.2]) cylinder(d = pd, h = nut_h - 0.4, $fn = 32);
}
