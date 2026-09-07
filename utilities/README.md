# Utilities

Reusable, project-agnostic tooling extracted from work on parts elsewhere in
this repo (mainly `coasters/`, some from `pole-foot/`). Intended for AI
tools (and humans) doing future CAD work in this repo — read this before
re-deriving any of the following from scratch; several took real time and
one wrong turn to get right the first time.

All scripts are stdlib-only Python 3 except `mesh_rasterize.py`, which needs
Pillow (`pip install Pillow`). Nothing here depends on anything outside
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
| `dxf_trace.py` | Extract exact 2D artwork (as ordered polygons) from a relief/engraving on an STL, including a *non-manifold* one that can't be booleaned directly. Pairs with `projection_trace_recipe.scad`. |
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

**"I need to reuse artwork/a relief from an existing STL, and it needs to be
recut, rescaled, or the source file has some defect that makes booleans
against it unreliable"** → `dxf_trace.py` + `projection_trace_recipe.scad`.
Full worked example, including the specific defect this was built to work
around, in `coasters/coaster_helm_of_awe_spec.md` sections 3 and 6 (C1, C2).

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
  `mesh_rasterize.py` exist specifically because of C4.

The short version of the C4 lesson, since it's the one most likely to repeat
if not internalized: **when your own derived reasoning (math, a re-run
script, a theory about how a tool works) disagrees with a direct
observation (a slicer/CAD viewer showing the actual file), suspect your
reasoning first.** Verify against the real, final artifact — not a mental
model of what it should be.
