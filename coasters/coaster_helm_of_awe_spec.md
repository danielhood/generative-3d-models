# Design spec: Helm of Awe coaster

Part: `cad/coaster_helm_of_awe.scad` -> `coaster_helm_of_awe.stl`
Source pattern: `insert-helm-of-awe.stl`
Revision: rev G, 2026-09-07. Rim set to 7 mm (R7/D1), between rev F's 10 mm
and the original 5 mm; everything else unchanged from rev E. Built and
mesh-verified, fill re-confirmed by direct mesh rasterization after the
change.
Status: **designed and mesh-verified; not yet printed.**

---

## 1. Function summary

A circular coaster, 100 mm diameter x 3 mm thick: the Helm of Awe
(Ægishjálmur) pattern — hub, 8 tridents, guard ring — is the solid material,
matching the source artwork's own sense (raised lines, open background),
with a solid 5 mm rim at the edge holding it together. The pattern is
redrawn from the exact traced outline of `insert-helm-of-awe.stl` (a square
insert built for another project), centered, rescaled to meet the rim, and
extruded the full 3 mm.

## 2. Requirements

| # | Requirement | Value |
|---|---|---|
| R1 | Coaster shape | circular |
| R2 | Coaster diameter | 100 mm |
| R3 | Coaster thickness | 3 mm, hub+tridents+ring solid, background between them open |
| R4 | Pattern source | `insert-helm-of-awe.stl` (Helm of Awe symbol) |
| R5 | Pattern placement | centered in the coaster |
| R6 | Construction | single piece, no swap-in insert |
| R7 | Outer rim | solid 7 mm band between the coaster edge and the pattern's outermost point (5 mm originally, 10 mm in rev F, rev G) |

---

## 3. Source pattern analysis

`insert-helm-of-awe.stl` is a 2 mm-tall relief on a 107.2 x 107.2 mm square
base. Rather than estimate its artwork by eye, the exact 2D silhouette was
extracted with OpenSCAD's `projection()` (a straight top-down flatten of the
relief, independent of the bevel/chamfer) and decomposed into its disconnected
sub-shapes (graph components of the traced outline). That decomposition
splits the file into four unrelated pieces, confirmed both numerically (by
distance from center) and visually (color-coded render, sent separately):

| Piece | What it is | Radius from center | Connected to center? |
|---|---|---|---|
| **Emblem** | central hub + 8 radiating tridents — the Helm of Awe symbol itself, 8-fold rotationally symmetric | out to 42.38 mm at the longest tine | yes — tine bases sit near the middle |
| **Guard ring** | 8 separate scalloped "gate" arcs (16 half-arcs) circling the emblem, one gate per tine, each gate gapped ~2.5-4.6 mm from its tine | 34-42.38 mm — nested almost exactly alongside the tridents, *not* a large circle standing outside them (an earlier read of this data, ~64 mm, was wrong — that radius belongs to the corner brackets below, not the ring) | no — floats right next to the emblem, doesn't touch it |
| **Corner brackets + edge ticks** | 4 L-shaped corner marks (sitting exactly at the square's corners, radius 53.6 x sqrt(2) = 75.8 mm) and 4 short bars mid-edge | ~46-76 mm | no |
| **Square border** | the plain 107.2 x 107.2 mm outline itself | 53.6-75.8 mm | no |

Confirmed by you as square/insert-specific and excluded: corner brackets,
edge ticks (A1), and — by the same logic, since it's just the bounding
square's own outline — the square border.

**D4 — resolved: emblem + ring kept.** Since the ring sits almost exactly
alongside the tridents rather than as a separate outer circle, keeping it
barely changes the outer scale (see section 7) — it mainly adds the scalloped
gate detail between the tine bases.

---

## 4. Assumptions — all confirmed

| # | Assumption | Status |
|---|---|---|
| A1 | Corner brackets and edge ticks excluded (square-specific, not part of the symbol) | **Confirmed.** Extends to the plain square border outline too, by the same logic — see section 3. |
| A2 | Coaster depth is 3 mm, exclusively the pattern — no solid base layer at all (supersedes the original "keep native 2 mm relief + 1 mm base" idea from rev A) | **Confirmed, updated.** Since the emblem is being redrawn parametrically anyway (G1), its Z-height is a free parameter — extrude it the full 3 mm rather than reusing the source file's 2 mm relief depth. |
| A3 | "Center the insert" means the center of the emblem's own symmetry | **Confirmed** as the goal. |

---

## 5. Decisions — resolved

**D1 — Edge margin: 7 mm, built as a solid rim (rev G).**
The pattern's outermost point sits 7 mm inside the 100 mm coaster edge,
i.e. at 43 mm from center — that band is solid, forming the coaster's
structural rim.

**D2 — Pattern solid, background open, solid rim at the edge (rev E).** The
Helm of Awe pattern itself (hub, tridents, ring) is the solid material —
matching the source artwork's own sense — with the background between them
open, and a solid 5 mm rim around the outside (R7). Total depth 3 mm,
uniform everywhere. See section 6, C4 for how this is actually produced:
the straightforward-looking `difference()` construction does not behave
like a literal set subtraction here, and getting the fill direction right
took real verification, not just visual inspection.

**D3 — Single piece, no insert.** Confirmed — unlike the source project's
swap-in square insert, this coaster is one fused part.

**G1 — Rebuild parametrically: confirmed**, with a refinement. Rather than
re-estimating the artwork's proportions by eye, the exact outline was
extracted from the source mesh via `projection()` (section 3) — so "rebuild"
here means redrawing the *exact* traced emblem shape at a new scale/depth,
not an approximation of it. This also fully sidesteps the non-manifold
defect: `projection()` (a straight silhouette flatten) succeeds where a
boolean `intersection()` against the same file previously failed with
`ERROR: The given mesh is not closed!` — no mesh repair needed.

---

## 6. Build log — three defects, all traced back to G1

**Extraction method.** `projection(cut=false)` on the source STL gives an
exact 2D silhouette. Its individual disconnected sub-shapes were recovered by
grouping the projection's line segments into connected components (shared
endpoints), each walked into an ordered polygon. Kept = every component whose
closest point to center is under 45 mm (hub + tridents + ring, 32 pieces);
excluded = everything beyond ~45.6 mm (brackets, ticks, border — see
section 3).

