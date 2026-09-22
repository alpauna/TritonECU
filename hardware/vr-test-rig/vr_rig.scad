// TritonECU — 36-1 VR trigger wheel test rig
// Printed parts only. The toothed wheel itself MUST be steel (see README.md).
//
//   render one part at a time:  part = "bearing_block" | "motor_mount"
//                                      | "wheel_hub" | "cam_target" | "sensor_mount"
//                                      | "crank_gear" | "cam_gear"
//                                      | "base" | "hole_jig" | "assembly"

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
/* MEASURE ALL FOUR on the wheel itself. The values below come from measuring
   the product photo (Dorman 917-060), which fixes their RATIOS but not their
   absolute size — see README. The photo is square-on, so the ratios are sound:
       bore / OD        = 0.253
       keyway width     = 15 % of bore diameter
       keyway depth     = 19 % of bore radius
   "150 mm OD with a 24 mm bore" is ratio 0.160 and cannot both be true. */
/* WHAT THE PART ACTUALLY IS. Dorman 917-060, cast into the front face along
   with FRONT. Dorman's catalogue: steel, 35 teeth, OE cross XW1Z-12A227-AC,
   fitting 2001-2010 F-150 4.6 and 2002-2010 F-150 5.4 among others. The reseller
   listing this file used to quote got BOTH the OD (6-3/4") and the engine family
   ("Small Block Ford") wrong.

   ** DO NOT FIT THIS WHEEL TO THE TRUCK. ** It is a bench part. Its applications
   start at 2001 and the truck is a 1999, and a customer review of this exact
   part reports its teeth do not match the OEM wheel - timing codes and rough
   running. See README. The rig does not care; the vehicle would. */
/* ** THE VENDOR'S 171.45 (6-3/4") IS WRONG. ** Photographed flat on the carrier
   template with the WHOLE plate in frame, the wheel measures about 13.5 of the
   10 mm grid squares. 171.45 would be 17.1 of them. Two independent scales agree
   on the photo - the 157 x 173 plate outline and the 101.4 mm pin-field slot -
   and they bracket the wheel at 128..141 mm.

   MEASURED 2026-09-22: 126.2 mm on the Dorman wheel in hand. That is 8.8 mm
   under the 135 photo estimate and OUTSIDE the +/-7 it was quoted with, so the
   grid read was not merely imprecise. It also lands the rig on the wrong side of
   the slot_y bug: at 126.2 the wheel dips 3.1 mm below the base top, and the old
   test ("does it punch out the BOTTOM") would have cut no slot at all. */
wheel_od        = 126.2;  // MEASURED, caliper, across the tooth tips
/* ONE VARIABLE WAS DOING TWO JOBS, and they are not the same feature.
   The hub thickness sets the SPIGOT LENGTH - how far the hub reaches through the
   centre bore. The rim thickness sets the BASE SLOT WIDTH - what the tooth ring
   has to pass through. On a stamped reluctor those differ routinely, and the
   3.175 measured on 2026-09-22 is the CENTRE. Split, so a measurement of one can
   never again be silently spent on the other. */
wheel_thk_hub   =   3.175; // MEASURED 2026-09-22 = 0.125" exactly, AT THE CENTRE.
                           // The listing said .120"/3.05 - wrong again, same direction.
wheel_thk_rim   =   3.97;  // MEASURED 2026-09-22 at the outer edge = 5/32" exactly.
                           // ENVELOPE of the bent teeth, not sheet: the bend adds
                           // 3.97 - 3.175 = 0.794 = 1/32" over the 1/8" stock.

/* THE MODEL ASSUMES A FLAT WHEEL, and until now assumed it silently. Left at 0
   on a genuinely dished wheel, the base cuts BOTH the slot and the CKP sensor
   station in the wrong plane - one print, two misses. Positive = teeth to +X.

   BOUNDED RATHER THAN MEASURED. The bend adds only 0.794 mm of envelope, so even
   if every tooth is bent the same way the envelope centre cannot sit further than
   half of that off the disc plane. Which side is unknown and does not need to be
   known, because both consumers swallow it with room to spare - see the echoed
   margins below. If a LATER wheel has a real dish (teeth on a pressed-in offset
   ring rather than a bent lip) this stops being a rounding error, which is why
   the parameter stays. */
wheel_tooth_off =   0;     // bounded at +/-tooth_off_max, not measured
tooth_bend      = wheel_thk_rim - wheel_thk_hub;   // 0.794 = 1/32"
tooth_off_max   = tooth_bend / 2;                  // all-one-way worst case

/* The product photo's RATIOS survived what its absolute dimension did not - a
   ratio is scale-free, so it cannot be wrong about size. The old wheel_bore 43.4
   was 0.253 x the WRONG OD, which is how a good ratio produced a bad number.

   ALL THREE MEASURED 2026-09-22, and all three ratios were vindicated:

     wheel_bore   0.253 predicted 31.93   caliper 31.75    (1.25")   0.18 mm
     key_w        0.15  predicted  4.7625 caliper  4.7625  (3/16")   exact
     key_d        0.19  predicted  3.03   caliper  3.175   (1/8")    0.15 mm

   CORRECTION, and it is the reason this paragraph is long. key_w was first
   recorded here as 9.525 (3/8"), which made the ratio look wrong by two to one,
   and a lesson was drawn from that - "a ratio being right about one feature says
   nothing about the next". The 9.525 was a misread; 3/16 is the keyway. The
   ratio was never wrong, and the lesson drawn from it was worse than useless,
   because it argued for distrusting the one source that had been right three
   times out of three.

   What the episode actually shows is the opposite: a scale-free ratio held
   against an OD that moved 8.8 mm. The thing to distrust is a fresh reading that
   disagrees with a source already corroborated twice, which is exactly the check
   that would have caught 9.525 on the day. */
wheel_bore      = 31.75;   // MEASURED = 1.25" exactly
key_w           =  4.7625; // MEASURED = 3/16" exactly. CIRCUMFERENTIAL width.
                           // Was wrongly recorded as 9.525 (3/8") - see above.
key_d           =  3.175;  // MEASURED = 0.125", RADIAL depth past the bore wall

/* AUXILIARY HOLE - the second location feature, for sandwiching the wheel.
   MEASURED 2026-09-22 off the wheel, from the bore WALL (not the axis):

     near edge  10.319  = 13/32"
     far edge   16.670  = 21/32"
     diameter    6.35   =  1/4"

   The two edge readings were taken independently of the diameter, so they check
   it: 16.670 - 10.319 = 6.351 against a measured 6.35. That agreement is worth
   more than either reading alone, and aux_d_check below keeps it enforced. */
