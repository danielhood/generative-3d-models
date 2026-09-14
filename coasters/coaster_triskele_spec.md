# Design spec: Celtic triskele coaster

Part: `cad/coaster_triskele.scad` -> `coaster_triskele.stl`
Source pattern: `Insert-air-tribe.stl`
Revision: rev A, 2026-09-14. Fourth coaster in the set, built to the same
brief as the Helm of Awe, Yggdrasil and Tree of Life coasters (100 mm
diameter, 3 mm thick, pattern out to r = 43, solid 7 mm rim) and sharing
their tooling.
Status: **designed and mesh-verified; not yet printed.**

This is the first source in the set that needed **no repair at all**. It is
scaled, subtracted and extruded, and that is the whole part. Section 3 is
the measurement that earned that, section 5 is the case for doing nothing,
and section 6 is what went wrong anyway — an opening that made the part
worse, and two invisible spurs that made a perfect-looking mesh leak.

---

## 1. Function summary

A circular coaster, 100 mm diameter x 3 mm thick: a solid disc with a Celtic
triskele cut clean through it — a triple spiral of three interlocking arms
around a small triskele of its own, ringed by 53 round dots and enclosed by
four broken-ring arcs — with a solid 7 mm rim at the edge. The artwork is
the exact traced outline of `Insert-air-tribe.stl`, centered and rescaled to
the set's geometry, with nothing added, removed or redrawn.

The sense matches the Tree of Life coaster and is **inverted relative to the
first two in the set**: the ground is the material and the drawing is the
void. See section 3.1.

## 2. Requirements

| # | Requirement | Value |
|---|---|---|
| R1 | Coaster shape | circular |
| R2 | Coaster diameter | 100 mm |
| R3 | Coaster thickness | 3 mm, ground solid, artwork cut through |
| R4 | Pattern source | `Insert-air-tribe.stl` (Celtic triskele in a broken ring) |
| R5 | Pattern placement | centered in the coaster |
| R6 | Construction | single piece, no swap-in insert |
| R7 | Outer rim | solid 7 mm band between the coaster edge and the pattern |
| R8 | Printability | every part of the print thick enough to hold together |

R1–R8 match the Tree of Life coaster's parameters exactly, so the four read
as a set.

---

## 3. Source pattern analysis

### 3.1 The mesh

`Insert-air-tribe.stl` is a 107.2 x 107.2 x 2.5 mm square plate **lying in
YZ** (thickness along X, faces at native x = -60.5 and x = -58.0), with the
design cut clean through it. Note the plane: `Insert-tree.stl` lies in XZ
with its thickness along Y, so that build's trace recipe does not transfer
and neither does the `mirror()` it needed. Section 6, E3.

Verified the way `utilities/README.md` requires, against the source mesh and
before anything downstream was drawn:

- **Sense.** Rasterize the plate's own face triangles and look: the
  knotwork is empty space, the ground around it is solid. Confirmed again by
  `sense_of()` over the finished trace — 0 of 64 interior points sit on
  material, unanimous. Same sense as `Insert-tree.stl`, opposite to
  `insert-yggdrasil.stl` and `insert-helm-of-awe.stl`, and the module is
  named `triskele_cuts_native()` to keep it unambiguous.
- **Through-cut, not engraved.** The two faces rasterize to the same shape
  at IoU 0.997 within r = 47.5, so this is a straight cut through the plate
  and the artwork does not depend on which face you read it from.

The two faces are not interchangeable for tooling, though. The x = -58.0
face carries four blind corner pockets (bottoms at -59.0 and -58.785) and
spans the full 107.2 mm square; the x = -60.5 face is clean and spans
99.6 mm. Both checks therefore run against **x = -60.5**, because a blind
pocket shows up on a face raster but not in a `projection()` shadow, and
that discrepancy is otherwise confusing. The pockets are insert-specific and
excluded by construction: they never appear in the trace at all.

The mesh has defects, like the Helm of Awe and Tree of Life sources: 25,054
triangles, 1 shell, but **4 edges not shared by exactly 2 faces and 8
mismatched directed edges**. That is why the artwork is recovered by
`projection()` trace rather than by a 3D boolean against the source — the
C1 leak. `projection()` needs only a valid surface and went through cleanly.

