# Utilities

Reusable, project-agnostic tooling extracted from work on parts elsewhere in
this repo (mainly `coasters/`, some from `pole-foot/`). Intended for AI
tools (and humans) doing future CAD work in this repo — read this before
re-deriving any of the following from scratch; several took real time and
one wrong turn to get right the first time.

All scripts are stdlib-only Python 3 except `mesh_rasterize.py`,
`raster.py`, `printability.py` and `pattern_trace.py`, which need Pillow
(`pip install Pillow`). Nothing here depends on anything outside
this folder except where noted; import by adding this directory to your
path, or just `cd` into it.

## Files

| File | What it's for |
|---|---|
| `stl_io.py` | Load an STL (ASCII or binary, auto-detected) into a plain list of triangles. Shared by everything below. |
| `mesh_check.py` | Manifold / winding / volume / bbox / shell-count check on any STL. The general-purpose sibling of `pole-foot/check_stl.py` (that one also has pole-foot-specific fit-probe cross-sections; this one is just the mesh-health part, meant to be reused as-is). |
| `mesh_slice.py` | Shared helpers (`flat_triangles_at_z`, `point_in_triangle`) for working with one flat Z-slice of a mesh — e.g. the top face of a `linear_extrude()`d part. Used by the next two. |
| `mesh_query.py` | **The "isSolid" test.** `is_solid_at(tris, x, y, z)` — is there material at this point? Read the module docstring before using this on anything high-stakes: an earlier version of this idea had a real bug that produced a confidently-wrong answer, and the docstring explains exactly what went wrong and why this version is checked against the *actual exported mesh* instead. |
| `mesh_rasterize.py` | Rasterize a flat Z-slice straight to a PNG by filling real mesh triangles — no OpenSCAD, no camera/projection math. The ground-truth visual check when a render, a preview, or your own math disagrees with what a part should look like. |
| `dxf_trace.py` | Extract exact 2D artwork (as ordered polygons) from a relief/engraving on an STL, including a *non-manifold* one that can't be booleaned directly. Pairs with `projection_trace_recipe.scad`. Its `trace_faces()` **repairs the self-touching components that `walk_polygon()` gives up on** -- the C2 failure mode this file used to tell you to drop or fake. |
| `edt.py` | Exact Euclidean distance transform on a 0/1 raster, plus `erode`/`dilate`/`opening` built on it. The measuring instrument under `printability.py`, and the way to enforce a minimum feature width instead of hoping for one. Read its header before editing it: the textbook version of this algorithm is subtly wrong in floating point and fails *large*, silently, while passing small unit tests. |
| `printability.py` | **Will this actually print?** Minimum material/hole widths, and an erosion ladder that answers the question `mesh_check.py` cannot: does the part stay in one piece when everything thinner than 2r is gone. Run it on any openwork part before calling it done. |
| `raster.py` | Binary masks over a mm grid: build from a mesh slice or from polygons, combine (`AND`/`OR`/`SUB`/`NOT`), label components, score `iou`, measure area, dump a PNG or a width heat-map. The substrate under the two files above. Uses PIL to *fill polygons* and nothing else — every boolean is explicit bytearray logic, because `ImageChops` on mode-`"1"` images does not mean what it looks like (see D8). |
| `mesh_orient.py` | Get a plate-like source mesh into the XY plane: find the thickness axis, find its flat faces (and spot blind pockets that are *not* through features), remap. Read its warning — this is where orientation bugs are born, and it cannot check your work. |
| `pattern_trace.py` | **The source-insert -> pattern-`.scad` pipeline**, with the two checks every coaster here has failed at least once: `sense_of()` (is a traced loop the artwork or the hole around it?) and `orientation_iou()` (which way up, and from which side?). Also `component_polygons()`, which hides the walk-or-repair decision, and `emit_scad()`. Worked example: `coasters/trace_tree_of_life.py`. |
| `projection_trace_recipe.scad` | The OpenSCAD half of `dxf_trace.py`'s recipe: flatten a relief to 2D and export to DXF. |

## When to reach for which

**"Is my exported STL actually one printable piece, watertight, the right
size?"** → `mesh_check.py`. Run this on every export before calling a part
done, not just when something looks wrong — a mesh can pass every topology
check and still be N disconnected shells or have a silently-vanished
feature (wrong volume). This is the same discipline as
`pole-foot/check_stl.py`; use whichever is more convenient, they check the
same things.

**"Is this specific point actually solid, or is it a hole?"** → `mesh_query.py`.
Don't reason about this from source polygon data, from a render, or from an
OpenSCAD preview — query the real exported mesh directly. See its docstring
for exactly why this distinction mattered once already.

**"I don't trust what a render/preview is showing me, or two of my own checks
disagree with each other"** → `mesh_rasterize.py`. Rasterize the real mesh
and look at it. This is the single most reliable check in this folder,
because it has the fewest steps between "the actual file" and "what you
see."

**"Is this openwork part actually printable, or will it come apart on the
bed?"** -> `printability.py`. This is a *different question* from
`mesh_check.py`'s shell count and it is the one that fails in real life.
CAD will happily join two lobes at a cusp of zero width and report one
watertight shell; a 0.4 mm nozzle will not. Run the erosion ladder. The
Tree of Life source is the worked example: 1 shell, watertight, perfect
bounding box -- and its entire rim detaches from the middle of the coaster
at 0.20 mm of erosion, which is exactly how it failed when it was printed
(`coasters/coaster_tree_of_life_spec.md` sections 3 and 7).

