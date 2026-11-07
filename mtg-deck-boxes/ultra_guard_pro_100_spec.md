# Design spec: Ultra Guard Pro 100+ deck box (SolveSpace rebuild)

Parts: `cad/build_ugp100.py` -> `ultra_guard_pro_100_bottom.slvs`,
`ultra_guard_pro_100_top.slvs` (and the `.stl` exports beside them)
Source: `orig/Ultra_Guard_Pro_100+_bottom-BLANK.stl`,
`orig/Ultra_Guard_Pro_100+_top-tight.stl`
Verification: `cad/check_ugp100.py`
Revision: rev A, 2026-11-07. First part in this repo built in SolveSpace
rather than OpenSCAD.
Status: **modelled and mesh-verified against the source STLs; not yet
printed.**

The brief was to rebuild two 13 000-triangle STLs as simplified parametric
SolveSpace models — not triangle for triangle, but close to the same body —
with the **interior cavity** and the **lip/groove mating dimensions** exact
and the cosmetic rounding free to change.

The thing that made this tractable is in section 3: the originals are a
clean 76 x 72 mm design that was then **non-uniformly scaled**, which is why
every number you measure off them is ugly and every number divided by the
scale factor is round. Section 6 is the build log, including the two
SolveSpace-specific traps that cost the most time — a skewed extrude that
generates correct geometry and then breaks the boolean kernel outright, and
a whole class of constraints being silently deleted because they carried a
request handle where an entity handle belongs.

---

## 1. Function summary

A two-part deck box for 100+ sleeved Magic cards. The two
halves are shells that meet along a **single plane slanted at 30 deg** (in
the unscaled design; 25.78 deg in the finished part) running low at the
front and high at the back. The bottom half carries a **lip** — the inner
1.8 mm of its wall, continuing 6 mm above the seam — and the top half
carries the matching **groove**. Cards stand on end in a 70.0 x 76.5 x
94.05 mm cavity.

Assembled: 78.234 x 86.062 x 102.05 mm exterior.

---

## 2. Requirements

| # | Requirement | Source |
|---|---|---|
| R1 | Interior cavity must match the original — it has to fit the cards | brief, "critical" |
| R2 | Wall and lip dimensions where the halves meet must match | brief, "critical" |
| R3 | Wall thickness within ~0.5 mm of the original | brief |
| R4 | Exterior edge radii are aesthetic, free to change | brief |
| R5 | Simplified structure, not a triangle-for-triangle trace | brief |
| R6 | Parametric and editable in SolveSpace, not a dumb solid | implied by "solvespace files" |
| R7 | Each rebuilt half should still mate with the original other half | reading of R2 |
| R8 | Watertight, single-shell, printable meshes | repo standard |

---

## 3. Source analysis: the originals are a scaled design

### 3.1 What the meshes are

Both source meshes are clean: watertight, consistently wound, one shell
each. 14 350 and 12 832 triangles. The bottom is named `-BLANK`, and it is:
the cavity is a plain rectangular prism with **sharp interior corners**, no
logo, no thumb notch, no card-retention features. Nothing had to be traced.

The two files share a coordinate frame to within 0.004 mm in x and y, so
they came out of one assembly — see 3.4 for the 0.027 mm in z that they do
not share.

### 3.2 The measurement that mattered

Every planar face was extracted by grouping triangles by normal and
least-squares fitting each group. The wall thicknesses came out as 4.1176
(x) and 4.7812 (y) — not round, and not equal, which is odd for a moulded
box. But:

    4.1176 / 4.0 = 1.0294        69.9992 / 68 = 1.0294        78.2344 / 76 = 1.0294
    4.7812 / 4.0 = 1.1953        76.4992 / 64 = 1.1953        86.0616 / 72 = 1.1953

Divide the whole part by `sx = 1.0294` in x and `sy = 1.1953` in y and a
clean design appears:

| In the unscaled design | |
|---|---|
| exterior | 76 x 72 mm, corner radius 2.0 |
| wall | 4.0, split 2.2 (outer, ends at the seam) + 1.8 (inner, becomes the lip) |
| interior | 68 x 64, sharp corners |
| floor, ceiling | 4.0 each |
| seam plane | **exactly 30 deg** |
| edge fillets | 0.5 |

And the scale factors are not arbitrary either: `70.0 / 68 = 1.029412` and
`76.5 / 64 = 1.1953125`. Somebody picked them to land the **interior** on
70.0 x 76.5 — the dimension that has to fit the cards — and rounded them to
five figures. So 69.9992 and 76.4992 are not the design intent, 70.0 and
76.5 are, and the 0.8 micron difference is rounding in the scale factor.

The 30 deg seam is the clincher: `tan(30) / 1.1953 = 0.4830171` against a
measured slope of `0.4830170`, fitted from 125 triangles.

The z axis is unscaled, which is why its numbers are already honest: floor
4.0, ceiling 4.0, interior height 94.05, assembled height 102.05.

### 3.3 The lip and the groove

The lip is the inner 1.8 mm of the wall carried 6.000 mm (vertically) above
the seam, with its top on a plane parallel to the seam. Its inner face is
flush with the interior wall, so the cavity stays 70.0 x 76.5 straight
through the lip. The groove in the top half mirrors it.

The lip-to-groove clearance is **different on the two axes** and is not a
round number on either: 0.01176 mm per side in x, 0.07813 mm in y. Dividing
by the scale factors does not reconcile them, and neither does any uniform
offset — so it is not recoverable as a design value, only as a measurement.
Both are far below what FDM resolves, and both were kept as measured so that
a rebuilt half still fits an original half (R7). If a single clean number is
wanted later, `CLEAR_X = CLEAR_Y = 0.05` is the obvious substitution.

This is presumably what `-tight` in the source filename refers to, and
implies a looser variant exists somewhere.

### 3.4 The 0.027 mm the originals disagree about

Aligned on their shared x/y frame, the original top's seam plane sits
**0.0271 mm lower in z** than the original bottom's — the two halves, as
exported, interfere by that much, at the seam and at the lip top
simultaneously. Meanwhile their floor and ceiling give a clean 4.0 + 94.05 +
4.0 = 102.05 assembled height.

So one of the two is off by 0.027 mm and the round numbers say which. The
rebuild puts both halves in one exact frame: assembled height exactly
102.05, seam faces coincident, lip top coincident with the groove roof. The
consequence is the only place the rebuild knowingly differs from a source
measurement, and `check_ugp100.py` prints it as expected rather than failing
on it.

Net effect on fit, since the rebuild is 0.027 mm "taller" at the seam than
the original top is:

| pairing | at the seam |
|---|---|
| rebuild + rebuild | touches exactly |
| rebuild bottom + original top | 0.027 mm interference — same as the original pair |
| original bottom + rebuild top | 0.027 mm clearance |

---

## 4. Decisions

**D1 — One shared frame, re-origined.** x and y centred on the box axis, z =
0 at the exterior underside of the bottom half. Both parts use it, so
bottom + top is the assembly. The originals' frame was arbitrary;
`check_ugp100.py` holds the transform back to it.

**D2 — Interior at exactly 70.0 x 76.5.** The model carries 69.9992 /
76.4992, i.e. `68 * sx` and `64 * sy`, because that reproduces the original
faces to the micron and section 3.2 explains where 70.0 went. Changing
`INT_HX`/`INT_HY` to exactly 35.0 / 38.25 is a one-line edit if the 0.8
micron ever matters, which it does not.

**D3 — Horizontal perimeter rounds dropped.** The original rounds its
bottom and top perimeters with r2.0. SolveSpace 3.3 has **no 3D fillet and
no sweep**, and a round that runs around a rounded-rectangle perimeter needs
one of them. Under R4 and R5 these are dropped and those edges are sharp.
For the bottom half this is arguably an improvement: a 2 mm round on the
underside perimeter is a bad first layer, and a flat one is not.