aux_edge_near   = 10.319;  // bore WALL to the nearest edge of the hole
aux_edge_far    = 16.670;  // bore WALL to the furthest edge
aux_hole_d      =  6.35;   // MEASURED = 0.25"
aux_hole_r      = wheel_bore/2 + aux_edge_near + aux_hole_d/2;   // 29.3695
aux_d_check     = aux_edge_far - aux_edge_near;                  // must match

/* ** NOT MEASURED ** - the one number the jig exists to settle. It moved three
   times before it settled, which is why the jig tolerates a range rather than
   trusting a value:

     ~95 deg    first estimate, by eye
     ~85 deg    revised - the wheel had been held upside down, and the photo
                is the FRONT
     92-98      pixels off that photo, bore-centre placement dominating the error
     95         SETTLED here. Re-checked against the part, the eye estimate was
                withdrawn in favour of the photo measurement.

   Direction is CLOCKWISE from the key viewed from the FRONT, confirmed against
   the photo: keyway at 12 o'clock, hole near 3 o'clock. Worth stating plainly
   because an upside-down wheel reverses it, and that already happened once. */
aux_hole_ang    = 95;      // deg CLOCKWISE from the key, viewed from the FRONT

echo(str("AUX HOLE: R ", aux_hole_r, " mm (bolt circle ", 2*aux_hole_r,
         " = ", 2*aux_hole_r/25.4, " in), dia ", aux_hole_d,
         ", angle ", aux_hole_ang, " deg CW from the key - UNCONFIRMED"));
echo(str("  edge cross-check: far - near = ", aux_d_check, " vs measured dia ",
         aux_hole_d, "  -> ", (abs(aux_d_check - aux_hole_d) < 0.1)
           ? "AGREES, both readings stand"
           : "** DISAGREE - one of the three numbers is wrong, do not print **"));

/* Tooth width at the rim as an angle, tooth_w_deg = 360*tooth_mm/(pi*wheel_od).
   50 % duty is the usual drawing and is NOT a measurement. It no longer sets
   key_to_gap - see below - it only bounds the uncertainty, +/- (10-w)/2. */
tooth_w_deg     =   5.0;  // MEASURE with calipers at the rim

/* Degrees from the MISSING TOOTH CENTRE to the keyway. Was 0, from a vendor
   product photo. THE PART SAYS OTHERWISE: the keyway lines up with THE GAP
   BETWEEN THE MISSING TOOTH AND THE NEXT TOOTH.

   That gap's centre is the midpoint of two tooth centres - one at the missing
   position, one a pitch away - so the tooth width cancels:

       gap spans  w/2 .. pitch-w/2   ->   centre = pitch/2 = 5.00 deg, any w

   EXACT and duty-free. The first reading of this part said 7.5 deg ("the rear
   edge of the tooth just forward"), which is the far boundary of this same gap
   and needed the duty to state. The centre of a gap is the better datum.

   SIGN. Defined by two EVENTS, not by geometry, because the first reading was
   taken with the wheel face-down and mirrored:

       key_to_gap = crank rotation from THE GAP PASSING THE SENSOR
                    until THE KEYWAY PASSES THE SENSOR.   Always positive.

   An order of events cannot be mirrored by picking the wheel up the other way.
   It is also how the part reads on the engine: the missing tooth goes by, and
   TDC is coming up.

   ** This is NOT CKP_GAP_TO_TDC_DEG. ** It is the wheel's half. The other half
   is where the sensor bolts to the block, and no measurement of the wheel can
   supply it. See README. */
key_to_gap      =   5.0;  // exact, half a pitch; +/-2.5 from the gap's own width

/* GEOMETRIC SENSE - now fixed, because the part carries its own orientation.
   FRONT is cast into the wheel's front face, and the engine turns CLOCKWISE seen
   from the front. A fixed sensor meets features in COUNTER-clockwise order (the
   next one to arrive is the one currently counter-clockwise of it), and the gap
   arrives before the keyway, so:

       on the face marked FRONT, sweeping CLOCKWISE:
       keyway first, then the missing tooth 5.00 deg later.

   The index flute on the flange OD is cut at key_to_gap so it points at the gap.
   Better still, read key_to_gap off a tooth log rather than trusting the flute:
   the flute must be KNOWN, not RIGHT. */
/* Both sensors share a 14.3 mm barrel; only their lengths differ (CKP 57 mm,
   CMP 38.1 mm). The mount is a through-bore clamp, so ONE part serves both —
   the sensor simply sits further in or out. */
sensor_dia      =  14.3;  // barrel diameter, both sensors
sensor_ckp_len  =  57.0;  // body length, crank
sensor_cmp_len  =  38.1;  // body length, cam

/* These sensors are FLANGE MOUNTED, not plain barrels: an O-ring'd barrel that
   drops into a bore, and a single bolt through an ear beside it. That means the
   insertion depth is fixed by the flange face — the sensor cannot be slid in or
   out to set the air gap. The slotted feet are the only adjustment. */
/* The FLANGE PLATE is perpendicular to the barrel, so a bolt normal to that
   plate runs PARALLEL to the barrel — the ear lies flat on a face the barrel
   passes through, and the bolt goes in alongside it. Measured from the barrel's
   edge: CKP 14.0 mm, CMP 12.7 mm, so +7.15 to reach the barrel axis. */
sensor_flange_ckp  = 14.0 + 14.3/2;   // 21.15 — barrel axis -> bolt centre
sensor_flange_cmp  = 12.7 + 14.3/2;   // 19.85
sensor_flange_bolt =  8.0;  // M8 through the flange eyelet
/* The ear itself, which the seating pad has to cover: 19 mm wide on both, with a
   rounded tip rather than a square end. Reach, from the barrel's edge: CKP
   25.4 mm, CMP 19.1 mm. The bolt is NOT centred on the tip radius — the ear runs
   past it on both — so the pad is sized from the reach, not from the bolt. */
sensor_flange_wide = 19.0;
sensor_flange_ext  = 25.4 + 14.3/2;   // 32.55 — barrel axis -> ear tip, the larger
/* Flange face -> sensing tip. These are the figures first recorded as "body
   length"; they are in fact the barrel, which is what positions the mount. */
sensor_barrel_ckp  = 57.0;
sensor_barrel_cmp  = 38.1;
sensor_flat     =   0;    // set >0 if the sensor body has a flat, for anti-rotation

