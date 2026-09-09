// Helm of Awe coaster: 100 mm diameter, 3 mm thick. The Helm of Awe pattern
// (hub + tridents + guard ring) is the solid material; the background
// between them is open, with a solid 7 mm rim at the edge.
//
// CORRECTION (2026-09-08): an earlier version of this comment claimed that
// `linear_extrude()` of this `difference()` does not behave like a literal
// "disc minus pattern" subtraction. That was wrong and has been retracted.
// The subtraction is entirely literal -- the catch is that the polygons in
// helm_of_awe_pattern.scad are the emblem's NEGATIVE SPACE, not the emblem.
// insert-helm-of-awe.stl is a plate with the design cut clean through it,
// so the trace picked up the open background between the emblem's lines;
// subtracting that from a disc leaves the emblem, exactly as written. The
// file and module were named for the emblem and have been renamed to say
// "background" instead (2026-09-08); the geometry is unchanged.
// See ../coaster_helm_of_awe_spec.md section 6 (C4, correction header) and
// ../coaster_yggdrasil_spec.md section 6 (F1).

include <helm_of_awe_pattern.scad>

coaster_diameter = 100;
thickness = 3;
edge_margin = 7;

outer_r = coaster_diameter / 2;                       // 50 mm
target_pattern_r = outer_r - edge_margin;             // 43 mm
scale_factor = target_pattern_r / native_max_r;

module coaster() {
    linear_extrude(height = thickness)
        difference() {
            circle(r = outer_r, $fn = 200);
            scale([scale_factor, scale_factor])
                helm_of_awe_background_native();
        }
}

coaster();
