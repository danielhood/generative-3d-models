# Design spec: Celtic Tree of Life coaster

Part: `cad/coaster_tree_of_life.scad` -> `coaster_tree_of_life.stl`
Source pattern: `Insert-tree.stl`
Revision: rev A, 2026-09-09. Third coaster in the set, built to the same
brief as the Helm of Awe and Yggdrasil coasters (100 mm diameter, 3 mm
thick, pattern out to r = 43, solid 7 mm rim) and sharing their tooling.
Status: **designed and mesh-verified; not yet printed.**

This is the first source in the set that **could not be reproduced
faithfully at any scale that fits the brief.** Its line weight is roughly
2x too fine for FDM at 100 mm. The border is therefore recomposed rather
than repaired, and the tree is redrawn at a heavier line weight. Sections 3
and 5 are the case for that; section 6 is what went wrong along the way.

---

## 1. Function summary

A circular coaster, 100 mm diameter x 3 mm thick: a solid disc with the
Celtic Tree of Life cut clean through it, ringed by a two-strand Celtic
braid, with a solid 7 mm rim at the edge. The tree is redrawn from the exact
traced outline of `Insert-tree.stl`, centered, rescaled to the set's
geometry, and opened up to a printable line weight. The source's own chain
border is discarded and replaced.

Note the sense, because it is **inverted relative to the other two coasters
in the set**: here the ground is the material and the drawing is the void.
See section 3.

## 2. Requirements

| # | Requirement | Value |
|---|---|---|
| R1 | Coaster shape | circular |
| R2 | Coaster diameter | 100 mm |
| R3 | Coaster thickness | 3 mm, ground solid, artwork cut through |
| R4 | Pattern source | `Insert-tree.stl` (Celtic Tree of Life in a chain ring) |
| R5 | Pattern placement | centered in the coaster |
| R6 | Construction | single piece, no swap-in insert |
| R7 | Outer rim | solid 7 mm band between the coaster edge and the pattern |
| R8 | **Printability** | every part of the print thick enough to hold together — the reason this build exists |

R1–R7 match the Helm of Awe coaster's final rev G parameters exactly, so the
three read as a set. R8 is new to this build and is the whole problem.

---

## 3. Source pattern analysis

### 3.1 The mesh

`Insert-tree.stl` is a 107.2 x 107.2 x 2.5 mm square plate lying in XZ
(thickness along Y, faces at native y = 58.0 and y = 60.5), with the design
**cut clean through it**. Verified the way `utilities/README.md` requires,
against the source mesh and before anything downstream was drawn: rasterize
the plate's own face triangles and look. The knotwork is empty space; the
ground around it is solid.

That is the **opposite** of `insert-yggdrasil.stl` and
`insert-helm-of-awe.stl`, whose traced polygons were the artwork's negative
space. Here the traced polygons *are* the artwork. Getting this backwards is
the single most expensive mistake in this repo's history (see the Yggdrasil
spec, section 6, F1), so it is checked, not assumed, and the module is named
`tree_of_life_cuts_native()` to keep it unambiguous.

The mesh has defects, like the Helm of Awe source and unlike Yggdrasil:
82,992 triangles, 1 shell, but **14 edges not shared by exactly 2 faces and
31 mismatched directed edges**. That is why the artwork is recovered by
`projection()` trace rather than by a 3D boolean against the source — the
C1 leak. `projection()` needs only a valid surface and went through cleanly.

### 3.2 The components

The trace gives 136 connected components, which sort themselves cleanly by
radius:

| Group | Count | Radius (native) | Kept? |
|---|---|---|---|
| Tree knotwork cuts | 62 | rmin 1.31–30.08, **rmax up to 40.97** | **kept** (rescaled and opened up) |
| Chain-ring cuts | 73 | rmin 41.63–43.10, rmax 45.81–47.28 | **discarded** — see 3.3 |
| Square plate border | 1 | 75.80 | excluded (insert-specific) |

