# Design spec: Ultra Guard Pro 100+ deck box (SolveSpace rebuild)

Parts: `cad/build_ugp100.py` -> `ultra_guard_pro_100_bottom.slvs`,
`ultra_guard_pro_100_top.slvs` (and the `.stl` exports beside them)
Source: `orig/Ultra_Guard_Pro_100+_bottom-BLANK.stl`,
`orig/Ultra_Guard_Pro_100+_top-tight.stl`
Verification: `cad/check_ugp100.py`
Revision: rev E, 2026-11-07. First part in this repo built in SolveSpace
rather than OpenSCAD. rev B added the lead-in bevel at the groove mouth (D5);
rev C the engraved label on the bottom's front face (D10); rev D relabelled it
from "MTG" to "Spock" and added `cad/relabel.py` and `README.md` (6.9); rev E
adds the four snap domes on the lip and their dimples in the top (D11), which
the original rebuild missed.
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
| R9 | Engraved text on the bottom's front face, in a centred 70 x 20 mm panel, ~3 mm deep, not through the wall | rev C request |
| R10 | Changing the label is a routine, low-risk operation with a documented procedure | rev D request |
| R11 | The lid snaps shut: four domes on the bottom's lip seat in dimples in the top's groove | rev E request |

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

**D5 — 0.5 edge fillets dropped, but the groove mouth is bevelled.** The
original fillets the seam's outer edge and the lip's top edges with r0.5;
those are omitted, and none of them is a fit surface — verified: the
original's groove roof meets its groove wall at a **sharp** corner, so the
rebuild's sharp lip-top corner has somewhere to go.

The original also relieves the groove's mouth, and that one is not cosmetic:
it is the lead-in that lets the top be dropped on roughly square rather than
lined up first. rev A omitted it and the halves had to be presented to each
other accurately. rev B puts back a single 45 degree chamfer at **0.6 x 0.6**
(`MOUTH_CHAMFER`) all round.

*Correction (rev E).* This section first described the original's relief as a
0.4 x 0.4 chamfer and mine as "a little more generous". That was only the top
of it. In section the original is a 0.4 chamfer on the wall followed by a round
of roughly 0.6 mm blending into the seam face, and the relief starts **1.46 mm
up the back wall, 1.02 up each side wall and 0.50 up the front**. So the
rebuild is about as generous as the original at the front and sides and
**materially smaller at the back wall**. The surfaces differ by at most 0.43 mm,
at the back wall only, and by under 0.25 mm elsewhere. It was found by the
audit in 6.10, which is also why it is not a miss: it is a lead-in, not a fit
surface, and the bevel as built was accepted. If the lid is hard to start at
the back, that is the place to enlarge it.

The cost of the bevel is paid twice over and both are affordable:

| | before | after |
|---|---|---|
| seam land, x | 2.253 mm | 1.653 |
| seam land, y | 2.551 mm | 2.011 |
| lip engagement at full width | 6.0 mm | 5.4 |

The bevel is on the top's groove rather than on the lip, which is where the
original puts it: it is the side that funnels, and it leaves the bottom's
lip — the more fragile of the two — at full section. Measured off the
exported mesh, the chamfer is 0.600 along the wall and 0.600 along the seam
face on all four sides, and the groove roof the lip bottoms against is
untouched (681.95 mm^2, exactly the un-chamfered prediction).

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

**D9 — The mouth bevel is two cutters, not one.** A chamfer is a prism of
constant triangular section swept along the edge it cuts, so it has to be
sketched in the plane *perpendicular to that edge* — and the groove's four
mouth edges do not share a direction. The two at y = +-GROOVE_HY run
straight along x; the two at x = +-GROOVE_HX follow the seam's slope. So:

| edge pair | sketch plane | extruded along |
|---|---|---|
| y walls | x = 0 (u reads as y, v as z - Z_SEAM) | x |
| x walls | normal (0, cos, sin) (u reads as x, v as depth below the seam) | that normal |

Each plane is extruded along its own normal, so neither is the skewed
extrude that D8/6.1 rules out, and each sketch holds both of its triangles
as two separate loops. Each cutter overshoots the corner by `MOUTH_CHAMFER`
in the other axis so the two bevels mitre instead of meeting at exactly
coincident faces, and each triangle is drawn `CHAMFER_OVER` back along both
legs — which leaves the hypotenuse on the same line while lifting the legs
off the groove wall and the seam face, for the same reason.