**D4 — Vertical corners get one circular radius.** The original's exterior
corner is an **ellipse** — r2.0 scaled non-uniformly, so 2.0588 x 2.3906 —
which no sketch arc can be. The rebuild uses r2.2, which differs from the
original surface by at most 0.19 mm (at the y-aligned end of each corner,
where the original's semi-axis is 2.3906; 0.14 mm at the x-aligned end).
Aesthetic only (R4). The lip's outer corners likewise go from 0.5147 x
0.5976 to r0.55.

**D5 — 0.5 edge fillets dropped.** The original fillets the seam's outer
edge, the lip's top edges and the groove's mouth with r0.5, and chamfers the
groove mouth 0.4 x 0.4. All are omitted. None is a fit surface — verified:
the original's groove roof meets its groove wall at a **sharp** corner, so
the rebuild's sharp lip-top corner has somewhere to go. The one thing lost
is assembly feel: the 0.4 chamfer at the groove mouth is a lead-in, and
without it the halves need to be squarer to each other going together. Easy
to add later as a sketch chamfer on the groove profile.

**D6 — The top's groove-roof-to-wall fillet dropped.** The original blends
its groove roof up to the interior wall with roughly r2.2. The rebuild has a
sharp step. Structural, not dimensional; it is the obvious thing to add if a
print cracks there.

**D7 — Groove corners sharp.** The original *relieves* its groove corners —
cuts them back past where the two flats meet. The rebuild leaves them sharp,
which still clears the lip's r0.55 corners with room, and is what lets the
groove cutter be a rectangle (see D8).

**D8 — Build order chosen so no cut is skewed.** See 6.1. In short: the
groove is cut by a profile drawn on an x-normal plane with the slant as a
*line*, extruded along that plane's own normal — not by a profile on the
slanted plane pushed vertically, which is the obvious move and does not
work.

---

## 5. Verified dimensions

From `cad/check_ugp100.py`, which exports both `.slvs` through
`solvespace-cli` and measures the resulting meshes.

### Critical (R1)

| | design intent | model | measured |
|---|---|---|---|
| interior x | 70.0 | 69.9992 | 69.99920 |
| interior y | 76.5 | 76.4992 | 76.49920 |
| interior z | 94.05 | 94.0500 | 94.05000 |

### Every significant face, rebuild vs original

All 31 planar faces present in both — exterior, interior, lip faces, groove
faces, floor, ceiling, seam plane, lip-top plane — agree to **within 0.00001
mm**, with the single documented exception of the top half's floor and
ceiling, which carry the 0.0271 mm of section 3.4.

### Wall thickness (R3)

| | original | rebuild | delta |
|---|---|---|---|
| x walls | 4.1176 | 4.1176 | 0 |
| y walls | 4.7812 | 4.7812 | 0 |
| lip, x | 1.8529 | 1.8529 | 0 |
| lip, y | 2.1515 | 2.1515 | 0 |
| floor / ceiling | 4.0 | 4.0 | 0 |

Comfortably inside R3; the walls were reproduced exactly rather than
approximated.

### Constraint health (R6)

Every group in both files: **0 degrees of freedom, 0 redundant equations**,
residual at machine precision. Checked by `dof_report()` rather than by
SolveSpace, for the reason in 6.7.

| | groups | largest group |
|---|---|---|
| bottom | 6 | `outer-profile`, 40 unknowns / 40 equations / rank 40 |
| top | 5 | `outer-profile`, 40 / 40 / rank 40 |

### Mesh health (R8)

| | triangles | shells | watertight | volume |
|---|---|---|---|---|
| bottom, original | 14 350 | 1 | yes | 90 637.6 mm^3 |
| bottom, rebuild | 260 | 1 | yes | 91 019.7 mm^3 (+0.42%) |
| top, original | 12 832 | 1 | yes | 91 094.8 mm^3 |
| top, rebuild | 188 | 1 | yes | 91 937.7 mm^3 (+0.93%) |

The rebuilds are slightly heavier because every omitted feature (D3, D5, D6)
*removes* material in the original. 55x and 68x fewer triangles.

### Assembly

All four bottom/top pairings — both rebuilds, and each rebuilt half against
the original other half — were tested for interference along 148 vertical
rays through the wall band and the four corners. All clear, with the mating
faces touching.

---

## 6. Build log

### 6.1 A skewed extrude generates the right solid and then breaks the boolean

The groove in the top half is a pocket with **vertical walls** and a **roof
on the slanted lip-top plane**. A SolveSpace extrude's end caps are always
parallel to its sketch plane, so the roof has to come from sketching on a
seam-parallel plane — and the walls have to come from extruding *vertically*
rather than along that plane's normal.

That works. SolveSpace's extrude vector is a free 3-vector (the `ONE_SIDED`
vs `ONE_SKEWED` subtype only matters when `predef.entityB` pins it to a
workplane normal, which a generated file need not do), so the resulting
solid is exactly right: four axis-aligned vertical faces, a slanted cap.
Verified by eye in the entity geometry.

