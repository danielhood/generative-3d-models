// Yggdrasil coaster: 100 mm diameter, 3 mm thick. The tree -- trunk,
// branches and roots -- is the solid material; the background between its
// limbs is open, with a solid 7 mm rim at the edge.
//
// The traced artwork (yggdrasil_pattern.scad) is the background, not the
// tree: the source insert is a plate with this design cut through it, so
// the tree is the remainder of a disc once the 22 background regions are
// removed. That makes the construction below a literal subtraction, and it
// does the rim in the same stroke -- every background region is bounded on
// the outside by the design's own circle at r = 48.0836 native (43 mm once
// scaled), so everything from 43 mm out to the 50 mm edge survives as the
// rim, already fused to every branch and root tip that reaches it.
//
// The fill direction here was still checked against the exported mesh
// rather than assumed -- see ../coaster_yggdrasil_spec.md section 6.

include <yggdrasil_pattern.scad>

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
                yggdrasil_background_native();
        }
}

coaster();