**D10 — The label.** A label is cut into the **front (-y) face** of the bottom,
in Bitstream Vera Sans, 3.000 mm deep, fitted to a 70 x 20 mm panel centred on
the face. The current label is **"Spock"** (rev D); rev C's was "MTG". The
procedure for changing it is `README.md`; this is why it is built the way it
is. Several of these were judgment calls on an ambiguous brief, and were
accepted when rev C was reviewed:

* **"Front" is the low wide face.** The bottom has two wide faces: 78.2 x
  27.25 mm at -y (where the seam is lowest) and 78.2 x up to 74.5 mm at +y. A
  70 x 20 panel is in the proportions of the first (3.5 : 1 against 2.9 : 1)
  and would look lost on the second, so -y. It is `P.PANEL_ZC` and the sign of
  `y_plane` if the other face is meant.
* **The text fills the panel; the panel itself is not cut.** "A 70 x 20
  centred panel" is the area the text is fitted into, not a recessed
  rectangle with raised letters. Text is made as large as the panel allows and
  is **fitted by its ink box**, never by cap height or advance width: round
  letters overshoot the cap height, and descenders and ascenders extend well
  past it. Which panel dimension binds depends on the string — see the table.
* **Cap height is rounded down to 0.01 mm**, so the dimension in the GUI is a
  clean number and the ink is never outside the panel.
* **Depth leaves 1.78 mm of wall** (the wall is 4.78 mm). `ugp100_params.py`
  asserts at least 1.2 mm — three 0.4 mm perimeters — so a deeper cut or a
  thinner wall fails the build instead of printing a translucent wall.
* **The font is the one SolveSpace bundles, not Verdana.** Verdana is not
  installed here and is not redistributable. A request naming a font the
  machine lacks does not fall back — SolveSpace draws a big X — so a system
  font would make the file fail on any machine without it. Bitstream Vera Sans
  (`BitstreamVeraSans-Roman-builtin.ttf`) is compiled in, so it resolves
  everywhere, and it is a close Verdana relative: wide, open, large x-height.
  A different font is one parameter, `TEXT_FONT`, but it should be one that
  is on every machine that will open the file.

What each label comes out as — the same machinery, very different results:

| | "MTG" (rev C) | "Spock" (rev D) |
|---|---|---|
| ink, in cap heights | 2.84 x 1.04 | 4.03 x 1.33 |
| binds on | height | height |
| cap height | 19.27 mm | 15.06 mm |
| ink on the face | 54.67 x 19.99 mm | 60.76 x 19.99 mm |
| stroke | ~2.6 mm | ~2.0 mm |
| margin to each side's corner tangent | 9.58 mm | 6.53 mm |
| volume removed | 1108.35 mm^3 | 849.75 mm^3 |
| triangles in the bottom's STL | 760 | 1984 |

"Spock" is the instructive one. Its ink is 1.33 cap-heights tall rather than
1.04 because the **p descends 0.29 cap-heights below the baseline** and the k
rises 0.04 above the capitals, and the whole ink box has to fit 20 mm. So the
capital S is 15 mm tall, not the 19 mm a descender-free label would get, and
the 70 mm width is not the limit (87% used). That is not a defect — it is what
fitting by ink means — but it is the thing most likely to surprise someone
renaming.

Measured off the exported mesh for either label: the pocket floor is one plane
at y = -40.0308 (3.0000 deep), the ink is centred on the panel to 0.0000 mm,
and the volume removed equals the floor area x depth, so the cutter touched
nothing but the label.

**D11 — The snap.** The halves are held shut by **four domes on the bottom's
lip, two on each x face (one toward the front, one toward the back), seating in
four matching dimples in the top's groove walls.** rev A-D left them out. The
lip is 0.012 mm inside the groove, so a dome 0.77 mm high is real interference
while the lid slides over it: the walls flex, and the dome clicks into the
dimple. Without them nothing but friction keeps the halves together.

The clue was there from the start: the lip's outer x faces measured 419 mm^2
against the ~477 a plain 6 mm lip would give, and I did not chase it.

