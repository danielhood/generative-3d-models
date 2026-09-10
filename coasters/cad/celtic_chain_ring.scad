// Replacement decorative border for the Tree of Life coaster: a two-strand
// Celtic braid, drawn as CUTS in the solid ground (same sense as
// tree_of_life_pattern.scad -- the ground is material, the drawing is the
// hole).
//
// Why this is not the source's own border. The chain ring on
// Insert-tree.stl is fine outline line-work: measured off the source mesh
// at coaster scale, its material ribbons run 0.36 mm (median; p75 0.40 mm,
// 84% of the ring under 0.60 mm) between cuts that are themselves only
// 0.63 mm wide. Both numbers are below one 0.4 mm extrusion, and the whole
// radial period is about 1.0 mm, so there is no offset, erosion or rescale
// that rescues it -- the band has to be redrawn at a printable line weight.
// That is the failure the user reported, and section 3 of the spec has the
// full measurement.
//
// Geometry. Two sinusoidal strands of constant width run around the band in
// antiphase, r(a) = rm +/- amp*sin(periods*a), so they cross 2*periods times
// and open a lens-shaped "eye" between each pair of crossings -- the
// classic twisted-cord border, and the nearest printable relative of the
// source's interlocking chain.
//
// The strands are built by true NORMAL offset of the centreline, not by
// offsetting the radius. That distinction matters here: these curves run up
// to ~39 degrees off tangential, where a radial offset of w/2 would leave a
// strand only w*cos(39) = 0.78*w wide -- it would quietly lose a fifth of
// the wall thickness at exactly the crossings, which is where the strand is
// doing the structural work.
//
// The band's inner edge is set by the tree, not by taste: the tree's root
// sweeps reach r = 37.26 mm (see tree_of_life_pattern.scad), and after the
// tree's cuts are eroded by 0.25 mm in the assembly they stop at 37.01 mm.
// An inner edge of 38.0 mm therefore leaves ~1.0 mm of solid ground between
// the tree's outermost root and the braid's outermost eye.

ring_r_in    = 38.0;   // inner edge of the braid band
ring_r_out   = 43.0;   // outer edge -- meets the plain 7 mm rim
ring_periods = 16;     // sine periods around the circle => 32 crossings
strand_w     = 1.40;   // constant strand width (material)
strand_amp   = 2.00;   // radial amplitude of each strand's centreline
ring_steps   = 720;    // samples per strand outline

ring_rm = (ring_r_in + ring_r_out) / 2;   // 40.5

// Centreline radius of a strand at angle a (degrees), phase ph (degrees).
function _braid_r(a, ph) = ring_rm + strand_amp * sin(ring_periods * a + ph);

// One point on a strand's edge: the centreline point pushed `off` mm along
// the true outward unit normal. d/dtheta is taken in radians (hence PI/180)
// so the tangent, and therefore the normal, is correct.
function _braid_pt(a, ph, off) =
    let (r  = _braid_r(a, ph),
         dr = strand_amp * ring_periods * cos(ring_periods * a + ph) * PI / 180,
         tx = dr * cos(a) - r * sin(a),
         ty = dr * sin(a) + r * cos(a),
         L  = sqrt(tx * tx + ty * ty))
    [r * cos(a) + off * ty / L,
     r * sin(a) - off * tx / L];

function _braid_edge(ph, off) =
    [for (i = [0 : ring_steps - 1]) _braid_pt(i * 360 / ring_steps, ph, off)];

// A strand is the closed band between its outer and inner offset curves.
// Both curves wind once around the centre, so the inner one is a hole in
// the outer one and a plain difference() is the whole story.
module braid_strand(ph) {
    difference() {
        polygon(points = _braid_edge(ph,  strand_w / 2));
        polygon(points = _braid_edge(ph, -strand_w / 2));
    }
}

// The CUTS: everything in the band that the two strands do not occupy.
// Callers subtract this from the coaster disc.
//
// Connectivity comes for free and is worth stating explicitly, because it
// is the thing that makes the border safe to print: each strand's peaks
// reach rm + amp + w/2 = 43.2 mm and rm - amp - w/2 = 37.8 mm, i.e. 0.2 mm
// PAST both edges of the band. Every outward peak therefore fuses into the
// plain rim and every inward peak into the field around the tree, so the
// braid is not a free-floating ring resting on tangent points -- it is
// stitched to the body of the coaster 32 times.
module celtic_chain_ring_cuts() {
    difference() {
        difference() {
            circle(r = ring_r_out, $fn = 360);
            circle(r = ring_r_in,  $fn = 360);
        }
        braid_strand(0);
        braid_strand(180);
    }
}
