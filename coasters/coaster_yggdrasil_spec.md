# Design spec: Yggdrasil coaster

Part: `cad/coaster_yggdrasil.scad` -> `coaster_yggdrasil.stl`
Source pattern: `insert-yggdrasil.stl`
Revision: rev A, 2026-09-08. Built to the same brief as the Helm of Awe
coaster (100 mm diameter, 3 mm thick, 7 mm rim) and shares its tooling, but
none of its defects — see section 6.
Status: **designed and mesh-verified; not yet printed.**

---

## 1. Function summary

A circular coaster, 100 mm diameter x 3 mm thick: the Yggdrasil tree —
trunk, canopy branches and roots — is the solid material, matching the
source artwork's own sense, with the background between the limbs open and
a solid 7 mm rim at the edge holding it together. The design is redrawn from
the exact traced outline of `insert-yggdrasil.stl` (a square insert built
for another project), centered, rescaled to meet the rim, and extruded the
full 3 mm.

## 2. Requirements

| # | Requirement | Value |
|---|---|---|
| R1 | Coaster shape | circular |
| R2 | Coaster diameter | 100 mm |
| R3 | Coaster thickness | 3 mm, tree solid, background between limbs open |
| R4 | Pattern source | `insert-yggdrasil.stl` (Yggdrasil / world tree) |
| R5 | Pattern placement | centered in the coaster |
| R6 | Construction | single piece, no swap-in insert |
| R7 | Outer rim | solid 7 mm band between the coaster edge and the pattern |

Matches the Helm of Awe coaster's final rev G parameters exactly, so the two
are a set.

---

## 3. Source pattern analysis

`insert-yggdrasil.stl` is a 107.2 x 107.2 x 2.5 mm square plate with the
Yggdrasil design **cut clean through it** — not a raised relief. Verified
directly by rasterizing the plate's own face triangles (`mesh_rasterize.py`,
after rotating the part so its face plane becomes XY): the tree is material,
the background around its limbs is empty.

The source mesh is clean — manifold (every edge shared by exactly 2 faces),
consistent winding, 1 shell, 4,416 triangles. **None of the Helm of Awe
source's defects are present here** (see that spec's C1 and C2), so the
trace was a single clean pass.

The 2D outline was extracted with `projection(cut=false)` and decomposed
into connected components (`dxf_trace.py`), giving 23 pieces:

| Piece | What it is | Radius from center | Kept? |
|---|---|---|---|
| **22 background regions** | the open areas between the tree's limbs. The tree's branches and roots divide the design circle's background into 22 separate regions, each one open to the circle's edge — every one has part of its boundary on r = 48.0836 | 2.9–48.08 (nearest point varies; all reach 48.08) | **kept** (as the subtrahend — see below) |
| **Square border** | the plain 107.2 mm outline of the plate itself | 75.80 | excluded |

All 22 walked into clean simple closed loops on the first attempt (835
points total); `is_clean_walk` passed for every one.

### The important structural point: the trace is the *negative* space

The traced polygons are the **background**, not the tree. Because the source
is a through-cut plate, the tree is *whatever is left* of the design circle
once those 22 regions are removed. The build therefore subtracts them from a
disc rather than extruding them (section 5, D2). The file is named
`yggdrasil_pattern.scad` with a module called
`yggdrasil_background_native()` to keep this unambiguous — a caller that
unioned it instead would render the design inside out.

This is also true of the Helm of Awe trace, which was *not* understood at
the time and cost that build real effort — see section 6.

---

## 4. Assumptions

| # | Assumption | Status |
|---|---|---|
| A1 | The square plate border is insert-specific and excluded | Applied, same logic as the Helm of Awe coaster's A1. It is the only non-design component in this file (no corner brackets or edge ticks here). |
| A2 | Coaster depth is 3 mm, no separate base layer — the pattern is the full thickness | Applied, matching the Helm of Awe coaster's A2. The source's own 2.5 mm plate thickness is not reused; Z is a free parameter once the artwork is redrawn. |
| A3 | "Centered" means the design circle's own center | Applied. The design's circle is at r = 48.0836 and all 22 components share it, so the center is unambiguous. |

---

## 5. Decisions

**D1 — Edge margin: 7 mm, built as a solid rim.** The pattern is scaled so
its outer circle lands at 43 mm from center; the band from 43 to 50 mm is
solid, forming the structural rim. Scale factor = 43 / 48.0836 = 0.89428.

**D2 — Tree solid, background open, solid rim (a literal subtraction).**

    difference() { circle(r = 50); scale(0.89428) yggdrasil_background_native(); }

extruded 3 mm. Since the trace is the negative space (section 3), this is an
ordinary set subtraction that means what it says.

**D3 — Connectivity comes free; no scaffolding needed.** Every one of the 22
background regions is bounded on the outside by the design's own circle, so
subtracting them from the *larger* 50 mm disc leaves the full 43–50 mm band
solid, already fused to every branch and root tip that reaches it. The
result is one connected piece by construction — **verified: 1 shell.** This
is where the Helm of Awe build spent its C3 effort (32 loose pieces needing
bridge tabs, then a rim + hub disc); nothing equivalent was needed here,
because that build was unioning negative-space polygons that genuinely do
not touch each other, rather than subtracting them.

**D4 — Rim inner edge left as the trace's own chords.** The background
regions' outer boundaries are polygonal approximations of the circle (101
chords, median 2.80 mm, max 3.01 mm native). Worst-case sagitta is 0.0236 mm
native = **0.021 mm at coaster scale** — an order of magnitude below layer
and extrusion resolution, so the rim reads as a true 7.00 mm circular band.
An explicit `intersection()` against a clean `circle(r=43)` was considered
and rejected as unnecessary complexity.