/* --- cam channel (CMP) — 2:1 gear driven, see README ----------------------- */
cam_target_od   =  60.0;  // printed disc; only the insert needs to be steel
cam_bolt        =   8.0;  // M8 shank — this is the face the sensor sees, head inward
cam_head_af     =  13.0;  // M8 hex across flats, for the captive pocket
cam_head_thk    =   5.5;  // M8 head height
/* Counterweight, cancelling the M8 trigger bolt's ~480 g.mm.
   The pocket is a slip fit on 13 mm brass rod, deliberately DEEPER than needed:
   you balance by cutting the rod to length, not by trusting this arithmetic.
   Expect roughly 18 mm of rod — the printed boss is itself 4.5 g at r 19.5 and
   already does about a fifth of the job.
   Capacity is 25 g brass / 34 g lead, so either material reaches balance.
   The fill must be NON-FERROUS: the boss reaches r 29.7 against a 30 mm rim, so
   it passes the sensor every revolution and steel would be a second VR trigger. */
cw_r            =  19.5;  // pocket centre radius
cw_dia          =  13.4;  // slip fit on 13 mm rod stock — CUT THE ROD TO BALANCE
cw_depth        =  21.0;  // deeper than needed, so there is length to trim
cw_boss         =  19.4;  // spans r 9.8..29.2, inside the 30 mm rim
cw_h            =  23.0;
cam_gear_teeth  =  40;    // 2 : 1 against crank_gear_teeth
crank_gear_teeth=  20;
gear_module     =   2.0;  // centre distance = module*(20+40)/2 = 60 mm.
                          // NOT module 1: a 0.4 mm nozzle cannot render a
                          // 1.57 mm pitch-circle tooth accurately. See README.
gear_pa         =  20;    // pressure angle
gear_w          =  10;    // face width

/* --- stock parts, change only if you buy different ones -------------------- */
shaft_dia       =  12.0;  // 12 mm ground steel, h6
brg_od          =  28.0;  // 6001-2RS  (12 x 28 x 8)
brg_id          =  12.0;
brg_w           =   8.0;
nema            =  42.3;  // NEMA 17 body
nema_bolt       =  31.0;  // bolt circle (square pattern)
nema_boss       =  22.0;
nema_shaft      =   5.0;

/* --- fit and print tuning -------------------------------------------------- */
brg_press       =  +0.30; /* Bearing pocket, OVERSIZE on the model.
   ** THIS WAS -0.05 AND IT SPLIT THE BLOCKS. ** PETG, bearings pressed in,
   all but one cracked within the hour.

   -0.05 was never the real interference. AN FDM BORE PRINTS UNDERSIZE -
   extrusion overlaps on the inside of a curve, and a horizontal bore also
   sags at its crown - so 0.2-0.4 mm on diameter is normal. That turns a
   harmless 0.05 into 0.25-0.45, and the hoop stress with it:

       0.05 interference  ->   2.8 MPa       fine
       0.35               ->  19.3 MPa       marginal
       0.45               ->  24.9 MPa       ** past PETG's ~22 MPa INTERLAYER **

   And it is the interlayer number that matters, because at the 3 and 9
   o'clock positions of a HORIZONTAL bore the hoop stress runs in Z. The
   radial crack plane there contains the bore axis and the radius - which
   IS the layer plane. The block does not crack, it DELAMINATES, splitting
   out through the 4 mm side wall at bore mid-height, right where the
   gusset root sits as a stress riser.

   Thickening the wall does NOT fix it: a thicker hub is a stiffer hub and
   develops proportionally more contact pressure. 4 -> 8 mm takes the hoop
   stress from 19.3 to 18.2 MPa. Six percent, for 8 mm of extra width.

   THE FIT IS THE LEVER. +0.30 targets a small CLEARANCE after shrink; the
   bearing is then held by RETAINING COMPOUND (Loctite 638/609), which
   wants 0.05-0.25 mm of gap and puts zero hoop stress into the plastic.
   The shoulder still locates it axially.

   ** CALIBRATED 2026-09-20 on this printer. ** The gauge's +0.15 pocket took a
   6001 with no play; +0.30 and +0.45 were both loose. A pocket modelled at
   28.15 that finishes snug on a 28.00 bearing means the bore shrinks ~0.15 mm
   on diameter, so:

       +0.15 -> ~0.00 gap   felt best, and is the WRONG one: no room for the
                            compound, and a block that prints a tenth tighter
                            is back in interference — the first PETG set's
                            failure exactly
       +0.30 -> ~0.15 gap   <= this one. Middle of the 0.05-0.25 window
       +0.45 -> ~0.30 gap   past what Loctite 638 will fill

   At a 0.15 mm gap use 638 (fills to 0.25), not 609 (~0.10 and marginal).
   Re-run the gauge on a different printer or filament: printers differ by more
   than the failure margin does. */
clr             =   0.25; // general clearance
wall            =   4.0;
base_t          =   8.0;

/* The plate is ASYMMETRIC in Y, and has to be. A 57 mm crank barrel puts that
   sensor's outboard edge near +152, which a symmetric plate would answer with
   334 mm — past a 320 bed. The -Y side only needs 105 (the cam gear reaches
   -102), so shifting the plate rather than growing it fits comfortably. */
plate_y_lo      = -105.0;
plate_y_hi      =  157.0;
plate_w         = plate_y_hi - plate_y_lo;
plate_yc        = (plate_y_hi + plate_y_lo)/2;

/* --- spine rods: the base's stiffness comes from these, not from the plate ---
   Two full-length steel rods in ribs under the plate. Offset from the neutral
   axis they act as a beam's flanges: EI goes 20.5 -> 826 N.m^2, FORTY times.
   The offset is what does it, not the diameter — a 5 mm rod in a rib beats a
   10 mm rod buried in the plate (30x vs 11x), because a rod on the neutral axis
   can only contribute its own I while an offset one contributes A*d^2.
   They also bridge the wheel slot, which is the plate's weakest section, and
   span the print seam so the split needs no separate dowels. */
rod_d           =   8.0;
rod_y           =  58.0;  // clear of the slot (+-36.6) and of every foot bolt
rib_w           =  18.0;
rib_h           =  22.0;  // 2 mm shallower than the feet, so it never touches down

/* --- printing the base in two pieces ---------------------------------------
   At 280 x 240 it fits a 300 mm bed, but it is a ~20 h print with real warp
   risk. Splitting at x = -60 gives 80 + 200 mm pieces (the 1/4 + 3/4 split) and
   the seam lands in the ONLY empty span, between the motor and the first
   bearing — where the flexible coupling already absorbs misalignment. A seam
   under the gear mesh or between the crank bearings would sit exactly where
   alignment matters. */
base_split      = false;  // informational; render part "base_a" / "base_b"
x_seam          = -60;

/* --- derived --------------------------------------------------------------- */
/* Shaft height. It was wheel_od/2 + 12 = 87, which lifted the wheel clear of the
   base entirely and left the wheel slot doing nothing. Dropping the shaft so the
   wheel runs THROUGH the slot shortens the printed uprights, and upright tip
   stiffness goes as 1/h^3 -- 87 -> 60 is 2.4x on its own, for free. */
