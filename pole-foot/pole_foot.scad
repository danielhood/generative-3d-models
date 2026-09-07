// Pole foot / end cap - 29 x 27 mm elliptical pole, PETG
//
// Blind socket with vertical interior ridges for a tight fit.
//
// Everything is built from one base ellipse (the nominal pole section) and
// 2D `offset()`s of it. offset() is a true parallel curve, so a wall, a bore
// clearance and a chamfer are all uniform all the way round - which scaling
// the ellipse would NOT give, since scaling moves the major axis further than
// the minor one.
//
// Fit: the bore is offset outward by `clearance`, then the ridges stand
// `ridge_h` proud of it. With clearance == ridge_h the crests land exactly on
// the nominal pole ellipse, so the pole beds on `ridge_count` narrow
// compliant lines rather than on one loose wall. PETG has enough give in a
// 0.4 mm crest to take up print tolerance without loading the wall.
//
// NOTE: an elliptical socket only accepts the pole in two rotations, 180 deg
// apart. That is inherent to the section, not a choice made here.

/* [Pole] */
pole_x        = 29;    // pole outside dimension across X (major)
pole_y        = 27;    // pole outside dimension across Y (minor)
socket_depth  = 40;    // how far the pole inserts

/* [Foot] */
wall          = 1.5;   // side wall thickness, uniform all round
floor_t       = 4;     // material below the end of the pole
base_chamfer  = 0.8;   // bottom outer edge, 45 deg
top_chamfer   = 0.6;   // top outer edge, 45 deg
lip_chamfer   = 0.6;   // bore mouth, 45 deg
seat_chamfer  = 0.6;   // socket floor corner, keeps the pole seating flat

/* [Fit] */
clearance     = 0.4;   // outward offset cut into the bore, before ridges
ridge_h       = 0.4;   // how far each ridge stands proud of the bore
ridge_d       = 1.6;   // ridge cylinder diameter (rounded crest)
ridge_count   = 8;
lead_in       = 3;     // ridge crests taper away over this much of the mouth

/* [Quality] */
$fa = 1;
$fs = 0.2;
ell_fn = 120;          // base ellipse segments; keep a multiple of 4 so the
                       // axis extremes land on real vertices
eps    = 0.01;         // AXIAL overshoot only - never applied to an offset
hull_e = 0.001;        // slab thickness for hull tapers

// ---- derived ----------------------------------------------------------
a_nom     = pole_x/2;              // 14.5
b_nom     = pole_y/2;              // 13.5
bore_off  = clearance;             // 0.4  -> bore is 29.8 x 27.8
outer_off = clearance + wall;      // 1.9  -> outside is 32.8 x 30.8
total_h   = floor_t + socket_depth;// 44

// Ridge axes sit on the offset curve that puts exactly ridge_h of the
// cylinder proud of the bore wall. crest = bore_off - ridge_h from nominal,
// so with clearance == ridge_h the crests sit on the nominal ellipse itself.
ridge_off = bore_off - ridge_h + ridge_d/2;   // 0.8

// ---- 2D base ----------------------------------------------------------
module ell(off) {
    if (off == 0) scale([a_nom, b_nom]) circle(r = 1, $fn = ell_fn);
    else offset(r = off) scale([a_nom, b_nom]) circle(r = 1, $fn = ell_fn);
}

// Straight section between two heights.
module prism(off, z0, z1) {
    translate([0, 0, z0]) linear_extrude(z1 - z0) ell(off);
}

// Ruled taper between two offsets at two heights - this is how a chamfer is
// made on a non-axisymmetric part. Both sections are convex, so the hull is
// exactly the ruled surface between them.
module taper(off0, z0, off1, z1) {
    hull() {
        translate([0, 0, z0])          linear_extrude(hull_e) ell(off0);
        translate([0, 0, z1 - hull_e]) linear_extrude(hull_e) ell(off1);
    }
}

// ---- solids -----------------------------------------------------------
module outer_solid() {
    union() {
        taper(outer_off - base_chamfer, 0, outer_off, base_chamfer);
        prism(outer_off, base_chamfer, total_h - top_chamfer);
        taper(outer_off, total_h - top_chamfer, outer_off - top_chamfer, total_h);
    }
}

module bore_cutter() {
    union() {
        taper(bore_off - seat_chamfer, floor_t, bore_off, floor_t + seat_chamfer);
        prism(bore_off, floor_t + seat_chamfer, total_h - lip_chamfer);
        taper(bore_off, total_h - lip_chamfer, bore_off + lip_chamfer, total_h);
        prism(bore_off + lip_chamfer, total_h, total_h + eps);   // axial overshoot
    }
}

// ---- ridge placement --------------------------------------------------
// Outward normal of the ellipse at parameter t is grad(x^2/a^2 + y^2/b^2),
// i.e. (cos t / a, sin t / b) - NOT the radial direction.
function ell_pt(t)     = [a_nom * cos(t), b_nom * sin(t)];
function ell_nrm(t)    = let (v = [cos(t)/a_nom, sin(t)/b_nom]) v / norm(v);
function ell_off(t, d) = ell_pt(t) + d * ell_nrm(t);

// Ridges taper to nothing over the top `lead_in`: as the cylinder shrinks,
// its crest walks back into the wall on its own. No cutter, so nothing can
// end up tangent or epsilon-offset from a surface it is meant to cut.
module ridges() {
    for (i = [0 : ridge_count - 1]) {
        t = i * 360 / ridge_count;
        c = ell_off(t, ridge_off);
        translate([c[0], c[1], floor_t]) {
            cylinder(h = socket_depth - lead_in, d = ridge_d);
            translate([0, 0, socket_depth - lead_in])
                cylinder(h = lead_in, d1 = ridge_d, d2 = 0.02);
        }
    }
}

module foot() {
    union() {
        difference() {
            outer_solid();
            bore_cutter();
        }
        // clipped to the silhouette so ridge stock cannot break out
        // through the top chamfer
        intersection() {
            ridges();
            outer_solid();
        }
    }
}

// ---- parts ------------------------------------------------------------
// A 10 mm tall slice of the socket - same bore, same ridges, no floor.
// Print this first and check the fit before committing hours to the foot.
fit_test_h = 10;

module fit_test_ring() {
    taper_h = 2;                     // ridge ends taper away over this height
    z0      = 0.5;                   // keep the ridges clear of both end faces
    body_h  = fit_test_h - 2*z0;
    union() {
        difference() {               // bore cut FIRST, then the ridges go in
            prism(outer_off, 0, fit_test_h);
            prism(bore_off, -eps, fit_test_h + eps);
        }
        for (i = [0 : ridge_count - 1]) {
            t = i * 360 / ridge_count;
            c = ell_off(t, ridge_off);
            translate([c[0], c[1], z0]) {
                cylinder(h = taper_h, d1 = 0.02, d2 = ridge_d);
                translate([0, 0, taper_h])
                    cylinder(h = body_h - 2*taper_h, d = ridge_d);
                translate([0, 0, body_h - taper_h])
                    cylinder(h = taper_h, d1 = ridge_d, d2 = 0.02);
            }
        }
    }
}

part = "foot";   // "foot" or "fit_test"

if (part == "foot") foot();
else if (part == "fit_test") fit_test_ring();