### 3.2 The components

The trace gives 64 components plus the plate's own square border, and they
sort themselves by radius with no ambiguity anywhere:

| Group | Count | Radius (native) | Radius (coaster, mm) | Kept? |
|---|---|---|---|---|
| Centre triskele | 1 | 0.73–5.21 | 0.67–4.74 | kept |
| Triskele arms | 3 | 4.25–30.14 | 3.87–27.47 | kept |
| Inner dots | 3 | 20.45–24.83 | 18.63–22.63 | kept |
| Ring dots | 53 | 34.88–38.48 | 31.78–35.06 | kept |
| Outer broken-ring arcs | 4 | 43.56–47.19 | 39.69–43.00 | kept |
| Square plate border | 1 | 75.80 | — | excluded (insert-specific) |

Every part of the design proper sits inside r = 47.20 and the only other
component is at r = 75.80, so the filter is not a judgement call. Total cut
area 2,549.5 mm² native = 2,116.8 mm² at coaster scale. The dots are
circles of 2.502 mm diameter.

The design's own outer radius, 47.1910 native, is the scale reference:
scaling by 43/47.1910 = 0.911191 lands the arcs' outer edge **exactly** on
the inner edge of the plain 7 mm rim, so the set's 43/7 split needed no
adjustment for this source. The generator asserts that radius rather than
trusting it (`trace_triskele.py`), because it is the one number the whole
part is hung from.

### 3.3 Why nothing has to be redrawn — the measurement

The same measurement that condemned the Tree of Life's border, run the same
way (`utilities/printability.py`, widths at coaster scale, taken off the
source mesh before anything was drawn). All figures in mm:

| Zone | material | cut |
|---|---|---|
| Triskele arms (r 6–28) | p1 **1.04**, p5 2.32, p25 2.64, p50 2.89 | p1 1.25, p5 2.39, p50 2.56 |
| Centre triskele (r < 6) | p5 0.71, p25 0.76, p50 **0.80** | p5 0.68, p25 0.74, p50 0.75 |
| Dot ring | min 1.36, p50 1.63 | p50 2.40 (the dots) |
| Arc band | 5.90 (the four bridges) | p50 3.14 |

And the structural test on the source artwork as traced, scaled to the
coaster, before any modification:

    erode 0.00 mm ->    1 pieces | main 5764.1 mm^2 | shed 0.00 mm^2
    erode 0.20 mm ->    1 pieces | main 5364.6 mm^2 | shed 0.00 mm^2
    erode 0.30 mm ->    1 pieces | main 5136.3 mm^2 | shed 0.00 mm^2
    erode 0.40 mm ->   61 pieces | main 4919.5 mm^2 | shed 0.21 mm^2

One piece, zero shedding, through 0.30 mm of erosion **as drawn**. For
comparison, the Tree of Life source lost its entire 2,086 mm² rim at 0.20 mm
and the finished, repaired Tree of Life coaster holds to exactly the same
0.30 mm. This source arrives at the standard the previous build had to be
rescued to.

The reason is structural, not luck. Where the Tree of Life's border was the
only bridge between rim and middle and was 0.36 mm wide, this design's outer
ring is **deliberately broken**: four arcs with four 5.90 mm gaps between
them, so the rim is joined to the middle of the coaster by four bridges an
order of magnitude wider than anything that failed before. The 53 ring dots
are isolated holes in solid ground and carry no load at all.

### 3.4 The one fine feature

The centre triskele, a ~9.5 mm triple spiral inside r = 4.74 mm, is the only
part of the design near the floor: 0.80 mm median material between 0.75 mm
median cuts, a period of about 1.5 mm. 0.80 mm is two extrusions of a 0.4 mm
nozzle — printable, with no margin.

It is left exactly as drawn, for two reasons. It is an **island inside solid
ground**, so nothing depends on it structurally: it is the only thing that
sheds anywhere in the erosion ladder (section 7), and it sheds at 0.50 mm,
by which point the threshold has passed the feature's own width. And the
only lever that would thicken it — eroding the cuts, as the Tree of Life
did — would take its 0.75 mm cuts down to 0.55 mm and turn the spiral to
mud. That is the wrong trade here: per the Tree of Life's D4a, a cut the
slicer cannot resolve simply fills in, which is cosmetic and self-healing,
whereas thin material has no such mercy. Spending margin to fix a cosmetic
risk by creating a structural one is backwards.