Then the boolean fails. Not subtly — `failed: I=15, avoid=2`, `trim was
empty`, `trim was unterminated`, `failed to assemble polygon to trim nurbs
surface in uv space`, and a self-intersecting 3-shell mesh out the other
end. Reduced to a minimum case (a 40 x 40 x 40 block, one tilted cutting
plane, one 20 x 20 square):

| cutter | result |
|---|---|
| sketch on tilted plane, extruded along its normal | clean |
| sketch on tilted plane, extruded vertically | self-intersecting mesh |
| same, with subtype `ONE_SKEWED` instead of `ONE_SIDED` | self-intersecting mesh |

**So: never extrude a sketch along anything but its own plane normal if the
result has to take part in a boolean.** The subtype does not rescue it.

The fix is to rotate the problem. Sketch the slant as a *line in the
profile* instead of as the sketch plane: put the cutter's profile on an
x-normal plane, where sketch `u, v` read straight off as world `y, z`, draw
a trapezoid whose top edge is the roof line, and extrude along that plane's
own normal (+x). Every face lands where it needs to — `x = +-GROOVE_HX` from
the extrude, `y = +-GROOVE_HY` and the slanted roof from the profile — and
the boolean is clean. That is `groove_cutter()`.

### 6.2 A request handle is not an entity handle, and the failure is silent

Every constraint that referenced a *line* rather than a *point* was being
thrown away on load. `HORIZONTAL`, `VERTICAL`, `ARC_LINE_TANGENT`,
`EQUAL_RADIUS`, `DIAMETER` — 20 constraints in, 8 out, and the only hint was
one dialog string about dependent elements being deleted.

Cause: the writer returned the **request** handle `r` as a line's identity,
where SolveSpace wants the request's **entity** handle `(r << 16) | 0`.
Points happened to work because they were being built correctly as
`(r << 16) | 1` and `| 2`, so coincidence constraints survived and the
geometry looked fine.

Two things make this expensive to notice:

* `Sketch::EntityExists()` treats handle 0 as "acceptable, just means it
  doesn't apply", and a pruned constraint is only *reported* if it is
  non-trivial — `POINTS_COINCIDENT`, `HORIZONTAL` and `VERTICAL` are
  explicitly excluded from the count. So a file can lose all its horizontal
  and vertical constraints and say nothing at all.
* The exported mesh is unaffected, because the seeded `Param` values already
  hold the right coordinates. The model is wrong in exactly the way an
  exported mesh cannot show.

**Check for this by regenerating and counting**: `solvespace-cli regenerate`
rewrites the file, so `grep -c AddConstraint` before and after must match.
That catches a *deleted* constraint. It does not catch a constraint that
survives and is wrong — see 6.7, which is the same lesson a second time.

