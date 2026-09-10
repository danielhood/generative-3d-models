// Celtic Tree of Life coaster: 100 mm diameter, 3 mm thick, to the same
// brief as the Helm of Awe and Yggdrasil coasters (pattern out to r = 43,
// solid 7 mm rim from 43 to 50) so the three read as a set.
//
// The sense here is inverted relative to the other two. Those two source
// inserts carried the artwork as the hole's *negative* -- their traced
// polygons were the background, and the design was what survived. This
// source is the other way round: Insert-tree.stl is a solid plate with the
// knotwork cut clean through it, so the ground is the material and the
// drawing is the void. The construction below subtracts the artwork from a
// disc, which means the coaster is one connected piece by construction --
// there is no scaffolding problem to solve here at all.
//
// What the printability repair does, and why each step is here:
//
//   1. offset(r = -tree_erode) on the tree's cuts.
//      The source draws the knot as wide cut bands separated by hairline
//      ribbons of material -- 0.54 mm wide at the median, 0.14 mm at the
//      10th percentile, measured at coaster scale. Shrinking every cut by
//      0.25 mm on all sides widens every one of those ribbons by 0.50 mm
//      and costs the cut bands the same 0.50 mm, which they can afford
//      (they run 1.06 mm at the median). This is the one step that trades
//      artwork weight for strength, and 0.25 mm is where the tree still
//      reads: at 0.35 mm the outer leaves start breaking into dashes.
//
//   2. offset(r = +open) offset(r = -open) on the finished 2D section.
//      A morphological opening. It deletes anything still thinner than
//      2*open = 0.80 mm and leaves everything wider untouched, so it puts
//      a hard floor under the minimum material width instead of hoping
//      one. It also rounds the artwork's sharp spikes to a 0.40 mm radius,
//      which is the right thing to do to tips a 0.4 mm nozzle cannot draw.
//
// An opening of the CUTS was tried too, to drop cuts too narrow to print,
// and rejected: it severs the knot ribbons at the crossings where they
// deliberately pinch, and the tree falls apart into loose dashes. The
// surviving narrow cuts are safe to leave -- a cut the slicer cannot
// resolve simply fills in, which adds material. Thin material is the
// failure mode; thin cuts are not. Spec section 6, D4.

include <tree_of_life_pattern.scad>
include <celtic_chain_ring.scad>

coaster_diameter = 100;
thickness        = 3;
edge_margin      = 7;

outer_r           = coaster_diameter / 2;        // 50 mm
target_pattern_r  = outer_r - edge_margin;       // 43 mm
scale_factor      = target_pattern_r / native_max_r;

tree_erode = 0.25;   // cut shrink, per side (step 1 above)
open_r     = 0.40;   // min material half-width (step 2 above)

// Note the ordering: the opening is applied to the disc-plus-tree ONLY, and
// the braid is subtracted afterwards. The braid does not need the opening --
// it is drawn at a guaranteed 1.40 mm strand width and measures 1.00 mm
// minimum straight off the mesh -- and running it through the offset pair
// actively hurt it, leaving hairline slivers in a band that had none
// (measured: the ring band went from 1.00 mm minimum to sub-0.2 mm
// artefacts). Opening only what needs opening is both faster and cleaner.
// Spec section 6, D5.
module coaster_section() {
    difference() {
        offset(r = open_r, $fn = 32)
        offset(r = -open_r, $fn = 32)
            difference() {
                circle(r = outer_r, $fn = 360);
                offset(r = -tree_erode, $fn = 16)
                    scale([scale_factor, scale_factor])
                        tree_of_life_cuts_native();
            }
        celtic_chain_ring_cuts();
    }
}

module coaster() {
    linear_extrude(height = thickness)
        coaster_section();
}

coaster();