---

## 4. Assumptions

| # | Assumption | Status |
|---|---|---|
| A1 | The square plate border and its corner features are insert-specific and excluded | Applied, same logic as the other three coasters' A1. The 4 corner marks are blind pockets, not through-holes — they do not appear in the `projection()` shadow at all. |
| A2 | Coaster depth is 3 mm, no separate base layer — the artwork is cut the full thickness | Applied, matching all three siblings' A2. The source's own 2.5 mm plate thickness is not reused. |
| A3 | "Centered" means the design's own center | Applied; the design is concentric and unambiguous. |
| A4 | Faithful reproduction is the goal wherever the source permits it | Applied, and this source permits it everywhere (3.3). The Tree of Life's A5 — "losing the source's finest detail is acceptable" — is deliberately **not** inherited: nothing here needed to be spent. |

---

## 5. Decisions

**D1 — Keep the source's sense: ground solid, artwork cut.** Same as the
Tree of Life's D1 and for the same reason. Subtracting the artwork from a
disc makes the coaster **one connected piece by construction** — it is a
disc with holes in it — so the Helm of Awe's C3 scaffolding problem does
not arise. Inverting it would leave 53 dots and three spiral arms floating
free with nothing holding them.

**D2 — Reproduce the design faithfully: no erosion, no opening, no
recomposed border.** The whole of `coaster_triskele.scad` is:

    difference() {
        circle(r = 50);
        scale(0.911191) triskele_cuts_native();
    }

This is the decision section 3.3 bought. The Tree of Life needed a 0.25 mm
cut erosion, a 0.40 mm opening and a wholly redrawn border; applying any of
that here would cost artwork weight to buy strength the part already has.
The exported mesh measures IoU **0.9969** against the source artwork
rasterized at the same scale — the design on the coaster is the design on
the plate.

An opening was tried anyway, on the assumption that it is free insurance.
It is not. See section 6, E1.

**D3 — Scale from the arcs' outer radius, not from the plate.** 47.1910
native -> 43.0 mm puts the outer arcs flush against the rim's inner edge,
which is what makes R7's 7 mm band read as a deliberate edge to the artwork
rather than as leftover space. The generator aborts if the traced rmax ever
drifts from that number.

**D4 — Zero-area spurs are removed from every traced polygon.** Not
cosmetic: they are why the first export was not watertight, and the fix went
into shared tooling. Section 6, E2.

**D5 — Single piece, no insert.** Same as all three siblings.

---

## 6. Build log

#### E1 — The opening was applied out of habit, and made the part worse

The Tree of Life ends with a morphological opening, `offset(+r) offset(-r)`,
which puts a hard floor under the minimum material width. Carrying it over
here looked like free insurance: it can only delete material thinner than
2r, and this design has almost none.

Measured at r = 0.20 and 0.30 mm against r = 0 (identical part otherwise):

| | erosion ladder | material ridge points < 0.40 mm |
|---|---|---|
| no opening | 1 piece to 0.20, 0.06 mm² shed at 0.40 | **37** |
| open 0.20 | unchanged | **117** |
| open 0.30 | unchanged | 125 |

The opening bought **nothing** structurally — every row of the ladder is the
same to within a rounding — and tripled the number of hairline material
slivers, because `offset()` at finite `$fn` re-facets all 6,435 polygon
points and sheds slivers of its own along every curve. The whole-part `p1`
material width went from 0.76 mm to 0.10 mm.

This is the Tree of Life's D5 finding generalised. That build had already
observed the opening damaging its braid (1.00 mm minimum -> sub-0.2 mm
artefacts) and concluded "open only what needs opening". The stronger
conclusion is the right one: **an opening is a repair, not a safety
margin.** It is a lossy operation that happens to pay for itself on artwork
that is genuinely too thin, and it costs on artwork that is not. Measure
before applying it, and be willing to ship a part with no repair steps at
all.

#### E2 — Two invisible spurs, and a mesh that was perfect except for being open