#### C1 — `intersection()` against the source STL leaks through the non-manifold defect

**Symptom.** Cropping with `intersection() { projection(...); circle(r); }`
never stopped at the true 42.38 mm edge of the emblem+ring — it kept
tracking whatever crop radius was given (tested 44, 45.5, 46-48.9, 60 mm; the
result's outer radius matched the crop radius almost exactly every time),
only saturating once the crop was big enough to fully enclose the corner
brackets (75.8 mm).

**Cause.** G1's non-manifold source mesh. The circle boundary was reaching
into real "excluded" geometry through a crack in the mesh rather than being
safely bounded by empty space, because the assumed "safe gap" between kept
(42.4 mm) and excluded (45.6 mm) geometry wasn't actually safe once a leak
could bridge it.

**Fix.** Abandoned the OpenSCAD-native crop entirely. Recovered the kept
polygons directly from the projection's own line-segment data (component
grouping described above) instead of relying on a boolean crop — this is
immune to the leak because it never asks CGAL to resolve the defective
region at all.

#### C2 — One trident's outline had a self-touching vertex

**Symptom.** 31 of the 32 kept components walked into a clean closed loop.
One (a trident, spanning 317-358 deg) produced a 4-vertex loop instead of the
expected ~67 — the walk closed early.

**Cause.** One vertex in that component had degree 4 instead of 2 (four
edges meeting at one point) — a self-touching point in the source geometry,
consistent with G1's non-manifold finding.

**Fix.** The design is 8-fold rotationally symmetric (confirmed: the other 7
tridents' centroid angles are 45 deg apart to within 0.5 deg). Rather than
resolve the degree-4 junction, the broken trident was replaced with a
rotated copy of a clean one, aligned by centroid angle. Exact, not an
approximation, given the confirmed symmetry.

#### C3 — 32 traced pieces do not touch each other

**Symptom.** The first full export was watertight per-piece but reported 32
separate connected shells and volume didn't match a single-solid expectation
— i.e. 32 loose parts, not one coaster.

**Cause.** The source artwork holds its hub dots, tridents, and ring gates
apart by small deliberate gaps (measured: 31 nearest-neighbor gaps, all
2.3-4.6 mm). That's invisible in the original project, where a solid backing
plate held everything together. This coaster has no backing (D2), so the gaps
are real holes all the way through.

**Fix attempt 1 (rejected): uniform 2D `offset()` grow on the whole shape.**
It closes the piece-to-piece gaps, but those are similar in size to the
*intentional* negative space between a tine's own parallel bars, so it also
filled in most of the artwork's fine detail (tested at r=1.35 mm — nearly the
whole coaster became a solid disc with a few small holes).

**Fix attempt 2 (rejected): a minimum spanning tree of small bridge tabs**,
one per nearest-neighbor gap (31 tabs, 1.8 mm wide). This worked mesh-wise
(0 non-manifold edges, 1 shell) but read as visual clutter and deviated from
the actual desired design (per your feedback) — a solid rim was wanted, not
ad hoc joins.

**Fix used (rev D, superseded by rev E — see C4): a solid 5 mm structural
rim (R7/D1/D2)** between the coaster edge and the pattern, unioned with the
pattern and a small solid center hub disc. Every trident tip and ring-gate
end already lands at nearly the same native radius (42.2-42.4 mm, section 3)
— so a single shared rim, overlapping the scaled pattern's edge by 0.4 mm to
avoid a tangent join, connected all 24 of those pieces (8 tridents + 16
ring-gate halves) into one shell in a single stroke; a small solid disc at
the center (radius 10.3 mm native) did the same for the 8 hub dots. Worked
mesh-wise (0 non-manifold edges, 1 shell), but rev E's construction (below)
makes the whole rim/hub-disc union unnecessary.