### 6.3 `SYMMETRIC_HORIZ` is symmetry about the vertical axis

From `constrainteq.cpp`: `SYMMETRIC_HORIZ` emits `av - bv = 0` and
`au + bu = 0` — same v, opposite u. That is the constraint for a
**horizontal** edge's two ends, i.e. symmetry about the v axis.
`SYMMETRIC_VERT` is the mirror of that.

Applied the other way round, it forces `au = bu` *and* `au + bu = 0` on a
vertical edge, so `u = 0`, so the rectangle collapses and the group exports
an empty mesh. Which is at least loud.

Also: symmetry on an edge implies that edge is horizontal (or vertical), so
it **replaces** `HORIZONTAL` on that edge rather than joining it — the GUI
deletes the redundant one for you (`constraint.cpp`,
`DeleteAllConstraintsFor`), and a generated file has to not add it.

### 6.4 A cutter sized by the footprint is not big enough

The cut that opens each half along the seam is an oversized rectangle on a
seam-parallel plane. Sized by the exterior footprint plus a margin, it very
nearly works — and the bottom half did work, by luck.

The sketch's v axis is tilted, so a point of the part maps to
`v = cos(th) * y + sin(th) * (z - z0)`. Over the bottom half's full z range
the second term is worth 23.5 mm against the footprint's 38.7 mm. A cutter
sized `EXT_HY + OVER` needs 62.25 and had 61.1 — undersized, and only
saved because the corner that needed it was below the seam anyway.
`seam_cover()` now sizes by both terms.

The same mistake in a more dangerous form: a cutter whose cap is
seam-parallel but whose depth is a vertical distance has a cap that climbs
0.483 mm per mm of +y. The top half's first groove cutter reached 12 mm below
the box axis (z = -12) and still came back up to **z = +7.6** at the back of
the box — inside a block that was solid down to z = 0. The cure is ordering:
open the seam first, and then every later cutter with a seam-parallel cap is
bounded by a surface it is parallel to.

### 6.5 What the `.slvs` format actually needs

Reading `src/file.cpp` saved a lot of guessing:

* **`AddEntity` records are not needed.** `ReadSketchFile()` discards them
  (`savedEntities` is `NULL` from `LoadFromFile`) and `GenerateAll()`
  rebuilds them from groups + requests. The generated files contain none.
* **`AddParam` records are needed**, but only as initial guesses — "params
  are regenerated, but we want to preload the values". Which means a
  generated file is only as good as its constraints, and a value that is
  merely seeded is a value the solver may move.
* **`Group.remap` can be empty.** The `'M'` loader reads lines until one
  fails to parse as `%d %x %d`, so `{\n}` is a valid empty table, and
  SolveSpace reassigns the mapping on regeneration.
* The param key in the save table is `Param.h.v.` — **with a trailing dot**.
* Zero-valued fields are omitted on save and default to zero on load, except
  `Group.scale`, which defaults to 1 after each `AddGroup`.

### 6.6 Checking that the constraints, not the coordinates, hold the shape

Because of 6.5, "it exports the right mesh" proves nothing about the
constraints. The test that does: jitter every request param by a random
amount and see whether the solver puts the geometry back.

| jitter | bottom | top |
|---|---|---|
| +-0.3 mm | exact recovery, 3/3 seeds | exact recovery, 3/3 |
| +-1.0 mm | 1/3 exact | 3/3 exact |
| +-3.0 mm | 1/3 exact | 2/3 exact |

The failures at 1-3 mm are a corner arc flipping to the other side of its
tangent lines: the drifts are 4.40 and 4.73 mm, both on the order of the
4.4 mm corner diameter. That is the ordinary multiple-solution behaviour of
a tangent-constrained rounded rectangle under a perturbation larger than the
radius, not a missing constraint. The +-0.3 mm row is the meaningful one.

Extrude-group params are deliberately excluded — see 7.3.