foot_h   =  34;                      /* leg height. Set by wheel clearance, not
                                        by looks: an 85.7 mm radius wheel dips
                                        25.7 mm below the base top, leaving only
                                        6 mm to the ground at 24. Raising the
                                        FEET costs nothing; raising shaft_h
                                        instead would cost ~30 % of the
                                        brackets' stiffness. */
shaft_h  =  60;                      // shaft centreline above the base top
blk_w    = brg_od + 2*wall;
/* Axial thickness of the upright. THIS is the rig's soft spot, not the shaft:
   at 16 mm the bracket was EI 24.6 N.m^2, below even the old 8 mm shaft and 8x
   below a 12 mm one. Stiffness goes as t^3, so 16 -> 24 is another 3.4x. */
blk_t    = max(brg_w + 2*wall, 24);
foot_y   =  34;                      // two bolt rows, not a single hinge line
blk_h    = shaft_h + brg_od/2 + wall;
gap_slot =  30;   /* Sensor air-gap travel, widened from 14. With a flange-
                     mounted sensor the barrel depth is fixed, so ALL of the gap
                     adjustment lives here — and it also has to absorb the
                     uncertainty in sensor_barrel_len. */

/* --- stations along the shafts (base is centred on the origin) -------------- */
/* Spaced against real part extents, not by eye. A bearing block's upright runs
   +-18 mm about its station and its foot +-26, so the gear boss (20 mm long)
   has to start beyond 48 or it lands inside the block. */
x_motor  = -95;
x_brg1   = -30;   // upright -48 .. -12
x_wheel  =   0;   // wheel STRADDLED between the bearings, not overhung
x_brg2   =  30;   // upright  12 ..  48
x_gear   =  70;   // boss 50..70 — clears the block at 48
/* Cam shaft on the NEGATIVE side, so it and the crank sensor do not both push
   the plate wider. */
cam_y    = -gear_module*(crank_gear_teeth + cam_gear_teeth)/2;  // -60 mm centres
x_cbrg1  =  30;   // same station as x_brg2 but 60 mm over in Y — they miss
x_camtgt =  88;   // 72..88
x_cbrg2  = 110;   // upright 92..128
/* Sensor mount stations. With a FLANGE-mounted sensor the tip lands at a fixed
   distance from the mounting face, so the station is set by the barrel length —
   not by the mount's own width, which is what the previous formula assumed.
       flange seats on the plate's outboard face
       tip = that face - sensor_barrel_len
       want tip = rim + air_gap
   The slotted feet then absorb however far sensor_barrel_len turns out to be
   from the guess above. */
air_gap  = 1.0;
/* Boss length, not plate thickness. At 10 mm a 57 mm barrel would hang 47 mm
   into free air off a single thin plate; on the engine that barrel sits in a
   deep bore. 30 mm supports over half of it and costs only plastic — and it
   pulls the mount 10 mm inboard, which the plate width is grateful for. */
sm_plate = 30;
y_ck     = wheel_od/2 + air_gap + sensor_barrel_ckp - sm_plate/2;
y_cmp    = cam_y + cam_target_od/2 + air_gap + sensor_barrel_cmp - sm_plate/2;

/* How far the wheel dips below the base top, and how wide the slot must be to
   let it. The old slot was cut wheel_od + 10 = 160 wide on a plate 100 wide --
   it severed the base in two. */
wheel_dip = wheel_od/2 - shaft_h;
/* FIXED — the old test asked the wrong question, twice.
   It was  (shaft_h + base_t < wheel_od/2), i.e. "does the wheel punch out the
   BOTTOM of the plate", and it sized the slot on the chord at that bottom face.
   But a slot is needed as soon as the wheel reaches below the base TOP, and it
   must be as long as the chord THERE -- the top face is the widest section of
   the intersection, the bottom the narrowest.
   At the current OD 135 the old form cut NO SLOT while the wheel buried 7.5 mm
   into an 8 mm plate: a hard collision, wheel cannot turn. Where it did fire
   (OD >= 138) it was short by 45 mm. Cut through; a blind pocket buys nothing. */
slot_y    = (wheel_dip > 0)
            ? 2*sqrt(pow(wheel_od/2, 2) - pow(shaft_h, 2)) + 10 : 0;
/* Cross-check against the photo, so a typo in the measured numbers is caught
   before anything is printed rather than after. */
echo(str("wheel bore/OD = ", wheel_bore/wheel_od,
         (abs(wheel_bore/wheel_od - 0.253) > 0.02)
           ? "  <-- DISAGREES with the photo's 0.253, check the measurements"
           : "  (photo: 0.253, consistent)"));
echo(str("shaft_h ", shaft_h, "  wheel dips ", wheel_dip,
         " mm, ", foot_h + base_t - wheel_dip, " mm to ground; slot ", slot_y, " mm"));
/* The base slot and the sensor bolt holes both track wheel_od directly, and
   wheel_od is still an estimate. Say so at render time, where it will be seen. */
/* GATE LIFT RETRACTED 2026-09-22, same day it was granted. It was granted on a
   3.175 thickness that turned out to be measured AT THE CENTRE, and the base
   slot does not pass the centre - it passes the teeth. The teeth are BENT, so
   the rim is thicker than the 0.125" sheet and wheel_thk_rim is a swept
   ENVELOPE, not a material thickness. Bent to one side, that envelope is also
   off-centre from the disc plane, which is what wheel_tooth_off carries.
   wheel_od is still measured and still good; the slot is what is not. */
rim_measured = true;   // set when wheel_thk_rim is a caliper reading AT THE TEETH
base_gate_ok = rim_measured;
echo(str("BASE GATE: wheel_od ", wheel_od, " MEASURED -> slot_y ", slot_y,
         " mm, y_ck ", y_ck, " mm, both good.",
         base_gate_ok ? "  Rim envelope set: slot width "
                      : "  ** HELD ** wheel_thk_rim is still the HUB value, slot width ",
         wheel_thk_rim + 6, " mm at x ", x_wheel + wheel_tooth_off, "."));
if (!base_gate_ok)
    echo(str("  DO NOT PRINT base/base_a/base_b. Measure ACROSS THE BENT TEETH",
             " (envelope, not sheet) and the offset of that envelope from the hub",
             " face. Both the slot AND the CKP sensor station are cut at x ",
             x_wheel + wheel_tooth_off, " - a dished wheel misses with both."));
/* The offset is bounded, not measured, so prove at render time that the bound is
   harmless rather than asserting it. Worst case is the whole bend to one side. */
echo(str("  OFFSET BOUND: bend ", tooth_bend, " mm -> envelope centre at worst ",
         tooth_off_max, " mm off the disc plane."));