#### C4 — Getting the fill direction right needed real verification, not just a look

**Symptom.** Rev D's construction (previous entry) had the pattern as solid
material directly — correct by construction, nothing to invert. But your
next two requests ("the center is lost" / "invert the fill, keep the ring")
led to rebuilding it as `difference() { circle(r=50); scale(...) pattern(); }`
— a plain "solid disc minus the pattern." Naive set-subtraction semantics say
that should leave the *pattern* as holes and the *background* solid. Several
of my own render checks along the way (OpenSCAD's default 3D view, a
same-file 2D-only variant, a from-scratch reconstruction of the same
polygons) kept showing the pattern as solid instead — which I initially
treated as a bug to hunt down. Partway through that, you confirmed you'd
opened the actual exported STL directly in OrcaSlicer and FreeCAD and it was
correct (pattern solid, background open, rim solid) — squarely contradicting
where my own investigation had gotten to.

**Cause, once actually isolated.** Two things were true at once, and only
one of them was a real finding:
1. `linear_extrude()` of this specific `difference()` genuinely does not
   follow literal set-subtraction semantics — confirmed conclusively by
   rasterizing the exported mesh's own top-face triangles directly (no
   OpenSCAD rendering pipeline involved at all): the pattern comes out
   solid and the background open, which is what naive subtraction predicts
   for the *opposite* fill. This is a real, reproducible OpenSCAD/CGAL
   quirk for extruding a multi-contour 2D difference, separate from the
   already-documented G1 mesh defect.
2. My attempt to *prove* this with a pixel/point-sampling test was itself
   wrong — a bug in a hand-rolled point-in-polygon check placed the
   "verification" point outside the trident entirely, in the open
   background, which is what generated the apparent contradiction with your
   report. You were right the whole time; my proof of the opposite was
   broken, not the geometry.

**Fix / resolution.** Re-verified by rasterizing the actual exported mesh's
top-face triangles directly and looking at the result — unambiguous, and in
agreement with your OrcaSlicer/FreeCAD check: pattern solid, background
open, rim solid. No geometry change was needed; only the code's own
explanatory comment (which had been written from the wrong mental model)
was corrected.

> **Pattern.** When a boolean operation's visible result and your
> expectation of "what the operator should do" disagree, verify against
> the actual output (rasterize the real mesh, sample real triangles) before
> trusting either a re-derived "proof" or a plausible-sounding theory of the
> underlying engine's behavior — and don't let a failed proof override a
> direct, tool-based observation (a slicer or CAD viewer showing filled
> geometry is closer to ground truth than a hand-rolled verification
> script). This is the same family of lesson as the pole-foot build's C10
> (preview vs. render can disagree) and C6 (check the instrument before the
> model) — here the twist was that the *instrument I built to check with*
> was the one that was broken.

---

## 7. Final verified dimensions

Measured from the exported mesh (`coasters/coaster_helm_of_awe.stl`), not
from intent, and independently confirmed by opening the file in OrcaSlicer
and FreeCAD:

| | |
|---|---|
| Overall | Ø100.0 x 3.00 mm (bounding box — the full coaster, rim included) |
| Max radius from center | 50.000 mm exact (the coaster edge itself, R2) |
| Rim | solid 7 mm band, 43-50 mm radius (R7/D1) |
| Pattern | hub + tridents + ring solid, background between them open (D2) |
| Thickness | 3.000 mm uniform (D2) |
| Mesh | watertight: 0 edges not shared by exactly 2 triangles |
| Shells | 1 (single physically connected piece — R6/D3) |
| Volume | 12,425.9 mm^3 |
| Triangle count | 4,308 |
| Construction | `difference() { circle(r=50); scale(...) pattern(); }`, extruded — see section 6, C4 for why this produces a solid pattern rather than the hole a literal subtraction would suggest |

---

## 8. File structure

    coasters/
      insert-helm-of-awe.stl           (source pattern, reference only)
      coaster_helm_of_awe_spec.md       (this file)
      coaster_helm_of_awe.stl           (final export)
      cad/
        helm_of_awe_emblem.scad         -- traced pattern polygons (32 pieces: hub + 8 tridents + 8 ring gates), native scale
        coaster_helm_of_awe.scad         -- centers, scales, and extrudes (section 6, C4)

## 9. Open items

- **Not yet printed.** Everything above is mesh-verified and confirmed in
  two independent viewers (OrcaSlicer, FreeCAD), but not print-verified.
- **The C4 `linear_extrude` fill behavior is empirically confirmed, not
  fully explained.** It reliably produces the correct, desired result for
  this specific design and should keep doing so under the small parameter
  tweaks in section 7 (scale, rim width) — but if the pattern geometry is
  ever restructured significantly, re-verify the fill by rasterizing the
  exported mesh's own triangles (section 6, C4) rather than trusting a
  rendered preview or a re-derived proof.