### 6.7 A file that exports perfectly and still will not open cleanly

Shipped rev A. Opened in the GUI: **unsolvable constraints**, naming
`c039-pts-coincident`, `c03a-pts-coincident`, `c03d-symmetric-h` and
`c042-angle`. Those four handles are 57, 58, 61 and 66 of the top half's 66,
which is exactly the `groove-profile` group — the trapezoid of 6.1.

Nothing that had been run could see it:

* `solvespace-cli export-mesh` produced a watertight single-shell mesh
* every face matched the originals to 0.00001 mm
* `regenerate` pruned nothing — 66 constraints in, 66 out
* the jitter test of 6.6 recovered the geometry exactly at +-0.3 mm

All of that is true *because the seeded `Param` values already sit at the
answer*. The solver starts there, has nothing to do, and reports success.
Only the GUI shows the rank deficiency, because only the GUI bothers to
tell you.

Two separate faults in one 16-equation group:

1. **Redundant, and short, at the same time.** The profile had
   `SYMMETRIC_HORIZ` on its bottom edge *and* `AT_MIDPOINT` putting the
   lip-top datum on its roof. With the two side edges vertical and the
   corners coincident, "centred in u" then follows twice over, so
   `AT_MIDPOINT`'s u-equation is implied — 16 equations of rank 15. The
   missing rank showed up as 1 remaining degree of freedom: nothing fixed
   the floor's height.
2. **The angle was asking for 180 - theta.** `ANGLE` constrains the
   *direction cosine* of the two line vectors. The roof runs right-to-left
   and the bottom edge left-to-right, so their dot product is `-cos(theta)`
   while the constraint wanted `+cos(theta)`. `other=True` negates the first
   vector and fixes it. Residual before the fix: 1.80, i.e. `2*cos(theta)` —
   the group was not at a solution at all, and nothing noticed.

The fix: bottom edge gets a plain `HORIZONTAL` (so `AT_MIDPOINT` does the
centring, once), the left edge gets a length dimension (so the floor has a
height), and the angle gets `other=True`. 16 equations, rank 16.

**What this needed was a check that does not go through SolveSpace at all.**
`slvs_write.dof_report()` rebuilds each group's equations from what the
writer emitted, takes a numeric Jacobian at the seeded solution, and
row-reduces it:

    redundant = equations - rank      (what the GUI will complain about)
    dof       = unknowns  - rank      (what is still free to drag)
    residual  = max |f(x)|            (whether the seed is even a solution)

Run on rev A it reproduced the GUI's verdict exactly — `groove-profile`:
16 unknowns, 16 equations, rank 15, 1 dof, 1 redundant, residual 1.8e+00 —
and found two more groups nobody had looked at (`seam-cut-plane` and
`lip-top-cut-plane`, 4 dof each; the oversized cutter rectangles had been
left with coincidence and horizontal/vertical only, on the grounds that
their size does not matter). Those are now dimensioned too. It is step 0 of
`check_ugp100.py`.

The generalisable form of this, which is the C4 lesson from
`pole-foot/pole_foot_spec.md` wearing a different hat: **a generated CAD
file has two independent things to get right — the geometry and the
constraints — and every check used here tested only the first.** An exported
mesh cannot distinguish a sketch held by its constraints from a sketch held
by nothing at all, because both export the same triangles.

---

## 7. Structure of the model

### 7.1 Files

| File | What it is |
|---|---|
| `cad/ugp100_params.py` | every dimension, with the base-design/scale derivation written down |
| `cad/build_ugp100.py` | emits both `.slvs` |
| `cad/check_ugp100.py` | the verification in section 5, including the degree-of-freedom check |
| `../utilities/slvs_write.py` | a reusable `.slvs` writer (groups, requests, params, constraints), plus `dof_report()` |