The 73 ring components are two interleaved radial families 1.04 mm apart —
the chain's double outline. The split between tree and ring is made on each
component's *minimum* radius, where there is a wide empty gap (30.08 vs
41.63), so it is not a judgement call.

The tree's own **maximum** radius is a different and much tighter number:
40.97 native = 37.26 mm at coaster scale. Its two big root sweeps run out to
within 0.66 mm of where the source ring began. That, not taste, is what sets
the replacement border's inner edge.

11 of the 136 components had a self-touching vertex and would not close
under `dxf_trace.walk_polygon` (its documented C2 failure mode). 8 of those
are in the discarded ring; only 3 needed repair. See section 5, D3.

### 3.3 Why the border cannot be kept — the measurement

All widths below are at coaster scale (scale factor 0.909452), measured off
the source mesh with `utilities/printability.py`, as 2x the distance-to-edge
along the ridge of the distance field:

| | material ribbons | cut strokes |
|---|---|---|
| **Chain ring** | median **0.361 mm**, p75 0.400, 84% under 0.60 | median 0.632 mm, **max 0.721** |
| **Tree knotwork** | median 0.539 mm, p25 0.361, p10 0.141 | median 1.063 mm, p75 1.628 |

The ring is the fatal one. Its material ribbons are 0.36 mm — **less than
one 0.4 mm extrusion** — and the cuts separating them are only 0.63 mm, so
the entire radial period is about 1.0 mm. There is no offset, erosion or
rescale that fixes that: widening the ribbons necessarily closes the cuts,
and the band has no room to give. The border has to be redrawn.

### 3.4 Why it failed the way it did

Running the unrepaired source artwork through the erosion ladder reproduces
the reported print failure exactly:

    erode 0.00 mm ->   91 pieces | main 5914.6 mm^2 | shed    0.24 mm^2
    erode 0.10 mm ->  113 pieces | main 5515.3 mm^2 | shed    0.24 mm^2
    erode 0.20 mm ->  135 pieces | main 2841.3 mm^2 | shed 2224.59 mm^2   <-- fails
    erode 0.30 mm ->  174 pieces | main 2443.0 mm^2 | shed 2344.85 mm^2

At 0.20 mm the part comes apart into two major pieces:

    piece #1   2841.3 mm^2   radius  0.0 .. 41.8 mm    (tree + inner field)
    piece #2   2085.9 mm^2   radius 38.8 .. 50.0 mm    (the rim)

**The rim falls off.** The chain ring's 0.36 mm ribbons are the only
structural bridge between the coaster's outer rim and its middle, so when
they go, the coaster separates into a ring and a disc. That is the
mechanism behind "the decorative ring contains very fine parts that do not
have enough strength to stay together once printed", and it is worth
noting that `mesh_check.py` is perfectly happy with this geometry — 1 shell,
watertight, correct bounding box. Shell count does not answer this question.
`printability.py` exists because of this build.

---

## 4. Assumptions

| # | Assumption | Status |
|---|---|---|
| A1 | The square plate border and its corner features are insert-specific and excluded | Applied, same logic as the other two coasters' A1. The 4 corner marks visible on the plate's face are blind pockets, not through-holes — they do not appear in the `projection()` shadow at all. |
| A2 | Coaster depth is 3 mm, no separate base layer — the artwork is cut the full thickness | Applied, matching both siblings' A2. The source's own 2.5 mm plate thickness is not reused. |
| A3 | "Centered" means the design's own center | Applied; the source ring is concentric and unambiguous. |
| A4 | The set's 43 mm pattern radius / 7 mm rim is worth preserving over giving the new border more room | Applied. Widening the border outward would have broken the set; widening it inward is blocked by the tree's roots at 37.26 mm (3.2). The border therefore gets the 38.0–43.0 mm band and no more. |
| A5 | Losing the source's finest detail is acceptable; losing the design's legibility is not | Applied, and it is the axis every parameter in section 5 was tuned along — by looking at the rendered result, not by reading percentiles. See D4. |