echo(str("    slot clearance per side, nominal ", (wheel_thk_rim + 6 - wheel_thk_rim)/2,
         " mm, worst case ", (wheel_thk_rim + 6 - wheel_thk_rim)/2 - tooth_off_max,
         " mm  -> ", ((wheel_thk_rim + 6 - wheel_thk_rim)/2 - tooth_off_max > 1)
                       ? "FINE" : "** TIGHT, measure the offset **"));
echo(str("    CKP pole ", sensor_dia, " mm across a ", wheel_thk_rim,
         " mm tooth; worst-case axial slip ", tooth_off_max, " mm = ",
         100*tooth_off_max/wheel_thk_rim, " % of the tooth -> ",
         (tooth_off_max < wheel_thk_rim/4) ? "still fully overlapped"
                                           : "** check sensor alignment **"));
echo(str("HUB GATE LIFTED: wheel_bore ", wheel_bore, " and key ", key_w, " x ",
         key_d, " all MEASURED. hub/wheel_hub/cam_target clear to print."));
echo(str("  hub_od ", hub_od, ", spigot ", wheel_bore - clr, " dia x ", wh_spig_l,
         " long, key stands ", key_d, " proud at ", key_w - clr, " wide."));
/* The key is the part that carries timing. Say what it is filling.

   ON THE BACKLASH FIGURE, before it alarms someone: 0.9 deg sounds fatal on a
   wheel with 10 deg between teeth, and it is not, for two reasons.

   The key is NOT the torque path. The wheel is held by a split clamp and three
   M4 bolts - friction drives it, and the key is anti-slip backup. It only sees
   load if the clamp has already let go, which is a failure to fix rather than a
   tolerance to budget.

   And backlash is only error when the drive REVERSES. Spun one way by a stepper,
   the key rests on one flank and stays there, so the slop is a constant phase
   offset - it calibrates out in the same breath as the datum. It would matter on
   reversal, on a stop-start, or under torque ripple hard enough to unload the
   clamp. None of those is how this rig runs a sweep.

   Tighten clr for the key only if a measured sweep shows tooth-to-tooth jitter
   that tracks direction. Do not pre-emptively shrink it: a printed key that has
   to be forced into a steel keyway splits along the layer lines. */
echo(str("  KEY FILL: ", key_w - clr, " / ", key_w, " = ",
         100*(key_w - clr)/key_w, " % of the keyway width, ", clr,
         " mm total slop -> ", (clr/(wheel_bore/2) * 180/PI),
         " deg of backlash at the bore."));
/* Cross-check the key against the photo ratio the same way the bore is checked,
   so a misread like the 9.525 cannot sit here unchallenged a second time. */
echo(str("  key_w vs photo ratio 0.15 x bore = ", 0.15*wheel_bore, " -> ",
         (abs(key_w - 0.15*wheel_bore) < 0.3)
           ? "AGREES" : "** DISAGREES - re-measure before printing the hub **"));

/* ===========================================================================
   BEARING BLOCK  x2 — 608 bearings, shaft through
   =========================================================================== */