`build_ugp100.py` reproduces both `.slvs` byte for byte, so the generator
and not the `.slvs` is the source of truth for the dimensions. Editing a
`.slvs` in the SolveSpace GUI is fine and expected — just know that
re-running the build overwrites it.

### 7.2 Build sequence

**Bottom** (5 sketch + extrude pairs):

1. exterior rounded rectangle, extruded up past everything — UNION
2. cut away everything above the seam plane — DIFFERENCE
3. the lip's footprint back as a *solid* block, same vertical extent — UNION
4. cut away everything above the lip-top plane — DIFFERENCE
5. the card cavity, from the floor datum upward — DIFFERENCE
   (which is what turns step 3's block into a ring)

Doing the cavity *after* the lip block is what keeps every sketch a single
closed loop; the alternative is a two-loop ring sketch.

**Top** (4 pairs):

1. exterior rounded rectangle, sketched on the exterior top face and pushed
   down — UNION
2. open the bottom along the seam plane — DIFFERENCE
3. the card cavity, from the ceiling datum down and out — DIFFERENCE
4. the groove, via the x-normal trapezoid of 6.1 — DIFFERENCE

Both parts end on an operation whose sketch is about the size of the part,
not the size of a cutter, because the group a file opens on is the one whose
wireframe you see. Everything before it is marked not visible — the cutters
are sized to swallow the whole box and with them all shown the file opens as
a thicket of wireframe rather than as the part. Unhide them when editing.

### 7.3 What is held by a constraint and what is not

Fully constrained with editable dimensions: all six profile sketches
(exterior, cavity, lip, groove), and every datum point — each pinned by
three dimensions, one against each reference plane, so the floor, seam,
lip-top, ceiling and exterior-top heights are all real constraints.

Carried in extrude-group params instead:

* the cutter depths and block heights — all oversized, dimensionally
  meaningless
* **`GROOVE_HX`**, the groove's x half-width, which is a fit dimension. It
  is the one number in the model that lives in an extrude vector rather than
  a constraint. The groove cut is `TWO_SIDED` from the box axis specifically
  so that this reads as a single symmetric half-width rather than a start
  plane plus a length.

Constraining an extrude length properly means referencing the extrude's
remapped top-face entities, whose handles SolveSpace assigns during
regeneration. That needs a two-pass build (generate, regenerate, read back
`Group.remap`, add constraints) and was judged not worth it — the generator
is the parametric model.

---

## 8. Tuning

In `cad/ugp100_params.py`:

| To change | Edit |
|---|---|
| cavity size (fit a different sleeve/count) | `INT_HX`, `INT_HY`, `INT_H` via `H_TOTAL` |
| lip/groove fit looser | `CLEAR_X`, `CLEAR_Y` (0.05 each is the sane single value) |
| lip engagement | `LIP_H` (6.0) |
| seam angle | the `30.0` inside `SEAM_TAN`, and `Z_SEAM` for its height |
| exterior corner look | `EXT_CORNER_R` |
| wall thickness | the `2.2` / `1.8` split, keeping their sum at the wall |

Then `python3 cad/build_ugp100.py && python3 cad/check_ugp100.py`. Note
`check_ugp100.py` compares against the *original* STLs, so after a
deliberate dimension change its section 3 will report differences — that is
the point of it.

---

## 9. Open items

* **Not printed.** Everything here is mesh verification. The lip/groove
  clearance is 0.012-0.078 mm per side, which is below what FDM holds, so
  the real fit will be decided by print tolerance, not by this model. Expect
  to open `CLEAR_X`/`CLEAR_Y` up after the first print.
* The 0.4 mm groove-mouth chamfer (D5) is worth adding before printing if
  assembly feels tight — it is a lead-in, and it is a two-line sketch change
  rather than a 3D chamfer.
* The groove-roof fillet (D6) is the stress riser to watch.
* `-tight` in the source name implies a looser top exists. If it turns up,
  the only thing that should differ is `CLEAR_X`/`CLEAR_Y`.
* No print orientation or support study has been done for either half.