The first export passed everything worth looking at — 100.000 x 100.000 x
3.000 mm, 1 shell, correct volume, and a rasterized top face that matched
the source at IoU 0.997 — and `mesh_check.py` reported **2 edges not shared
by exactly 2 faces**.

The two edges were vertical, at r = 42.93 and 120° apart, each shared by
four faces. Tracing them back: two of the four arc polygons visited the same
vertex twice, wandering ~0.05 mm along the arc's outer edge and returning to
where they started — a sub-loop of **2.3e-6 mm²**. A third such spur, of
exactly zero area, sat in one of the triskele arms.

The Tree of Life build had seen these and dismissed them: its D3 notes that
the repaired components "turned out to be simple loops carrying a zero-area
spur... not genuine figure-eights", and treated that as the reassuring
outcome. It is not reassuring. A polygon that touches itself at a point is
still a valid `polygon()` and still renders the correct 2D shape, but
`linear_extrude()` turns that point into an edge shared by four side faces,
and the result is a mesh that is right in every measurable respect and not
watertight. The Tree of Life escaped only because its spurs did not land on
a shared vertex — and possibly because its `offset()` pair rewrote the
outlines anyway, which this part deliberately does not have.

Two further things worth keeping:

1. **One of the three spurs came out of a component `walk_polygon` had
   walked perfectly cleanly.** This is not a `trace_faces()` problem or a
   C2-repair problem, so the cleanup belongs on every traced polygon, not
   just the repaired ones.
2. The fix is `dxf_trace.drop_spurs()`, called from
   `pattern_trace.component_polygons()`, so every future trace in this repo
   gets it. It deletes a repeated-vertex sub-loop only when that sub-loop
   encloses less than 1e-3 mm²; a repeated vertex enclosing real area is a
   genuine figure-eight and stays `trace_faces()`'s job. Re-running
   `trace_tree_of_life.py` afterwards reproduces
   `tree_of_life_pattern.scad` and `coaster_tree_of_life.stl` byte for
   byte, so the earlier part is provably untouched.

After the repair: 0 non-manifold edges, consistent winding, and **the volume
is unchanged to the microlitre** (17,210.484 mm³ before and after) — which
is the tell that this was a validity bug and never a shape bug, and exactly
why nothing else in the toolkit caught it.

#### E3 — The plate is in a different plane, and this time the checker said so

`Insert-tree.stl` lies in XZ; this plate lies in YZ. Reusing that build's
`rotate([90,0,0]) ... mirror([0,1,0])` recipe would have produced a
transposed, mirrored trace — and a mirrored triskele is a *different design*,
since the three spirals would turn the other way.

The recipe used instead is `rotate(a = -120, v = [1,1,1])`, which cyclically
maps (x,y,z) -> (y,z,x) and is exactly what `mesh_orient.orient_to_xy(axis=0)`
does. Picking the permutation that matches the helper, rather than a
rotation about a single axis plus a compensating flip, means the trace and
every mesh-side check share one frame and no sign convention is hidden
anywhere downstream.

`orientation_iou()` scored it **0.9698 for (False, False)** against 0.53,
0.51 and 0.46 for the three flips — decisive, and the first coaster in this
repo whose trace recipe was right the first time. Three builds of paying for
this lesson, and the thing that finally made it cheap was a reusable checker
that scores all four variants in one call. The chirality helped too: this is
the first source in the set where a mirror would have been visible by eye.
It was still settled by measurement.

---

## 7. Final verified dimensions

Measured from the exported mesh (`coasters/coaster_triskele.stl`), not from
intent:

| | |
|---|---|
| Overall | Ø100.0 x 3.00 mm (bounding box) |
| Rim | solid 7 mm band, 43–50 mm radius (R7) — measured min 7.00, p50 7.12 mm |
| Pattern | triskele and border cut through a solid ground (D1) — confirmed by rasterizing the exported mesh's own top-face triangles |
| Fidelity | IoU **0.9969** against the source artwork rasterized at the same scale |
| Thickness | 3.000 mm uniform |
| Mesh | watertight: 0 edges not shared by exactly 2 triangles; consistent winding |
| Shells | 1 (single physically connected piece — R6) |
| Volume | 17,210.5 mm³ |
| Triangle count | 27,108 |
| Solid area (top face) | 5,770.4 mm² of the 7,854 mm² disc (73%) |