| | dome (bottom) | dimple (top) |
|---|---|---|
| shape in the source | cap of a 1.5 mm sphere, then scaled | cap of a ~1.70 mm sphere, circular |
| size in the source | base 1.553 (y) x 1.299 (z), 0.772 high | mouth radius 1.433, 0.787 deep |
| as rebuilt | circular cap, base radius 1.299, 0.7721 high | **exact**: mouth radius 1.433, 0.7857 deep |
| sphere radius as rebuilt | 1.479 | 1.700 |
| volume | 2.29 mm^3 (source 2.72) | 2.79 mm^3 |

The base design's dome is a cap of a 1.5 mm sphere 0.75 high, whose base radius
is sqrt(1.5^2 - 0.75^2) = 1.299 — that is where the odd 1.299 comes from. The
non-uniform scale then stretches it to an ellipse, 1.553 x 1.299, 0.772 high.
Centres, in the rebuild frame, are the same on both faces: (y, z) =
(-31.7434, 35.2115) toward the front and (33.8296, 67.1883) toward the back.
The source's dimples are coaxial with its domes to within 0.031 mm, so one set
of four positions serves both.

**What is different from the original, and why it matters.** SolveSpace has no
non-uniform scale, so the dome cannot be the source's ellipse. It is a circular
cap that keeps the two dimensions governing the click: its **height**, and its
**base radius in z**, which sets the profile along the direction the lid slides
(vertical). The vertical detent is therefore unchanged. What is lost is the 0.25
mm of extra width in y each side.

That width turns out not to be incidental. Sectioning the source's dome and
dimple at matching depths (6.10) shows the dimple is **~0.1 mm narrower in y
than the dome from the rim down to near the tip** — 1.38 vs 1.50 at the base,
0.98 vs 1.08 mid-depth — so the source's own bottom presses into its own top's dimple flanks
by about 0.1 mm each side. That is almost certainly an oversight (the dome was
scaled with everything else; the dimple, made afterwards, was not), but it is a
squeeze the original has and this rebuild does not. The rebuilt dome seats with
the same **0.0254 mm** clearance as the source's apexes: (GROOVE_HX + DENT_DEPTH)
- (LIP_HX + BUMP_H), measured 0.0253. A rebuilt bottom still fits the original
top; the original bottom does not seat cleanly in a rebuilt top, exactly as it
does not in its own.

If the printed lid proves too loose, the dome can be widened in y without
changing its height or vertical profile (two overlapping caps offset +-0.25 mm
in y); not done, because it is a guess about a print that has not happened.

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

| | sketch groups | largest group |
|---|---|---|
| bottom | 11 | `outer-profile`, 40 unknowns / 40 equations / rank 40; `text-plane`, 8 / 8 / 8; each of the four dome profiles 14 / 14 / 14 |
| top | 11 | `outer-profile`, 40 / 40 / rank 40; each of the four dimple profiles 14 / 14 / 14 |

The extrude groups carry 3 unconstrained params each (their extrusion
vector) and the report lists them as such; see 7.3.

### Mesh health (R8)

| | triangles | shells | watertight | volume |
|---|---|---|---|---|
| bottom, original | 14 350 | 1 | yes | 90 637.6 mm^3 |
| bottom, rebuild ("Spock", with domes) | 3 434 | 1 | yes | 90 178.9 mm^3 (-0.51%) |
| top, original | 12 832 | 1 | yes | 91 094.8 mm^3 |
| top, rebuild (with dimples) | 1 732 | 1 | yes | 91 866.0 mm^3 (+0.85%) |

Without the label the bottom is 91 028.7 mm^3 (+0.43%): the rebuilds are
slightly heavier because every omitted feature (D3, D5, D6) *removes* material
in the original. The label takes 849.8 mm^3 ("Spock"; "MTG" took 1108.4); the
four domes add 9.0 mm^3 to the bottom and the four dimples take 10.9 from the
top, against 4 x 2.29 and 4 x 2.79 for the ideal caps (the difference is
tessellation). Triangle counts are high now because the text and the spheres
are tessellated finely, not because the model is more complex.

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

### 6.8 Text: the format is two free points, and everything else is measured

Adding the label needed three things that are not obvious from the file
format, and one that is a SolveSpace behaviour to design around.