**"I need to reuse artwork/a relief from an existing STL, and it needs to be
recut, rescaled, or the source file has some defect that makes booleans
against it unreliable"** → `pattern_trace.py`, which drives `dxf_trace.py` +
`projection_trace_recipe.scad` and adds the verification. Start from
`coasters/trace_tree_of_life.py` and change the parameters; it is a complete
working example that regenerates a real pattern file, refuses to write it if
either check fails, and reproduces its coaster's STL byte for byte. The
specific mesh defect this was originally built to survive is in
`coasters/coaster_helm_of_awe_spec.md` sections 3 and 6 (C1, C2).

**Keep the extraction script.** The Helm of Awe and Yggdrasil pattern files
cannot be regenerated — their traces were done by hand, so the generated
`.scad` is now the only record of decisions nobody can re-derive. Write the
five-line driver and commit it.

**Do this first, every time you trace a source STL: find out whether the
artwork is raised material or cut clean through the plate.** A `projection()`
trace returns closed loops, and nothing in the loops themselves says which
side of each one is solid. Get it backwards and you will be handed the
artwork's *negative space* while believing you have the artwork, and every
downstream boolean will be inverted — which is exactly what happened once
here, and cost a build a phantom "OpenSCAD quirk" plus a pile of unnecessary
connectivity scaffolding (`coasters/coaster_yggdrasil_spec.md` section 6,
F1). Two cheap checks, both against the source mesh:

    # 1. look at it: is the artwork solid, or is it a hole?
    rasterize_z_slice(source_tris, z=<a flat face>).save("src.png")

    # 2. ask the mesh what a traced polygon actually is
    is_solid_at(source_tris, *centroid_of(polygon), z=<that face>)

If (2) comes back False, the polygon is background: subtract it from a disc
rather than extruding it. `pattern_trace.sense_of()` does exactly this over
a whole trace — but note it uses `interior_point()`, **not** the area
centroid. The centroid of a long curved ribbon, which is what knotwork
traces into, routinely falls outside the ribbon: on the Tree of Life's 62
polygons a centroid-based test returned 28/62, an even split that reads as
"this trace mixes both senses" and is really just the probe missing the
shape. The interior-point version returns 0/62. Expect near-unanimity from
this check and treat anything else as a stop, not a majority vote.

**And check the orientation in the same breath** —
`pattern_trace.orientation_iou()`. It is a separate failure and a sneakier
one, because no derived quantity detects it: area, radii, component counts
and width distributions are all identical under a mirror and all agree with
each other while the part is upside down.

## Background: the mistakes these encode

Two build logs are worth reading in full before doing similar work, not just
skimming this table:

- **`pole-foot/pole_foot_spec.md` section 6** — ten defects across a single
  parametric part: chamfers-as-subtracted-cones, tangent cutters, epsilon
  placement, boolean ordering, preview-vs-render mismatches. Several of
  those patterns generalize to any OpenSCAD part, not just pole-foot.
- **`coasters/coaster_helm_of_awe_spec.md` section 6** — a non-manifold
  source mesh causing a boolean crop to leak (C1), a self-touching vertex
  breaking a polygon trace (C2), 32 traced pieces that don't touch each
  other needing a deliberate connectivity fix (C3), and — the most
  expensive one — a wrong "proof" from a buggy verification script directly
  contradicting a correct direct observation, costing real time before the
  bug was found in the checker, not the part (C4). `mesh_query.py` and
  `mesh_rasterize.py` exist specifically because of C4. **Read C4 with its
  correction header:** its headline conclusion (that `linear_extrude()`
  violates set-subtraction semantics) was later retracted, and C3's
  "pieces that don't touch" turned out to be a symptom of the same root
  cause — see the next entry.

- **`coasters/coaster_yggdrasil_spec.md` section 6 (F1)** — the retraction,
  and the cheapest lesson in this folder: the traced polygons had been the
  artwork's *negative space* the whole time, because the source insert was a
  through-cut plate rather than a raised relief. Nobody asked the source
  mesh what its own polygons meant. One `is_solid_at()` call would have
  settled it.

- **`coasters/coaster_tree_of_life_spec.md` section 6** -- the first source
  in this repo whose artwork could not be reproduced faithfully at all: its
  line weight is roughly 2x too fine for FDM at 100 mm, so the border had to
  be recomposed rather than repaired (D1, D2). Also the third distinct
  orientation bug in three coasters (D6): `projection()` after
  `rotate([90,0,0])` lands vertically mirrored, which stood the tree on its
  head through several rounds of measurement because every *number* was
  right. And two cases of a checker being wrong rather than the part (D7,
  D8) -- one of them the distance transform itself, which reported a 112 mm
  inscribed width inside a 100 mm disc.

The short version of the C4 lesson, since it's the one most likely to repeat
if not internalized: **when your own derived reasoning (math, a re-run
script, a theory about how a tool works) disagrees with a direct
observation (a slicer/CAD viewer showing the actual file), suspect your
reasoning first.** Verify against the real, final artifact — not a mental
model of what it should be.

And the F1 corollary, which is what actually closed C4 out: **verify the
inputs the same way you verify the output.** C4's discipline was applied
faithfully to the exported STL and never once to the source STL, so a
mislabeled input survived every check and got blamed on the tool. When a
tool appears to violate its own documented semantics, look at what you
handed it before concluding the tool is wrong.
