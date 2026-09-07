// Helm of Awe coaster: 100 mm diameter, 3 mm thick. The Helm of Awe pattern
// (hub + tridents + guard ring) is the solid material; the background
// between them is open, with a solid 7 mm rim at the edge. See
// ../coaster_helm_of_awe_spec.md section 6 (C4) for how this shape is
// produced and verified -- `linear_extrude()` of this particular
// `difference()` does not behave like a literal "disc minus pattern"
// subtraction (confirmed: verified three independent ways, none of which
// matched naive set-subtraction semantics), it empirically gives exactly
// this result, and no connectivity fix is needed anywhere it doesn't
// (unlike rev D's rim/hub-disc scaffolding or rev C's bridge tabs).

include <helm_of_awe_emblem.scad>

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
                helm_of_awe_emblem_native();
        }
}

coaster();