---

## 5. Decisions

**D1 — Keep the source's sense: ground solid, artwork cut.** Inverting it to
match the other two coasters (artwork solid, background open) was
considered and rejected on structural grounds. In the negative, the tree's
knot bands and the border's links are both material, but the thing that
currently joins them — the solid field between the canopy and the ring — is
open, so the tree would float free inside the border with nothing holding
it. That is the Helm of Awe C3 scaffolding problem, deliberately not
re-entered. Keeping the source's sense makes the coaster **one connected
piece by construction**: it is a disc with holes in it.

**D2 — The border is recomposed, not repaired: a two-strand Celtic braid.**
Two sinusoidal strands of constant width run around the 38.0–43.0 mm band in
antiphase, r(a) = 40.5 +/- 2.0*sin(16a), crossing 32 times and opening a
lens-shaped eye between each pair of crossings. Strand width 1.40 mm, eye
opening 2.6 mm by design and **2.62 mm measured** off the exported mesh.
This is the nearest printable relative of the source's interlocking chain —
same rhythm (32 crossings against the original's ~37 links), same Celtic
idiom, roughly 4x the line weight.

Strands are built by **true normal offset of the centreline**, not by
offsetting the radius. These curves run up to ~39 degrees off tangential,
where a radial offset of w/2 would leave the strand only w*cos(39) = 0.78w
wide — quietly losing a fifth of the wall thickness at exactly the
crossings, which is where the strand carries load.

Each strand's peaks reach 0.2 mm *past* both edges of the band, so every
outward peak fuses into the plain rim and every inward peak into the field
around the tree. The braid is stitched to the body of the coaster 32 times
rather than resting on tangent points — which is precisely what the source
border failed to do (3.4).

**D3 — The 3 broken tree components are repaired, not dropped.**
`dxf_trace.walk_polygon` cannot close a component whose curve touches
itself, and this file's own advice was to drop it or substitute a rotated
copy of a symmetric twin. Both are lossy and neither applies to an
asymmetric tree. Instead `trace_faces()` walks the component as a planar
graph and returns its real faces. All 3 turned out to be simple loops
carrying a zero-area spur — a duplicated edge traversed both ways — not
genuine figure-eights, which is why each returned a clean +/- area pair plus
a 0.0. The routine is now in `utilities/dxf_trace.py`.

**D4 — Tree line weight: erode the cuts 0.25 mm, then open the section
0.40 mm.**

    offset(r = +0.40) offset(r = -0.40)          // morphological opening
        difference() {
            circle(r = 50);
            offset(r = -0.25) scale(0.909452) tree_of_life_cuts_native();
        }

The first offset shrinks every cut by 0.25 mm on all sides, which widens
every material ribbon between them by 0.50 mm and costs the cut bands the
same 0.50 mm — which they can afford (median 1.06 mm) and the ribbons
cannot (median 0.54 mm). The second pair is an opening: it deletes anything
still thinner than 0.80 mm, leaves everything wider untouched, and rounds
the artwork's sharp spikes to a 0.40 mm radius, which is the right thing to
do to tips a 0.4 mm nozzle cannot draw anyway.

0.25 mm is where the tree still reads. This was settled by rendering the
result and looking at it at 0.15 / 0.25 / 0.35 / 0.45: at 0.35 the outer
leaves begin breaking into dashes, and at 0.45 the canopy is scratchwork.

**An opening of the CUTS was tried too and rejected — see section 6, D4a.**

**D5 — The braid is subtracted *after* the opening.** The opening is applied
to the disc-plus-tree only. The braid does not need it — it is drawn at a
guaranteed 1.40 mm strand width — and running it through the offset pair
actively damaged it, taking the band from a 1.00 mm minimum to sub-0.2 mm
hairline artefacts. Opening only what needs opening is both cleaner and
faster.

**D6 — Single piece, no insert.** Same as both siblings.

---

## 6. Build log

#### D4a — Opening the cuts destroys the knot; the numbers said it was fine

The natural companion to D4 is to open the *cuts* as well, dropping cut
strokes too narrow for the nozzle so that the STL is honest about what will
actually print. Tried at kappa = 0.40 mm, it produced the best statistics of
the whole build:

    material  p1 0.86  p5 1.08  p25 1.86  p50 2.34
    cut       p1 0.81  p5 0.92  p25 1.17  p50 1.40

Both distributions comfortably clear 0.8 mm. The rendered part is
unrecognisable: the knot ribbons are severed at every crossing and the tree
is a scatter of loose dashes. An opening cuts a region wherever it pinches,
and a Celtic knot *deliberately* pinches at every over/under crossing — so
the operation attacks precisely the design's defining feature.

Two things worth keeping from this:

1. The right operation was per-region, not morphological: drop a whole cut
   region that is never wider than the threshold, and keep regions that are
   wide somewhere and pinch elsewhere. That preserves ribbons intact.
2. **Thin cuts and thin material are not symmetric risks.** A cut the slicer
   cannot resolve simply fills in, which *adds* material — the failure is
   cosmetic and self-healing. Thin material has no such mercy. So the final
   build leaves narrow cuts alone and spends all its margin on material.

The lesson is the one this repo keeps relearning from the other side: the
statistics were not wrong, they were answering a different question than the
one that mattered. Render it and look.

#### D6a — The trace came out vertically mirrored, and every number was right

`projection(cut=false) rotate([90,0,0]) ...` maps (x,y,z) -> (x,-z,y), so
the projection lands at (x, 60-z) — **vertically flipped** relative to the
plate as drawn. The Tree of Life was assembled upside down: canopy at the
bottom, roots arching over the top.

What makes this worth recording is that nothing measurable was wrong. Areas,
radii, component counts, width distributions, connectivity — all identical
under a mirror, all cross-checked, all correct. The design is near-symmetric
left-to-right, so the usual mirror tell was absent too. It survived until
the assembled part was rendered and looked at.

Settled by measurement rather than by eye, once suspected: rasterize the
emitted polygons against the source mesh's own cut region and score the
overlap. **IoU 0.28 as traced, 0.94 mirrored.** The fix went into the trace
recipe rather than as a flip in the extraction script, so there is no hidden
sign convention downstream; re-deriving the pattern through the corrected
trace reproduces the STL byte for byte.

Third orientation bug in three coasters. `projection()` after a `rotate()`
deserves an explicit orientation check every time, and the IoU test above is
a cheap one.

#### D7 — The distance transform was wrong, and it failed *large*

The width measurements all rest on a Euclidean distance transform written
for this build (no numpy in this environment). The textbook formulation uses
+inf as the "foreground, no seed yet" sentinel. In floating point that is
wrong: the lower-envelope step computes `((f[q]+q^2) - (f[v]+v^2)) / (2q-2v)`,
inf - inf is NaN, `NaN <= z[k]` is False, so the pop branch never fires and
the envelope silently corrupts.

It passed a 7x7 hand-checked unit test. It reported a **112 mm inscribed
width inside a 100 mm disc**, and a 0.004 mm^2 island as 34.75 mm wide.

The tell was a result that was internally impossible rather than merely
surprising — a hand-sized number where a dust-sized one belonged. Fixed with
a large *finite* sentinel, where the offsets cancel exactly and give the
correct s = (q+v)/2. Now verified against brute force on random rasters and
against a disc of known radius, both wired into `utilities/edt.py`'s
`__main__`.

This is the Helm of Awe C4 pattern again — a buggy checker, not a buggy
part — and the same rule closed it: when a derived measurement contradicts
something you can state on physical grounds, suspect the measurement first.

#### D8 — Two more checker bugs, same session, same shape

Both found by output that could not be true, not by review:

- `ImageChops.invert()` on a mode-`"1"` PIL image does not do what it looks
  like it does. It produced a material mask covering 2045 mm^2 of a 7854 mm^2
  disc for a design that is 80% solid. Replaced throughout with explicit
  bytearray logic; the giveaway was that material + cuts no longer summed to
  the disc's area, which is now an assertion worth keeping.
- A dilation was implemented as `edt2d(mask) <= r^2`. Every *background*
  cell has distance 0 and passes that test, so the dilation returned the
  entire raster and an "opening" reported removing 2506 mm^2 from a design
  whose whole cut area was 1314 mm^2. Dilation needs the transform of the
  **complement**. Both forms are now spelled out in `utilities/edt.py`.

#### D9 — The sense check was nearly a coin flip, for a boring reason

Recorded because it is the check this repo leans on hardest. `sense_of()`
asks the source mesh whether there is material at a point inside each traced
polygon; 0-of-N means the polygons are cut-outs, N-of-N means raised
artwork. Written the obvious way, using each polygon's **area centroid**, it
returned **28 of 62** — an even split, which reads as "this trace mixes
artwork and background and must be separated before use". Entirely wrong,
and wrong in a direction that would have blocked a correct build.

The centroid of a long curved ribbon lies outside the ribbon. Celtic
knotwork traces into almost nothing but long curved ribbons, so the probe
was mostly sampling whatever sat next door. Replaced with a scanline
interior point — guaranteed inside a simple polygon — which returns **0 of
62**, unanimous, matching what rasterizing the plate showed directly on day
one.

Two things worth carrying forward. First, the generator now refuses to write
the pattern file unless this check is near-unanimous, rather than taking a
majority: a genuine 50/50 is a stop, and so is a fake one. Second, this is
the fourth checker bug in this build (D7, D8 x2, D9) against zero part bugs
found by review. Every one surfaced as a number that was internally
impossible or implausible rather than merely surprising, and every one would
have been invisible if the value had landed somewhere unremarkable.

#### A note on cusps, and why `min` is not the headline number

The finished part reports a minimum material width of 0.10 mm at 20 px/mm —
which looks like a failure until you re-measure at 40 px/mm and get 0.05 mm.
The reported width **scales with the pixel size**, so these are not ribbons
of any fixed width: they are cusps, isolated points where two cut regions
meet and pinch the material between them to zero. There are about 96 of
them, all in the tree.

A cusp is a real geometric feature but not a structural one, and the erosion
ladder is what says so: removing everything thinner than 0.60 mm still
leaves the part in one piece with **zero** shed area, so no cusp is
load-bearing. `min` over a rasterized field is a resolution artefact
detector; the erosion ladder is the structural test. `printability.py` now
prints that warning next to the number.

---

## 7. Final verified dimensions

Measured from the exported mesh (`coasters/coaster_tree_of_life.stl`), not
from intent:

| | |
|---|---|
| Overall | Ø100.0 x 3.00 mm (bounding box) |
| Rim | solid 7 mm band, 43–50 mm radius (R7) — measured p5 7.00, p50 7.04 mm |
| Braid band | 38.0–43.0 mm, two-strand braid (D2) |
| Pattern | tree and braid cut through a solid ground (D1) — confirmed by rasterizing the exported mesh's own top-face triangles |
| Thickness | 3.000 mm uniform |
| Mesh | watertight: 0 edges not shared by exactly 2 triangles; consistent winding |
| Shells | 1 (single physically connected piece — R6) |
| Volume | 19,053.7 mm^3 |
| Triangle count | 55,116 |
| Solid area (top face) | 6,390.5 mm^2 of the 7,854 mm^2 disc (81%) |

### Printability (R8)

Widths, from `utilities/printability.py`:

| Zone | material | cut |
|---|---|---|
| Whole part | p5 **1.00**, p25 1.20, p50 1.43, p75 4.30 | p25 0.30, p50 0.86 |
| Tree field (r < 37.5) | p5 0.95, p25 1.10, p50 1.84 | p25 0.40, p50 1.00 |
| Braid band (37.5–43.5) | **min 1.00**, p5 1.17, p50 1.26, max 3.13 | p50 0.61, max 2.62 |

Erosion ladder — the structural test:

    erode 0.00 mm ->   1 pieces | main 6390.5 mm^2 | shed 0.00 mm^2
    erode 0.10 mm ->   1 pieces | main 6103.1 mm^2 | shed 0.00 mm^2
    erode 0.20 mm ->   1 pieces | main 5730.5 mm^2 | shed 0.00 mm^2
    erode 0.30 mm ->   1 pieces | main 5412.3 mm^2 | shed 0.00 mm^2
    erode 0.40 mm ->  22 pieces | main 5026.0 mm^2 | shed 0.12 mm^2  (largest loose 0.027 mm^2)
    erode 0.50 mm -> 513 pieces | main 4450.6 mm^2 | shed 234.60 mm^2

**Holds as one piece with zero shedding through 0.30 mm**, so every
structural connection in the part is at least ~0.6 mm wide. At 0.40 mm it
sheds 0.12 mm^2 total — 21 specks, largest 0.027 mm^2 — which is dust, not
a failure. Compare the source at the same thresholds (3.4), where 2,086 mm^2
of rim detaches at 0.20 mm.

Against the Yggdrasil coaster, which survived 0.40 mm cleanly, this part has
slightly less margin. It is nonetheless the denser design of the two, and
the braid band — the thing that actually failed before — is now the
*strongest* part of the artwork at a 1.00 mm minimum.

---

## 8. File structure

    coasters/
      Insert-tree.stl                   (source pattern, reference only)
      coaster_tree_of_life_spec.md      (this file)
      coaster_tree_of_life.stl          (final export)
      cad/
        tree_of_life_pattern.scad       -- 62 traced tree CUT polygons, native scale
        celtic_chain_ring.scad          -- the replacement two-strand braid, parametric
        coaster_tree_of_life.scad       -- scales, erodes, opens, subtracts, extrudes

The pattern file is generated, not hand-made — unlike the two earlier
coasters, whose traces cannot be re-derived:

    coasters/trace_tree_of_life.py    -- regenerates cad/tree_of_life_pattern.scad
                                         from Insert-tree.stl; verifies sense and
                                         orientation and refuses to write on failure.
                                         Reproduces the STL byte for byte.

New reusable tooling extracted from this build, in `utilities/`:

    edt.py             -- exact Euclidean distance transform + erode/dilate/opening
    raster.py          -- binary masks over a mm grid: build, combine, label, score
    mesh_orient.py     -- get a plate-like source mesh into the XY plane
    pattern_trace.py   -- source insert -> verified polygons -> pattern .scad
    printability.py    -- minimum widths and the erosion-connectivity ladder
    dxf_trace.py       -- gained trace_faces(), which repairs its own C2 failure mode

## 9. Open items

- **Not yet printed.** Mesh-verified only, same status as both siblings.
- The braid is parametric (`ring_periods`, `strand_w`, `strand_amp` in
  `celtic_chain_ring.scad`). If the first print shows the eyes reading as
  mud at arm's length, drop `ring_periods` to 12–14 and re-render; nothing
  downstream depends on the count.
- The tree's finest source detail — leaf veins and the hairline separators
  inside the knot — is gone by construction (D4), not by accident. The cut
  area drops from 1,342 mm^2 as traced to 864 mm^2 as built. If a
  test print shows more headroom than 0.30 mm of erosion suggests,
  `tree_erode` can be relaxed toward 0.15 mm to bring some of it back.
- Roughly 96 cusps remain in the tree (section 6). They are not structural,
  but they are where the slicer will make its own decisions, and they are
  the first place to look if a print shows unexpected gaps.