### Printability (R8)

Widths, from `utilities/printability.py` at 20 px/mm:

| Zone | material | cut |
|---|---|---|
| Whole part | p1 0.76, p5 1.43, p25 2.80, p50 5.22 | p25 2.42, p50 2.60 |
| Centre triskele (r < 6) | p5 0.71, p25 **0.80**, p50 0.81 | p5 0.63, p50 0.72 |
| Arms (6–28) | p5 2.31, p25 2.65, p50 2.90 | p1 1.00, p50 2.53 |
| Dot ring (31–36) | **min 1.36**, p50 1.63 | p50 2.40 |
| Arc band (39–43) | 5.90 (four bridges) | p50 3.14 |
| Rim (43–50) | min 7.00, p50 7.12 | — |

Erosion ladder — the structural test:

    erode 0.00 mm ->    1 pieces | main 5762.3 mm^2 | shed 0.00 mm^2
    erode 0.10 mm ->    1 pieces | main 5578.9 mm^2 | shed 0.00 mm^2
    erode 0.20 mm ->    1 pieces | main 5342.3 mm^2 | shed 0.00 mm^2
    erode 0.30 mm ->    2 pieces | main 5143.9 mm^2 | shed 0.00 mm^2  (largest loose 0.002 mm^2)
    erode 0.40 mm ->   27 pieces | main 4903.6 mm^2 | shed 0.06 mm^2  (largest loose 0.005 mm^2)
    erode 0.50 mm ->    6 pieces | main 4696.3 mm^2 | shed 1.29 mm^2  (largest loose 1.278 mm^2)
    erode 0.60 mm ->    6 pieces | main 4455.5 mm^2 | shed 0.67 mm^2

**Holds as one piece with zero shedding through 0.20 mm**; at 0.30 mm it
sheds a single 0.002 mm² speck, and at 0.40 mm 0.06 mm² across 27 specks —
dust, not a failure.

Everything that sheds, at every threshold, lies at **r = 2.1–4.7 mm**: it is
the centre triskele (3.4), an island inside solid ground, and it goes at
0.50 mm because that is where the threshold passes its own 0.80 mm line
weight. Nothing structural — rim, arcs, dot ring, arms — sheds anywhere on
this ladder.

Against the Tree of Life coaster, which holds one piece to 0.30 mm and then
loses 234 mm² across 513 pieces at 0.50 mm, this part is the more robust of
the two by a wide margin at the deep end, on a design that was not repaired
at all.

---

## 8. File structure

    coasters/
      Insert-air-tribe.stl            (source pattern, reference only)
      coaster_triskele_spec.md        (this file)
      coaster_triskele.stl            (final export)
      cad/
        triskele_pattern.scad         -- 64 traced CUT polygons, native scale
        coaster_triskele.scad         -- scales, subtracts, extrudes. That is all.

The pattern file is generated, not hand-made:

    coasters/trace_triskele.py      -- regenerates cad/triskele_pattern.scad
                                       from Insert-air-tribe.stl; verifies
                                       sense, nesting, orientation and the
                                       scale reference, and refuses to write
                                       on failure. Reproduces the STL byte
                                       for byte.

Tooling changed by this build, in `utilities/`:

    dxf_trace.py       -- gained drop_spurs(), which removes the zero-area
                          excursions that make an otherwise perfect
                          linear_extrude() non-watertight (E2)
    pattern_trace.py   -- component_polygons() now runs every polygon
                          through it, on both the clean-walk and the
                          repaired path

## 9. Open items

- **Not yet printed.** Mesh-verified only, same status as all three
  siblings.
- The centre triskele (3.4) is the feature to look at on a first print. Its
  0.75 mm cuts are below one nozzle width and some may partly fill in; that
  is expected and self-healing. If it reads as a solid blob rather than a
  spiral, the fix is to widen those cuts — `offset(r = +0.08)` on the
  pattern inside r = 6 — and not to touch anything else, since nothing else
  in the part is near a limit.
- The 53 ring dots are 2.50 mm holes at 1.36 mm minimum spacing. Comfortable
  for FDM, but they are the feature most likely to show elephant's foot on a
  first layer; consider printing the artwork face down.
- No preview renders are committed, matching the rest of `coasters/`.
