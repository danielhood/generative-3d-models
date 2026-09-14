// Celtic triskele coaster: 100 mm diameter, 3 mm thick, to the same brief
// as the Helm of Awe, Yggdrasil and Tree of Life coasters (pattern out to
// r = 43, solid 7 mm rim from 43 to 50) so the four read as a set.
//
// The sense matches the Tree of Life and is inverted relative to the first
// two. Insert-air-tribe.stl is a solid plate with the design cut clean
// through it, so the ground is the material and the drawing is the void.
// Subtracting the artwork from a disc makes the coaster one connected piece
// by construction -- there is no scaffolding problem to solve here.
//
// WHY THERE IS NOTHING ELSE IN THIS FILE.
//
// The Tree of Life coaster needed two repair steps and a replacement
// border, because that source's line weight was roughly 2x too fine for FDM
// at 100 mm: its chain ring measured 0.36 mm material ribbons and its rim
// detached from the middle of the coaster under 0.20 mm of erosion. This
// source is a different animal. Measured off the source mesh at this exact
// scale, before anything was drawn (spec section 3):
//
//     arms  (r 6-28)  material p1 1.04  p5 2.32  p50 2.89 mm
//     whole part      holds ONE piece, zero shed, through 0.30 mm erosion
//
// So it is reproduced faithfully: scale, subtract, extrude. No erosion of
// the cuts, no morphological opening, and the source's own border kept
// rather than redrawn.
//
// An opening was tried anyway, at open_r = 0.20 and 0.30, on the assumption
// that it is free insurance. It is not. It left the erosion ladder
// unchanged and TRIPLED the number of sub-0.4 mm material ridge points, 37
// -> 117, because offset(+r) offset(-r) at finite $fn re-faceted 6,443
// polygon points and shed hairline slivers of its own. Spec section 6, E1.
// This is the Tree of Life's D5 finding generalised: an opening is a repair
// for artwork that needs one and a source of damage for artwork that does
// not. Measure first; do not apply it by reflex.

include <triskele_pattern.scad>

coaster_diameter = 100;
thickness        = 3;
edge_margin      = 7;

outer_r           = coaster_diameter / 2;        // 50 mm
target_pattern_r  = outer_r - edge_margin;       // 43 mm

// native_max_r comes from triskele_pattern.scad: the outer radius of the
// design's four broken-ring arcs. Scaling by this lands those arcs' outer
// edge exactly on the inner edge of the plain 7 mm rim, which is why the
// brief's 43/7 split needed no adjustment for this source.
scale_factor = target_pattern_r / native_max_r;

module coaster_section() {
    difference() {
        circle(r = outer_r, $fn = 360);
        scale([scale_factor, scale_factor])
            triskele_cuts_native();
    }
}

module coaster() {
    linear_extrude(height = thickness)
        coaster_section();
}

coaster();