**A text request has two free points, not four.** `point[0]` is the
**top-left** and `point[1]` the **bottom-left** of the first glyph, so their
separation *is* the cap height; the text runs along `(v x normal)` and is
`aspectRatio` cap-heights long. Points 2 and 3 (the right-hand corners) look
like free sketch points but are not: `EntityBase::GenerateEquations` pins them
to the first two with four equations. So the group has 8 unknowns and 4
equations of its own, and wants four constraints of yours — which is
bottom-left x, bottom-left z, "directly above", and the height. `dof_report()`
now models those four (rank 8 of 8). A text with only a position and no height
looks plausible and is quietly 2 DOF short.

**The aspect ratio is a stored, load-bearing number you cannot compute.** It is
advance width over cap height and it is what the two derived points are pinned
to, so a wrong seed leaves them off their equations. Computing it means
reimplementing FreeType. `utilities/slvs_text.py` instead builds a throwaway sketch,
lets `solvespace-cli regenerate` write back the value SolveSpace computed, and
extrudes the text to read the **ink box** off the mesh. That second part
matters: advance width is not ink width (side bearings: here 0.135 cap-heights
of bearing on the left) and cap height is not ink height (the round G
overshoots, so the ink is 1.0375 cap-heights tall, not 1). Taking the cap height
as 20 mm would have made the ink 20.75 mm tall — 0.75 mm outside the panel —
and centring by the advance box would have left it 0.22 mm off centre. It refuses to proceed if the font did not resolve, which it detects
by the aspect ratio staying at its seed.

**A font that is not installed does not fall back.** SolveSpace looks the font
up by *file basename* (`TtfFontList::LoadFont`) and, failing that, draws a big
X at the text's corners. Verdana was the request; it is not installed here and
a file naming it would show an X on every machine without it. The bundled
Bitstream Vera Sans is compiled into the binary and always resolves — see D10.

**Orientation.** Seen from the front, +x is to the right and +z up, and
`u x v = x x z = -y` points *out* of the face. So the sketch plane sits 1 mm
outside the face with u = +x, v = +z, and the extrude runs back **against** its
normal — through the face and 3 mm into the wall. The far end of the cut is an
exact distance, so the wall left behind is a dimension rather than a hope.
This is the first of the orientation bugs in this repo that was right first
time; a render confirmed the text reads left to right and upright rather than
mirrored.

**Jitter test.** Jittering only the text's own 8 params recovers the exact
pocket volume at +-1, +-3 and +-8 mm. Jittering everything else at +-1 mm does
change the volume, but that is the older rounded-corner arcs flipping (6.6),
not the label — which the isolation shows, and which is why the +-0.3 mm row
remains the meaningful one.

### 6.9 Renaming the label: what a second string showed

Changing "MTG" to "Spock" went through first time, but only because the first
version fitted by ink box. It also exposed three things "MTG" could not, and
because renaming is expected to be routine (R10) the answer was to build a
procedure (`README.md`, `cad/relabel.py`) rather than leave it as "edit
`TEXT` and see".

**Descenders change the size of everything.** "MTG" has no descender and "Spock"
has one, so the capitals went from 19.3 to 15.1 mm. A fit by cap height would
have made the ink 26.55 mm tall — 6.55 mm over the panel, the p's descender
alone being 5.7 mm — and centring by the advance box would have mis-centred
it; neither was written, which is the whole benefit of
`slvs_text.fit()` measuring the ink. `relabel.py` says so in a note whenever it
happens, because it is the one result a person would otherwise take for a bug.

**o and p have counters, and that is fine.** "MTG" has no enclosed shapes, so
this was untested until "Spock". A counter is a tower of un-cut material
standing in the pocket, attached to the pocket floor, so the mesh stays one
shell and the engraving check holds — it counts floor area, which is only the
ring of the letter — and the volume removed still equals floor area x depth.
Rendered: the `o`'s counter stands, the `p`'s stands.

**A missing character is silent, so the tool makes it loud.** The case that
could have gone unnoticed: a character the font lacks (`A☃B`, anything outside
Latin-1) does *not* fail. FreeType prints "CID-to-GID mapping ... failed" on
stderr, SolveSpace carries on using the character code as a glyph index, and a
mesh comes out — containing whatever shape that glyph index happens to be.
`A☃B` exports successfully. `slvs_text.measure()` now reads that message and
refuses, naming the character and its code point.