module bearing_block() {
    difference() {
        union() {
            translate([-blk_w/2, -blk_t/2, 0]) cube([blk_w, blk_t, blk_h]);
            translate([-blk_w/2 - 8, -foot_y/2, 0]) cube([blk_w + 16, foot_y, base_t]);
            for (s = [-1, 1]) scale([s,1,1])
                translate([blk_w/2, -blk_t/2, 0])
                    rotate([90,0,90]) linear_extrude(wall)
                        polygon([[0,0],[14,0],[0,blk_h*0.6]]);
        }
        // Bearing pocket, BLIND with a shoulder — a 24 mm deep bore would let an
        // 8 mm wide bearing wander. The shoulder lands on the outer race only.
        translate([0, -blk_t/2 - 1, shaft_h]) rotate([-90,0,0])
            cylinder(d = brg_od + brg_press, h = brg_w + 1, $fn = fit_fn);
        translate([0, -blk_t/2 - 2, shaft_h]) rotate([-90,0,0])
            cylinder(d = brg_od - 4, h = blk_t + 4, $fn = fit_fn);
        // FOUR M4 feet. Two bolts on the centreline is a hinge: the rotating
        // radial load has nothing but bolt preload resisting sideways rock.
        for (x = [-blk_w/2 - 4, blk_w/2 + 4], y = [-11, 11])
            translate([x, y, -1]) cylinder(d = 4.4, $fn = hole_fn, h = base_t + 2);
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
            cylinder(d = wheel_bore - clr, $fn = fit_fn, h = 16 + wheel_thk_hub); // spigot: CENTRE thickness
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
wh_spig_l = wheel_thk_hub + 3;   // spigot through the centre bore
module wheel_hub() {
    difference() {
        union() {
            cylinder(d = wh_flange, h = 10);                    // flange + gear face
            translate([0,0,10]) cylinder(d = wheel_bore - clr, $fn = fit_fn, h = wh_spig_l);
            // Integral key, formed in X-Y with the spigot. It must stand PROUD
            // of the spigot by the wheel's keyway depth — the spigot fills the
            // bore, and the key fills the slot cut outward from it. The cube
            // runs from the axis so it merges with the spigot; only the part
            // past wheel_bore/2 does any work. (This comment said "the 24 mm
            // bore" and "r = 11.875" through two OD corrections; the numbers
            // are derived now, so it no longer carries any.)
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
   VR SENSOR — a CHECK MODEL, not a rig part.

   Built from the SAME parameters the mount uses, deliberately. Print it, hold it
   against the real sensor, and any mismatch is a mismatch in the mount too —
   which is the whole point. It is cheaper to find that on a 20 g print than
   after the base is done.

   Everything here is measured except flange thickness and the connector, which
   are eyeballed from photographs and marked below.
   =========================================================================== */
sensor_flange_t = 6.0;   // MEASURE: flange plate thickness
/* The flange does not stop at the barrel — it carries on past it with the same
   radius as the tip end. Measured from the barrel's outer surface to the
   flange's outermost edge on that far side: */
sensor_back_ckp = 6.0;
sensor_back_cmp = 3.0;
/* Connector tails lie FLUSH with the flange, in its own plane — neither sensor
   has anything projecting behind it.
   The crank's is a SINGLE straight leg leaving at 90 deg to the ear: the "L" is
   the ear and that leg together, not a leg that itself bends.
   The cam has NO side tail. Its connector is a socket on the flange's back face,
   coaxial with the barrel and pointing 180 deg away from it.
   Leg and socket lengths are measured; the socket's cross-section is eyeballed. */
sensor_tail_w   = 13.0;  // GUESS
sensor_tail_l1  = 26.0;  // GUESS
sensor_socket_l = 14.0;  // cam socket, out the back of the flange
sensor_socket_w = 18.0;  // GUESS
sensor_socket_d = 12.0;  // GUESS

module vr_sensor(barrel_len, flange_reach, bolt_off, back_ext, ell) {
    tip_r = sensor_flange_wide/2;
    difference() {
        union() {
            /* Barrel. Flange face is z = 0, tip at z = barrel_len. */
            cylinder(d = sensor_dia, h = barrel_len - tip_r/2);
            translate([0, 0, barrel_len - tip_r/2 - 1])
                cylinder(d1 = sensor_dia, d2 = sensor_dia - 3, h = tip_r/2 + 1);

            translate([0, 0, -sensor_flange_t]) linear_extrude(sensor_flange_t) {
                /* Flange: rounded at BOTH ends, not just the bolt end. It runs
                   past the barrel by back_ext on the far side. */
                hull() {
                    translate([-(sensor_dia/2 + back_ext - tip_r), 0])
                        circle(r = tip_r, $fn = 48);
                    translate([flange_reach - tip_r, 0]) circle(r = tip_r, $fn = 48);
                }
                /* Connector tail, in the flange's own plane. */
                if (ell) {
                    /* Crank: one straight leg at 90 deg to the ear. Together with
                       the ear it makes the L — the leg itself does not bend. */
                    hull() {
                        circle(d = sensor_tail_w, $fn = 32);
                        translate([0, sensor_tail_l1]) circle(d = sensor_tail_w, $fn = 32);
                    }
                }
                /* Cam has no side tail at all — its connector is the socket
                   below, coaxial with the barrel. */
            }
            /* Cam: connector socket on the flange's back face, pointing 180 deg
               from the barrel. */
            if (!ell)
                translate([0, 0, -sensor_flange_t - sensor_socket_l])
                    linear_extrude(sensor_socket_l)
                        hull() for (sx = [-1,1], sy = [-1,1])
                            translate([sx*(sensor_socket_w/2 - 2.5),
                                       sy*(sensor_socket_d/2 - 2.5)])
                                circle(r = 2.5, $fn = 24);
        }
        translate([bolt_off, 0, -sensor_flange_t - 1])
            cylinder(d = sensor_flange_bolt, h = sensor_flange_t + 2, $fn = 32);
        translate([0, 0, 6]) rotate_extrude($fn = 64)
            translate([sensor_dia/2, 0]) circle(d = 2.4, $fn = 24);
    }
}

/* ===========================================================================
   SENSOR MOUNT — the only precision part. Slotted for air-gap adjustment.
   =========================================================================== */
module sensor_mount() {
    body    = sensor_dia + 2*wall + 4;
    pw      = max(body, sensor_flange_wide + 2*wall);   /* pad wide enough for the ear */
    plate_t = sm_plate;
    /* The ear is offset straight UP from the barrel, which keeps the mount
       narrow in X. The sensor turns freely in its bore, so the direction is
       ours to choose — pick the one that does not widen the base. */
    /* Tall enough to seat the whole ear, not merely to reach its bolt. */
    top     = shaft_h + sensor_flange_ext + wall + 3;
    footy   = gap_slot + 2*wall + 8;
    difference() {
        union() {
            translate([-pw/2, -plate_t/2, 0]) cube([pw, plate_t, top]);
            translate([-pw/2 - 10, -footy/2, 0]) cube([pw + 20, footy, base_t]);
            for (sgn = [-1, 1]) scale([1, sgn, 1])
                translate([-pw/2, plate_t/2, 0]) rotate([90,0,0])
                    linear_extrude(wall) polygon([[0,0],[pw, 0],[0, top*0.55]]);
        }
        /* Barrel bore, through, along the sensor axis */
        translate([0, -plate_t, shaft_h]) rotate([-90,0,0])
            cylinder(d = sensor_dia + clr, h = 3*plate_t, $fn = fit_fn);
        /* Flange bolt, PARALLEL to the barrel. Slotted so one printed part takes
           both sensors: CKP sits 21.15 mm above the barrel axis, CMP 19.85. */
        hull() for (dz = [sensor_flange_cmp - 2, sensor_flange_ckp + 2])
            translate([0, -plate_t, shaft_h + dz]) rotate([-90,0,0])
                cylinder(d = sensor_flange_bolt + 0.5, h = 3*plate_t, $fn = hole_fn);
        /* SLOTTED feet — with the barrel depth fixed by the flange, this is the
           only air-gap adjustment there is. */
        for (x = [-pw/2 - 5, pw/2 + 5])
            hull() for (y = [-gap_slot/2, gap_slot/2])
                translate([x, y, -1]) cylinder(d = 4.4, $fn = hole_fn, h = base_t + 2);
    }
}

/* ===========================================================================
   BASE — long enough for motor, two bearings, wheel, sensor
   =========================================================================== */
base_l = 300;   // parts span -128..+136; sized to a 300 mm rod bought whole, so
                // the spine needs no cutting. Print as base_a + base_b.
/* 280 x 240, which prints whole on a 300 mm bed (or as base_a + base_b). The
   plate itself is a floppy sheet — the stiffness comes from the two spine rods
   in ribs underneath. Plywood remains a fine substitute; this module doubles as
   its drilling template.
   The old 10 mm M4 grid is gone: at this plate size it was 660 holes and minutes
   of CGAL time for mounting points nothing used. Holes now sit only at stations
   that carry something, which is what you would mark out by hand anyway. */
module base() {
    sb = sensor_dia + 2*wall + 4;
    difference() {
        union() {
            translate([0, plate_yc, 0]) cube([base_l, plate_w, base_t], center = true);
            for (x = [-1,1], y = [-1,1])
                translate([x*(base_l/2 - 14), plate_yc + y*(plate_w/2 - 14), -base_t/2 - foot_h])
                    cylinder(d = 22, h = foot_h + 1);
            for (y = [-1,1])                                   // spine ribs
                translate([0, y*rod_y, -base_t/2 - rib_h/2])
                    cube([base_l, rib_w, rib_h], center = true);
        }
        for (y = [-1,1])                                       // rod bores
            translate([0, y*rod_y, -base_t/2 - rib_h/2]) rotate([0,90,0])
                cylinder(d = rod_d + 0.3, h = base_l + 2, center = true, $fn = fit_fn);
        // wheel slot, sized to the actual dip
        if (slot_y > 0)
            translate([x_wheel + wheel_tooth_off, 0, 0])
                cube([wheel_thk_rim + 6, slot_y, base_t + 2], center = true);
        // four bearing blocks, four bolts each
        for (st = [[x_brg1, 0], [x_brg2, 0], [x_cbrg1, cam_y], [x_cbrg2, cam_y]])
            for (dx = [-1,1], dy = [-1,1])
                translate([st[0] + dx*(blk_w/2 + 4), st[1] + dy*11, -base_t/2 - 1])
                    cylinder(d = 4.4, $fn = hole_fn, h = base_t + 2);
        // motor mount
        for (dx = [-1,1])
            translate([x_motor + dx*(nema/2 + wall + 4), 3, -base_t/2 - 1])
                cylinder(d = 4.4, $fn = hole_fn, h = base_t + 2);
        // two sensor mounts — the mount's own feet are slotted for air gap
        for (st = [[x_wheel + wheel_tooth_off, y_ck], [x_camtgt, y_cmp]])
            for (dx = [-1,1])
                translate([st[0] + dx*(sb/2 + 5), st[1], -base_t/2 - 1])
                    cylinder(d = 4.4, $fn = hole_fn, h = base_t + 2);
    }
}

/* Split for printing: the spine rods run through both pieces and splice them. */
module base_half(lo, hi) {
    intersection() {
        base();
        translate([(lo + hi)/2, 0, 0])
            cube([hi - lo, plate_w + 20, 200], center = true);
    }
}

/* =========================================================================== */
/* ===========================================================================
   FIT GAUGE — measure your printer's bore shrink instead of guessing it
   ===========================================================================
   Three pockets at different oversizes, in the SAME ORIENTATION as the real
   block (bore horizontal), because horizontal and vertical bores do not
   shrink alike. Print it, try a 6001 in each, and set brg_press to the one
   that slides in with a whisker of play.                                   */
gauge_steps = [0.15, 0.30, 0.45];

/* LABEL BAND. Fixed 2026-09-20: the labels used to sit at baseline z = 3.5 with
   the bore centred at z = 18, so the bore mouth opened at z = 3.93 directly
   above them and ate everything but the bottom 0.4 mm of each digit. Printed,
   only the very bottom of the number was visible on all three. The band is now
   plain plate BELOW the bores, the whole reason the part got taller.

   The numbers are the only thing that tells the pockets apart — 0.15 mm on
   diameter is not something you can eyeball — so the band also carries a V
   notch in the top face over the SMALLEST pocket. If the text fails again, the
   notched end is still the +0.15 end. */
gauge_band  = 8.0;   // plain plate under the bores, for the labels
gauge_text  = 4.5;   // cap height lands ~3.2, centred in the band
gauge_cut   = 0.8;   // engraving depth; 0.6 was shallow for a dark filament
gauge_notch = true;
notch_w     = 6.0;
notch_d     = 1.5;   // over the bore there is only wall (4) to give away


/* ===========================================================================
   HOLE JIG — one flat part that checks every wheel number at once
   ===========================================================================
   A 1/8" plate that plugs the bore and keyway, dog-legs up over the wheel face,
   and drops a pin into the auxiliary hole. Seat it and six measurements are
   confirmed together: bore diameter, keyway width, keyway depth, centre
   thickness (the plug finishes flush), hole radius, and hole angle.

   THE PIN IS ROUND, because the hole is round. An earlier version made it
   obround - tight radially, narrow circumferentially - so that one part would
   seat across the whole +/-3 deg the angle was uncertain by. That was overruled,
   and the reasoning is kept here only so the consequence is not a surprise:

     round 6.10 in a 6.35 hole  ->  0.12 mm radial slop  ->  +/-0.24 deg

   A ROUND PIN MAKES THIS A SET, NOT A PART. At +/-0.24 deg against an angle
   known to +/-3, one jig at nominal has about one chance in twelve of seating
   even on a flawless wheel. Print the ladder - 92 to 98 at 1 deg - and the one
   that seats reports the angle to +/-0.24, which is far finer than any single
   tolerant part could have managed. The looseness was doing the tolerating; the
   ladder does it instead, and it does it better.

     openscad -D 'part="hole_jig"' -D aux_hole_ang=93 -o jig_93.stl vr_rig.scad

   Each part carries its own angle debossed on the arm, because seven jigs that
   differ by one degree are otherwise indistinguishable in a pile.

   FAILURE IS DIAGNOSTIC, which matters for a gauge that checks six things. Every
   other number here is measured and cross-checked - the bore is 1.25" on the
   nose, the edge readings agree with the hole diameter to 0.001 - so the angle
   is the only genuinely unknown input. If it will not seat, the angle is the
   first suspect, not the sixth.

   PRINTING, AND WHAT PETG DOES TO IT. Modelled in USE orientation - wheel face
   at z=0, plug and pin hanging below, arm above - because that is the
   orientation in which "clockwise from the key" is unambiguous. The dispatcher
   flips it for export, so the STL arrives arm-down on the bed with plug and pin
   as vertical columns: no supports, and no bridging under the dog leg.
   Consequences worth knowing before blaming the wheel:

     - The fit surfaces are vertical walls, NOT the first layer, so elephant foot
       lands on the arm outline where nothing fits. This is the reason for that
       orientation beyond convenience.
     - PETG runs wide. The same printer measured 0.15 mm of shrink on a
       horizontal bore in fit_gauge, but an external column errs the other way,
       so the pin and plug carry clr (0.25) off nominal rather than a shrink
       allowance. If the plug will not enter, skim it - do not open the wheel.
     - Pin and plug get a 0.8 mm lead-in taper. PETG's first perimeter on a small
       column bulges slightly, and a chamfer beats discovering that in the bore.
   =========================================================================== */
jig_t       = wheel_thk_hub;           // 1/8" - and it gauges the wheel's own
jig_pin_d   = aux_hole_d - clr;        // 6.10 round, to a round hole
jig_arm_w   = 13;
jig_hub_d   = wheel_bore + 12;         // arm rests on the face around the bore
jig_lead    = 0.8;                     // PETG lead-in taper

module hole_jig() {
    ang = -aux_hole_ang;               // CLOCKWISE from the key, front view
    difference() {
      union() {
        // plug: fills bore + keyway, finishing flush with the wheel face
        translate([0, 0, -jig_t]) {
            cylinder(d = wheel_bore - clr, h = jig_t, $fn = fit_fn);
            translate([0, -(key_w - clr)/2, 0])
                cube([wheel_bore/2 + key_d - 0.1, key_w - clr, jig_t]);
        }
        // dog leg: rests on the wheel face, carries the arm out to the hole
        hull() {
            cylinder(d = jig_hub_d, h = jig_t, $fn = 90);
            rotate([0,0,ang]) translate([aux_hole_r, 0, 0])
                cylinder(d = jig_arm_w, h = jig_t, $fn = 60);
        }
        // pin: down into the hole, exactly as deep as the wheel is thick,
        // with a lead-in taper so a fat first perimeter cannot jam the entry
        rotate([0,0,ang]) translate([aux_hole_r, 0, -jig_t]) {
            cylinder(d1 = jig_pin_d - 0.9, d2 = jig_pin_d, h = jig_lead, $fn = 48);
            translate([0,0,jig_lead])
                cylinder(d = jig_pin_d, h = jig_t - jig_lead, $fn = 48);
        }
      }
      /* Angle CUT INTO the arm's upper face in use orientation - a deboss, not an
         emboss. Raised text here would be 0.4 mm proud of what becomes the BED
         face once the dispatcher flips the part, so the jig would stand on its
         own label and print tilted. Caught by the z span, not by eye.

         No mirroring. That face is read from +Z whether the jig is sitting on
         the wheel or the printed part has just been lifted off the bed, so text
         modelled to read from +Z reads correctly both ways. */
      rotate([0,0,ang]) translate([aux_hole_r - 17, 0, jig_t - 0.6])
          linear_extrude(1.2) rotate([0,0,-ang])
              text(str(aux_hole_ang), size = 5, halign = "center",
                   valign = "center", $fn = 24);
    }
}

jig_tol = asin((aux_hole_d - jig_pin_d)/2 / aux_hole_r);
echo(str("HOLE JIG: ", jig_t, " mm plate, plug ", wheel_bore - clr,
         ", ROUND pin ", jig_pin_d, " at R ", aux_hole_r, ", ",
         aux_hole_ang, " deg CW."));
echo(str("  seats only within +/-", jig_tol, " deg, i.e. ",
         aux_hole_ang - jig_tol, " to ", aux_hole_ang + jig_tol,
         ". PRINT THE LADDER 92..98 - one jig will not find the angle."));


module fit_gauge() {
    pitch = brg_od + 6; n = len(gauge_steps);
    w = n*pitch; h = brg_od + 2*wall + gauge_band; t = brg_w + 3;
    zc = gauge_band + wall + brg_od/2;      // bore centre, lifted by the band
    difference() {
        translate([-w/2, -t/2, 0]) cube([w, t, h]);
        for (i = [0:n-1]) {
            x = -w/2 + pitch*(i + 0.5);
            translate([x, -t/2 - 1, zc]) rotate([-90,0,0])
                cylinder(d = brg_od + gauge_steps[i], h = brg_w + 1, $fn = fit_fn);
            translate([x, -t/2 - 2, zc]) rotate([-90,0,0])
                cylinder(d = brg_od - 4, h = t + 4, $fn = fit_fn);
            // label, in the band, clear of the bore by the whole wall
            translate([x, -t/2 + gauge_cut, gauge_band/2]) rotate([90,0,0])
                linear_extrude(gauge_cut + 0.5)
                    text(str(gauge_steps[i]), size = gauge_text,
                         halign = "center", valign = "center", $fn = 16);
        }
        // V notch in the top face, over the smallest pocket
        if (gauge_notch)
            translate([-w/2 + pitch*0.5, 0, h]) rotate([90, 0, 0])
                linear_extrude(t + 2, center = true)
                    polygon([[-notch_w/2, 0], [notch_w/2, 0], [0, -notch_d]]);
    }
}

echo(str("fit gauge  ", len(gauge_steps), " pockets ", gauge_steps,
         "  on a ", len(gauge_steps)*(brg_od+6), " x ", brg_w+3, " x ",
         brg_od + 2*wall + gauge_band, " coupon"));
echo(str("  bore centre z       ", gauge_band + wall + brg_od/2));
echo(str("  bore mouth bottom   ",
         gauge_band + wall + brg_od/2 - (brg_od + gauge_steps[0])/2,
         "  <- label band is clear below this"));
echo(str("  label band          0 .. ", gauge_band, ", text ", gauge_text,
         " centred at ", gauge_band/2, ", cut ", gauge_cut, " deep"));
echo(str("  material over the notch root  ",
         (brg_od + 2*wall + gauge_band) - notch_d
           - (gauge_band + wall + brg_od/2 + (brg_od + gauge_steps[0])/2), " mm"));
echo("  SMALLEST pocket is the NOTCHED end, and reads left to right with the");
echo("  numbers upright.");

if      (part == "fit_gauge")     fit_gauge();
else if (part == "bearing_block") bearing_block();
else if (part == "base_a")        base_half(-base_l/2 - 1, x_seam);
else if (part == "base_b")        base_half(x_seam, base_l/2 + 1);
else if (part == "motor_mount")   motor_mount();
else if (part == "hub")           hub();
else if (part == "wheel_hub")     wheel_hub();
else if (part == "crank_gear")    spur_gear(crank_gear_teeth);
else if (part == "cam_gear")      spur_gear(cam_gear_teeth);
else if (part == "cam_target")    cam_target();
else if (part == "sensor_mount")  sensor_mount();
else if (part == "hole_jig")      rotate([180,0,0]) hole_jig();  // export print-ready
else if (part == "sensor_ckp")    vr_sensor(sensor_barrel_ckp, 25.4 + sensor_dia/2,
                                            sensor_flange_ckp, sensor_back_ckp, true);
else if (part == "sensor_cmp")    vr_sensor(sensor_barrel_cmp, 19.1 + sensor_dia/2,
                                            sensor_flange_cmp, sensor_back_cmp, false);
else if (part == "base")          base();
else {
    // rough assembly preview — check clearances, do not print
    color("silver")      translate([0,0,base_t/2]) base();
    color("lightblue")   translate([x_motor, 0, base_t]) motor_mount();
    color("lightgreen")  for (x = [x_brg1, x_brg2]) translate([x, 0, base_t]) bearing_block();
    color("lightgreen")  for (x = [x_cbrg1, x_cbrg2]) translate([x, cam_y, base_t]) bearing_block();
    color("orange")      translate([x_wheel - 9, 0, base_t + shaft_h]) rotate([0,90,0]) wheel_hub();
    color("gray")        translate([x_wheel, 0, base_t + shaft_h]) rotate([0,90,0])
                             cylinder(d = wheel_od, h = wheel_thk_rim, center = true, $fn = 120);
    color("gold")        translate([x_gear, 0, base_t + shaft_h]) rotate([0,-90,0]) spur_gear(crank_gear_teeth);
    color("gold")        translate([x_gear, cam_y, base_t + shaft_h]) rotate([0,-90,0]) spur_gear(cam_gear_teeth);
    color("tan")         translate([x_camtgt, cam_y, base_t + shaft_h]) rotate([0,-90,0]) cam_target();
    color("red")         translate([x_wheel,  y_ck,  base_t]) sensor_mount();
    color("red")         translate([x_camtgt, y_cmp, base_t]) rotate([0,0,180]) sensor_mount();
    echo(str("plate ", base_l, " x ", plate_w, " mm, Y ", plate_y_lo, "..", plate_y_hi,
         " — needs a bed of at least ", max(base_l, plate_w), " mm"));
}