**D5 — Single piece, no insert.** Same as the Helm of Awe coaster.

---

## 6. Build log

This build produced no defects of its own. The one finding worth recording
is about the *previous* build.

#### F1 — The Helm of Awe spec's C4 "OpenSCAD quirk" does not exist

**What that spec claims.** Helm of Awe C4 concluded that
`linear_extrude()` of a multi-contour 2D `difference()` "genuinely does not
follow literal set-subtraction semantics" — that `difference() { circle();
pattern(); }` empirically leaves the *pattern* solid rather than cutting it
out — and flagged it as a real, reproducible OpenSCAD/CGAL behavior to
re-verify if the geometry was ever restructured.

**What is actually true.** The polygons in `helm_of_awe_pattern.scad` are the
emblem's **negative space**, not the emblem. They were traced from a source
insert that is a through-cut plate (the same construction as this one), and
were mislabeled as the emblem itself. `difference()` behaved exactly as
documented the whole time: subtracting the background from a disc leaves the
emblem, which is precisely what the exported STL, OrcaSlicer, FreeCAD and
the rasterizer all showed.

**How it was settled here.** Both halves were checked against real meshes,
not reasoning:

1. Rasterized `insert-helm-of-awe.stl`'s own face triangles — it is a
   through-cut plate, emblem solid, background open.
2. Took the area centroid of each of the 32 polygons in
   `helm_of_awe_pattern.scad` and asked `mesh_query.is_solid_at()` whether
   the source mesh has material there. **0 of 32 sit on material; 32 of 32
   sit in the cut-out background.**

That also retroactively explains C3: those 32 "pieces" do not touch each
other because background regions separated by the emblem's lines never
could. The bridge tabs and the rim+hub scaffolding were solving a problem
created by the mislabeling.

**Consequences.** The Helm of Awe part itself is fine — correct geometry,
correctly verified, nothing to reprint. What was wrong was the explanation,
and it had leaked into `utilities/README.md` and `utilities/mesh_slice.py`
as a standing warning not to trust `linear_extrude` of a 2D difference.
Correction notes have been added in all three places rather than editing the
original build log, so the record of what was believed at the time survives.

The trace file was also renamed to say what it holds:
`cad/helm_of_awe_emblem.scad` -> `cad/helm_of_awe_pattern.scad`, module
`helm_of_awe_emblem_native()` -> `helm_of_awe_background_native()`, matching
this build's naming. Rebuilding the Helm of Awe coaster after the rename
produced a **byte-identical STL** (md5 47d776a4cd26c0c7a9eb6e652151c0a5),
confirming the change was nomenclature only.

Note what the correction does *not* touch: C1 and C2 stand. The Helm of Awe
source mesh really is non-manifold (`mesh_check.py`: 1 edge not shared by
exactly 2 faces, 2 mismatched directed edges), so the boolean-crop leak and
the self-touching vertex were real defects with a real cause. Only C3 and C4
— the two that depended on believing the polygons were the emblem — are
withdrawn. The Yggdrasil source, by contrast, is clean.

> **Pattern.** C4's own stated lesson — verify against the real artifact
> rather than a theory of the tool — was right, and was correctly applied to
> the *output* (the exported STL). It was never applied to the *input*: no
> one asked the source mesh what its own polygons meant. When a tool appears
> to violate its documented semantics, check what you actually handed it
> before concluding the tool is at fault. A one-line
> `is_solid_at(source_mesh, *centroid)` would have settled it immediately.

---

## 7. Final verified dimensions

Measured from the exported mesh (`coasters/coaster_yggdrasil.stl`), not from
intent:

| | |
|---|---|
| Overall | Ø100.0 x 3.00 mm (bounding box) |
| Rim | solid 7 mm band, 43–50 mm radius (R7/D1) |
| Pattern | tree solid, background between limbs open (D2) — confirmed by rasterizing the exported mesh's own top-face triangles |
| Thickness | 3.000 mm uniform |
| Mesh | watertight: 0 edges not shared by exactly 2 triangles; consistent winding |
| Shells | 1 (single physically connected piece — R6/D5) |
| Volume | 12,373.4 mm^3 |
| Triangle count | 4,224 |
| Solid area (top face) | 4,112 mm^2 of the 7,854 mm^2 disc (52%) |

### Printability

Measured on the exported mesh's top face by distance transform + erosion:
the whole pattern stays one connected piece when eroded by a 0.40 mm radius,
and only begins shedding slivers (0.33 mm^2 and smaller) at 0.50 mm.

**Narrowest structural connection: ~0.9–1.0 mm wide.** That is 2–3 perimeters
on a 0.4 mm nozzle, so it prints without needing a scale-up, but it is the
thinnest part of the design and the place to look first if a print fails.
The very tips of the finest roots taper below this, as artwork tips do; the
slicer will round them off.

---

## 8. File structure

    coasters/
      insert-yggdrasil.stl              (source pattern, reference only)
      coaster_yggdrasil_spec.md         (this file)
      coaster_yggdrasil.stl             (final export)
      cad/
        yggdrasil_pattern.scad          -- 22 traced background polygons, native scale
        coaster_yggdrasil.scad          -- centers, scales, subtracts, extrudes

## 9. Open items

- **Not yet printed.** Mesh-verified only, same status as the Helm of Awe
  coaster.
- The ~1 mm minimum feature width (section 7) is untested in a real print.