**The tool changes nothing by default, and proves the build, not just the
fit.** `relabel.py "text"` fits the string and then builds the bottom in a
temporary folder with it, checking watertightness, shell count and the same
engraving checks the full verification runs. That second part matters because
the failure that measurement cannot predict is SolveSpace's NURBS boolean
breaking on some particular set of outlines (6.1 was exactly that for a
different cut). `--apply` is opt-in. It then rewrites the one `TEXT` line,
rebuilds, exports the bottom's STL, runs the full verification, and confirms
the top's `.slvs` is byte-identical to before — a relabel must not touch the
top, and if it does something else has changed.

What was tried, to establish what the guards are worth (all through the dry
run, so no repo state involved):

| label | result |
|---|---|
| Spock, Kirk, Wi | fits, one shell, passes |
| Jean-Luc Picard | passes, **width-limited**: capitals shrink to 6.7 mm, stroke ~0.9 mm |
| Q&A (2024), He said "hi", Beam me up, 0123456789 | pass; width-limited; stroke 1.1-1.2 mm |
| AVAV, Ty To, fjfj, rnrn, WWW, MMMM, gjpqy, @#%&* | pass, one shell — touching and overlapping glyph pairs did not break the boolean |
| A☃B, 日本 | **refused**: character not in the font |
| empty, spaces only | **refused** |
| 40 x "x" | **refused**: over the 32-character limit |

Two limits are therefore soft rather than hard, and the tool warns instead of
refusing: width-limited labels (still engraves, just smaller) and thin strokes
(under 1.2 mm "printable but only just", under 0.8 mm — two nozzle widths —
"will not print reliably"). 0.8 mm is a rule of thumb for a 0.4 mm nozzle, not
a measured property of this printer.

The stroke is measured, not remembered: a capital I in a sans face is a plain
bar, so `slvs_text.stem_width()` measures one and scales by the cap height.

**Archive naming.** The repo has an `archive/` folder of STLs named
`ultra_guard_pro_100_bottom-<label>.stl` (`-MTG`, `-BLANK`). `--archive`
follows that and refuses to overwrite. It is opt-in, and it archives the *new*
label; keeping the outgoing one is a manual step before relabelling, which is
how `-MTG` got there.

### 6.10 The snap domes: how they were missed, and what finding them taught

**How they were missed.** Every check in this repo compared things the rebuild
already had. The face-by-face comparison only walks planar faces present in
both meshes, and the lip's outer x faces *are* in both: they matched to
0.00001 mm. A dome is 336 small non-planar facets that group into nothing, so
it fell under the comparison's area floor. The interference grid sampled
vertical rays through the wall band and never looked outside the lip face. And
the clue was in the first analysis: the lip's outer x faces were 419 mm^2
against the ~477 a plain 6 mm lip gives, which I read past.

The general lesson is the one 6.7 taught from the other side: **a check that
only looks at what you built cannot find what you left out.** `audit_missing.py`
is the answer (below).

**How they were found.** Triangles with a vertex clearly outside the lip face
(more than 4 microns), above the seam plane, grouped by position: two clusters
of 324 on each side, identical left and right, 0.772 high. The base ring is
1.553 x 1.299 (ratio 1.1953, the y scale) and 1.299 = sqrt(1.5^2 - 0.75^2), so
the base design's dome is a cap of a 1.5 mm sphere 0.75 high, and the height
profile matches that sphere at every radius sampled.

**Measuring positions: use the bounding box, not the mean.** A first pass took
each ring's centre as the mean of its vertices and put the dimples 0.13 mm
higher than the domes at the front. That was an artefact: a search window clips
the ring unevenly, and a vertex mean follows the clipping. The bounding box of
the ring is immune to it, and gives dimples coaxial with domes to 0.031 mm.
The 0.13 mm was reported once, in passing, and is wrong; nothing was built on it.

**The dimple is not the dome's mirror, and the original presses itself.**
Sectioning dome and dimple at the same depth below their rims:

| depth | dome half-width in y | in z | dimple half-width in y | dome minus dimple in y |
|---|---|---|---|---|
| 0.05 | 1.500 | 1.260 | 1.380 | +0.12 |
| 0.25 | 1.320 | 1.120 | 1.220 | +0.10 |
| 0.45 | 1.080 | 0.900 | 0.980 | +0.10 |
| 0.65 | 0.680 | 0.560 | 0.620 | +0.06 |

The dimple is a circle and the dome an ellipse, wider than it in y at every
depth sampled from the rim down to 0.65 (at the very tip, 0.72, the dimple is
0.02 wider). The original's own bottom therefore overlaps its own top by ~0.1 mm at
each flank. `check_ugp100.py` reports this as 0.73 mm of "overlap", which is the
*height* of that thin sliver along a vertical ray, not its thickness; it took
a section to see that, and the check output now says so rather than leaving it
to be misread. The rebuilt dome does not do this (D11).

**Why a lathe, and why the hemisphere.** A spherical cap cannot be an extrude:
its end caps are flat, so the only extrude-shaped dome is a flat-topped boss.
A lathe of a closed profile (a centre, an apex on the axis, and a point on the
equator, joined by the axis edge, a square edge and an arc) gives the cap. The
profile is the *hemisphere*, not the bare cap: its flat face sits 0.707 inside
the lip, in solid material, so no face of the dome is coincident with a face of
the lip. A cap cut off exactly at the lip face would put two coplanar faces
into the boolean, which is the thing these booleans handle worst. The same trick
for the dimple puts the hemisphere's flat face 0.914 into the empty groove.

A profile edge on the lathe axis makes SolveSpace print `Vector::WithMagnitude(1)
of zero vector!` for each cap (the zero-width surface that edge sweeps out). It
is noise: the mesh is one watertight shell and the cap measures exactly its
parameters.

Each profile is 14 unknowns and 14 equations (7 points; 4 coincidences, the
axis horizontal, the square edge vertical, one radius dimension, two placement
dimensions, and the arc's own equal-radius equation). `dof_report()` gets all
eight to rank 14.

**Checking it, and checking the check.** `check_snap()` measures all 8 caps
against their parameters (height, base radius and centre to 0.001 mm), tests
engagement over the domes' footprint for all four pairings, and measures the
nearest approach of dome to dimple: 0.0253 mm against a design of 0.0254. Then
the control: **the same bottom against a top built without dimples must
overlap, and does, by 2.54 mm**. Without that, "seats clear" is as meaningless
as the old grid was.

| pairing | at the domes |
|---|---|
| rebuild bottom + rebuild top | seats clear |
| rebuild bottom + ORIGINAL top | seats clear |
| ORIGINAL bottom + rebuild top | overlap (as the source's own pair) |
| ORIGINAL bottom + ORIGINAL top | overlap (the source's own press-fit, ~0.1 mm) |

**The audit.** `cad/audit_missing.py` samples the original densely (vertices,
centroids and edge midpoints: ~57 000 points on the bottom), finds each one's
distance to the nearest point of the rebuild, and keeps those over 0.25 mm. A
distance is not a defect: a dropped fillet is also far from the rebuild. So
regions that are *recorded decisions* are subtracted: the corners (D4), the
perimeter rounds (D3), the seam-edge and lip-top fillets (D5), the groove-roof
blend (D6), and the mouth bevel (D5). What is left is, by construction,
something nobody decided. For the rebuild as it now stands: **nothing**, in
either part. `--prove` runs it on a rebuild *without* domes and dimples and
requires the audit to report all eight, and it does: exactly four clusters in
each part, at exactly those positions.

Its limits: it only looks from the original toward the rebuild, so it finds
what is missing and not what is extra; its zones are my own judgement of what
is intended; and a feature under 0.25 mm will not show. It also found
something while being written: the mouth-bevel difference corrected in D5.

---

## 7. Structure of the model

### 7.1 Files

| File | What it is |
|---|---|
| `cad/ugp100_params.py` | every dimension, with the base-design/scale derivation written down |
| `../utilities/slvs_text.py` | asks SolveSpace for a string's aspect ratio and ink box, fits text to the panel, and rejects strings that cannot be engraved |
| `cad/relabel.py` | changes the label: fit report, trial build, then (with `--apply`) rewrite, rebuild, export and verify |
| `README.md` | the runbook for changing the label |
| `cad/build_ugp100.py` | emits both `.slvs` |
| `cad/check_ugp100.py` | the verification in section 5, including the degree-of-freedom check and the snap engagement |
| `cad/audit_missing.py` | what the original has that the rebuild does not (6.10); `--prove` shows it can find a missing feature |
| `../utilities/slvs_write.py` | a reusable `.slvs` writer (groups, requests, params, constraints), plus `dof_report()` |

The part's scripts are thin: the machinery they use is shared, in
`../utilities/` (see its README): `slvs_write` and `slvs_shapes` to build,
`slvs_check` to verify a generated file, `slvs_info` to read one, and
`mesh_geom` / `mesh_rays` / `mesh_planes` / `mesh_features` / `mesh_compare` for the
measuring in `check_ugp100.py` and `audit_missing.py`. They were private
helpers in these scripts until they were needed elsewhere; moving them changed
nothing, which was verified: both `.slvs` still build byte for byte, and the check
and audit give identical output.

`build_ugp100.py` reproduces both `.slvs` byte for byte, so the generator
and not the `.slvs` is the source of truth for the dimensions. Editing a
`.slvs` in the SolveSpace GUI is fine and expected — just know that
re-running the build overwrites it.

**The `.stl` exports are not reproducible, and that is not a bug in the
model.** `solvespace-cli export-mesh` is nondeterministic: three runs over
an unchanged `.slvs` at the same chord tolerance gave three different files,
two of them with a different triangle count (258 vs 260). Volume agrees to
0.001 mm^3, the bounding box is identical and both are watertight single
shells — it is only the choice of how to split the flat faces. So the STLs
churn in git whenever they are regenerated; do not go looking for a
geometry change behind it.

### 7.2 Build sequence

**Bottom** (6 sketch + extrude pairs, then 4 lathes):

1. exterior rounded rectangle, extruded up past everything — UNION
2. cut away everything above the seam plane — DIFFERENCE
3. the lip's footprint back as a *solid* block, same vertical extent — UNION
4. cut away everything above the lip-top plane — DIFFERENCE
5. the four snap domes, one lathe each — UNION (D11)
6. the engraved label — DIFFERENCE (D10)
7. the card cavity, from the floor datum upward — DIFFERENCE
   (which is what turns step 3's block into a ring)

Doing the cavity *after* the lip block is what keeps every sketch a single
closed loop; the alternative is a two-loop ring sketch.

**Top** (4 pairs, then 4 lathes):

1. exterior rounded rectangle, sketched on the exterior top face and pushed
   down — UNION
2. open the bottom along the seam plane — DIFFERENCE
3. the card cavity, from the ceiling datum down and out — DIFFERENCE
4. the groove, via the x-normal trapezoid of 6.1 — DIFFERENCE
5. the lead-in bevel round the groove's mouth, as the two cutters of D9 —
   DIFFERENCE
6. the four snap dimples, one lathe each — DIFFERENCE (D11)

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
| the label's text | **`python3 cad/relabel.py "text" --apply`** — see `README.md`, do not hand-edit `TEXT` |
| the label's panel or depth | `PANEL_W`/`PANEL_H`, `TEXT_DEPTH` (asserted against the wall), then rebuild and check |
| the label's font | `TEXT_FONT`; pick one present on every machine that will open the file |
| the snap's strength or position | `BUMP_H`, `BUMP_BASE_R`, `DENT_DEPTH`, `DENT_MOUTH_R`, `SNAP_POINTS`; the dome seats with `(GROOVE_HX + DENT_DEPTH) - (LIP_HX + BUMP_H)` clearance, so change dome and dimple together |
| easier to drop the top on | `MOUTH_CHAMFER` (0.6); it comes out of the seam land and the lip's full-width engagement, see D5 |
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
  to open `CLEAR_X`/`CLEAR_Y` up after the first print; the 0.6 mm mouth
  bevel is there to make that first attempt go together at all.
* The groove-roof fillet (D6) is the stress riser to watch.
* **The label's print orientation is unstudied.** The bottom prints upright, so
  each letter's top edge is a roof over a pocket 3 mm deep, supported at its
  back and open at the front. That is a short cantilever rather than a bridge
  and should print, but the round of the G is a shallow overhang worth a look
  in the slicer preview.
* **The snap is untested on a printed part, and is where the print matters
  most.** The dome is 0.77 mm of interference against a lid whose walls have to
  flex over it. Whether it clicks, is too stiff to close, or lets go too easily
  depends on printed wall stiffness, layer orientation and tolerance, none of
  which a mesh check can see. The source's own dome squeezes its dimple ~0.1 mm
  per side in y (D11) and this rebuild's does not, so if the lid is loose, that
  is the first thing to put back.
* `-tight` in the source name implies a looser top exists. If it turns up,
  the only thing that should differ is `CLEAR_X`/`CLEAR_Y`.
* No print orientation or support study has been done for either half.
