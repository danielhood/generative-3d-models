# Design spec: 3 x 3 deck case (tray and lid)

Parts: `cad/build_case.py` -> `deck_case_3x3_bottom.slvs` (the tray),
`deck_case_3x3_top.slvs` (the lid), and `.stl` exports beside them
Parameters: `cad/case_params.py`  ·  Verification: `cad/check_case.py`
Source: the single deck box, `../mtg-deck-boxes/` (its spec: `ultra_guard_pro_100_spec.md`)
Revision: rev C, 2026-11-08 (rev C adds the finger ledges, section 4 D8)
Status: **rev B (no ledge) printed in PLA: fits and snaps as designed. Rev C (with the ledges) is modelled and mesh-verified; not printed.**
How to use it, and what every variable controls: [`README.md`](README.md).

A case that holds nine of the single Ultra Guard Pro 100+ boxes' card slots in a
3 x 3 grid: one tray, one lid. It is the single box multiplied, and almost every
dimension is *imported* from that box's parameters, so "the outer walls remain the
same" is true by construction and stays true if the single box is retuned. What is
new is the arrangement, and one structural change: **a flat seam**, where the
single box's slopes front to back.

---

## 1. The brief, and how it is met

| # | Requirement | Result (measured off the exported meshes) |
|---|---|---|
| R1 | 3 x 3 grid of slots, each the single box's size | nine slots, each **69.9992 x 76.4992** (the single box's cavity, exactly) |
| R2 | No angle front to back; constant height | seam is flat at z = 67.5534 |
| R3 | Tray as tall as the back (tall) edge of the single bottom | **73.5534** tall; the single bottom's STL is 73.5534 |
| R4 | Outer walls as in the single box | walls 4.1176 (x) / 4.7812 (y), lip 1.8529 / 2.1515, clearance 0.01176 / 0.07813 |
| R5 | Inner walls 3 mm | dividers **3.000** |
| R6 | Under 250 x 250 mm | **224.233 x 247.060** (245.060 plus the 3 mm ledge), margins 25.8 and 1.9 |
| R7 | Outer edge holds the case shut: domes and dimples on **all four sides, three per side, centred on each slot** | 12 domes on the tray, 12 dimples in the lid, one per slot per side |
| R8 | Lid has walls front-to-back **only**, none left-right | 2 front-to-back dividers; a line front-to-back through any slot meets only the two end walls |
| R9 | A finger ledge on the front of each half, 3 mm proud, 2 mm thick, flush with the tray's bottom and the lid's top, centred over 2/3 of the front, corners rounded | 149.49 wide at the wall, a flat 105.87 wide a full 3.000 proud, tangent arcs out to the wall; z = 0..2 on the tray, z = 100.05..102.05 on the lid |

---

## 2. What the brief left open, and what I assumed

Each of these has a sensible default and a one-line change; none is hard to undo.
**All seven were confirmed as correct on 2026-11-08**, after the first print. The
"if you meant otherwise" column is kept as the record of what each one controls.

| # | Not specified | Assumed | If you meant otherwise |
|---|---|---|---|
| A1 | Which "height" of the single bottom | its **bounding-box height, 73.553, including the lip**: the tray is that tall, and its outer walls stop 6 mm lower at the seam (z = 67.553) | The back *wall's* top is 68.824; the tray would then be 74.824 with its lip and the seam 1.27 mm higher. `TRAY_H` in `case_params.py` |
| A2 | Total height / the lid's height | **102.05**, the single box's, so the same 94.05 of card space with a 4 mm floor and ceiling; the lid is the remaining **34.50** | `H_TOTAL`; it must stay >= floor + card + ceiling |
| A3 | How the two halves' dividers meet | tray dividers (both directions) rise to **0.15 under** the lip-top plane; lid dividers hang to **0.15 over** the groove roof; so a **0.30 mm gap** where they meet, and the lip and roof own the seam | `DIV_GAP`; 0 makes them touch |
| A4 | Slot orientation | the single box's: **70 wide across x, 76.5 deep along y** (the direction a card stack is thick in, and what "front to back" means) | swapping would give 243.7 x 225.6, which also fits |
| A5 | Dome height above the seam | the single box's two domes sit 2.505 and 2.809 above its sloping seam; a flat seam has one height, so the **mean, 2.657** | `DOME_ABOVE_SEAM` |
| A6 | The mouth bevel | included, the single box's 0.6 x 0.6 lead-in | `MOUTH_CHAMFER`, 0 for none |
| A7 | A label | none | the single box's `relabel.py` does not apply here yet |

---

## 3. Dimensions

| | |
|---|---|
| interior of the whole case | 215.9976 x 235.4976 (3 slots + 2 dividers each way) |
| exterior | **224.2328 x 245.0600**, plus the ledge: **224.2328 x 248.0600** |
| tray | 73.5534 tall: floor 4.0, walls to z = 67.5534, lip to 73.5534 |
| lid | 34.4966 tall, z = 67.5534 .. 102.05: groove 6 deep, ceiling 4.0 thick (underside z = 98.05) |
| card space | 94.05, floor to ceiling, in every slot |
| slot pitch | 72.9992 across x, 79.4992 along y |
| dividers | at x = +-36.4996 (running along y) and y = +-39.7496 (running along x) |
| domes / dimples | at z = 70.2105; across x on the front and back faces at -72.999, 0, +72.999; along y on the left and right faces at -79.499, 0, +79.499 |

---

## 4. Decisions

**D1 — A flat seam makes this far simpler than the single box.** The single box's
slope forced every cut onto a tilted plane, and an extrude cannot be skewed (that
box's spec 6.1), so the groove had to be built sideways. Here every block and
cutter is a plain vertical extrude, and the only things that are not boxes are the
snap caps. Nothing in this file needed a workaround.

**D2 — The seam and lip planes are datum-dimensioned.** Each block is sketched on a
datum at the plane that matters (the seam for the walls, the lip top for the lip,
the roof for the groove, the ceiling for the cavity) and pushed from there, so those
mating planes are real constraints rather than extrude lengths.

**D3 — Dividers join by overlap, never by sharing a face.** Each bar runs 1 mm into
the lip or wall at both ends, and into the floor or ceiling, so it unions with
solid material. A bar whose end or top lay exactly in another face's plane would put
a coplanar face into the boolean, which is what these booleans handle worst. This is
also why the 0.15 gaps in A3 are not cosmetic: a tray divider topped exactly at the
lip-top plane would be coplanar with the lip where they overlap.

**D4 — Tray dividers in two groups, lid dividers in one.** Bars that cross cannot
share a sketch (an extrude wants disjoint loops), so the tray's x- and y-direction
dividers are two groups unioned together. The lid has only y-direction bars, which
are disjoint, so one group.

**D5 — Why the lid has no left-right dividers** (the brief's reason, recorded so it
is not "optimised" later): a stack that is not perfectly vertical leans front or back,
and a left-right wall in the lid would meet it and could bend the cards while the lid
goes on. Front-to-back walls are parallel to the lean and meet nothing.

**D6 — The snap is the single box's, on all four sides.** The dome and dimple are
the single box's (height 0.7721, base radius 1.299; depth 0.7857, mouth radius
1.433), built by the same lathed hemisphere (`slvs_shapes.spherical_cap`, which
gained a `along="y"` option for the front and back faces). The dome is a circular
cap, not that box's ellipse; spec D11 there explains why.

**D7 — The y-face domes seat looser than the x-face ones.** See 5.

**D8 — The finger ledge (rev C).** The case is too wide for one hand to grip across, so
each half gets a shelf on its front (-y) face to hook fingertips on: the lid's is flush
with the top of the lid (fingertips go under it and lift), the tray's flush with the
bottom of the tray (fingertips press down on it). Requested: 3 mm proud, 2 mm thick
(first sketched at 2 mm by 1 mm, then raised twice), centred over 2/3 of the front, the
same on both halves, corners slightly rounded. The shape chosen from two sketched
options was the *clipped* arc: an arc over the 149.49 mm span, cut flat at the ledge's
depth. Its sagitta was 4 mm at 2 mm proud; at 3 mm proud the same 4 mm would clip the
flat down to 75 mm, so it is **6 mm**, which keeps the flat 105.87 wide. Its two corners
(where the clip meets the arc) are rounded by replacing each cut-off arc with one
**tangent to the flat**, radius 80.8, dropping the 3 mm over the remaining 21.8 mm to
the wall. So the outline is a flat with no corner anywhere on it, ending in a thin wedge
(about 16 degrees) against the wall; nothing in the outline catches a fingertip or a
sleeve. Only the plan view is rounded, as the ledge is 2 mm thick.

* *Why front only.* Depth is the tight axis: 245.06 plus 3 is 248.06, 1.9 under the
  bed; a ledge on the back as well would not fit (251.06).
* *Why flush with the ends.* Both halves print on those faces, so a flush ledge is a
  plain 2 mm plate on the bed and needs no support; and the tray still stands flat.
* *What it stays clear of.* The tray's ledge is z = 0..2 and the tray stops at
  73.55; the lid's is z = 100.05..102.05 and the lid starts at 67.55: neither ledge
  touches the other half, the seam, the lip or any snap.
* *How it is built.* A 28-equation, 0-DOF plan profile (`build_case.finger_ledge`) on a
  datum at the part's end face, extruded 2 mm into the part. It runs 1 mm into the
  wall so it joins by overlap. Its bottom (tray) / top (lid) face is *coplanar* with
  the part's own, which is what makes it flush; SolveSpace unions that cleanly (one
  watertight shell, no extra boolean retries on the tray).
* *The tip.* The flank's last ~6 mm are under 0.2 mm proud, below what a 0.4 mm
  nozzle prints as a separate feature, so the printed ledge will look about 138 mm
  wide, not 149. Harmless: it joins the wall, and is not where fingers go.
* *Not tried.* The size is a request, not a measurement. How much purchase a 3 mm
  ledge gives a fingertip is unknown until printed; `LEDGE_OUT` and `LEDGE_H` are the
  knobs, and the bed is the limit on `LEDGE_OUT` (1.9 mm of room left; raise
  `LEDGE_ARC_SAG` with it to keep the flat wide).

---

## 5. A finding: front and back domes seat with 0.092 mm, left and right with 0.025

The apex gap of a seated dome is the lip-to-groove clearance **plus** the dimple's
extra depth (0.0136). The clearance is not the same on both axes, because the single
box's walls were scaled 1.0294 in x and 1.1953 in y: **0.0118 across x, 0.0781 across
y.** So:

| | clearance | apex gap (measured) | effective interference while sliding |
|---|---|---|---|
| left / right faces | 0.0118 | 0.0253 (design 0.0254) | 0.7721 - 0.0118 = **0.760** |
| front / back faces | 0.0781 | 0.0913 (design 0.0917) | 0.7721 - 0.0781 = **0.694** |

The single box only had x-face domes, so this never arose there. It means the
front and back snaps are ~9% weaker and the lid has ~0.07 mm more play in y. It is not
a defect, but it is not what "the same dome on every side" suggests. **The first
print did not show it:** the fit was reported as neither too loose nor too tight,
so no correction was made. If a printed lid is ever looser front-to-back than
side-to-side, the fix is to raise the y-face domes by 0.066 (or make the y-face
dimples that much shallower).

This was found by the verification, not by the build: the check that measures the
nearest approach of dome to dimple first used the x figure for all twelve with a
tolerance wide enough to pass the y caps. It is per-axis and tight now.

---

## 6. Verification

`python3 cad/check_case.py` (about 20 s) exports both parts through SolveSpace and
measures the meshes. **All checks pass:**

* every sketch group of both parts is 0 DOF, 0 redundant (20 and 21 groups);
* each part is one watertight shell (tray 4 786 triangles, 676 296 mm^3; lid 4 698,
  368 050 mm^3);
* footprint, slots, walls, lip, clearances, heights, card space and divider
  positions as in the table in 1;
* all 12 domes and all 12 dimples measure to their parameters (height/depth to
  0.002, radius to 0.003, centre to 0.005), and there are exactly three domes on
  each of the four lip faces and no others;
* the pair overlaps nowhere over 1 800 vertical columns across the whole footprint
  and 1 092 more across the domes' footprints;
* **a control**: the same tray against a lid built *without* dimples overlaps by
  2.54 mm, so the engagement test can fail.
* **the ledges** (section 9 of `check_case.py`): each half's front face is measured
  at 17 stations along x, mid-thickness, against the flat-then-flank-then-wall outline
  (0.03 mm tolerance, the mesh's chord tolerance); each is exactly one solid run over
  z = 0..2 (tray) and 100.05..102.05 (lid), measured through the middle of the ledge; nothing
  else stands proud of the wall; and **a control**: a half built *without* the ledge
  fails that test 17 ways.

`python3 ../utilities/slvs_check.py deck_case_3x3_bottom.slvs` (and `_top`): the
mesh is one shell, the constraints survive a reload (289 -> 289 and 285 -> 285), and
every sketch is restored after perturbing ~400 parameters by up to 0.3 mm.

SolveSpace prints surface-intersection retries building the domes' sphere booleans
(8 for the tray, 112 for the lid). The meshes are verified clean and every cap
measures exactly, so they are benign; see `utilities/slvs_cli.py`.

---

## 7. Print results, open items and risks

* **Rev B (no ledge) printed once, in PLA, 2026-11-08: the lid locks perfectly.**
  Neither too tight nor too loose, and with the same feel as prints of the single
  box's original STLs (printed in PLA and PETG). Original-STL and rebuilt single-box
  halves also interchange (an original top on a new bottom, and the reverse), which
  says the lip, groove, clearances and snap carried over from the originals are
  right, and they are what this case imports. Not tried: PETG for the case; a
  second printer or nozzle; a print after long storage.
* **Rev C adds the finger ledges and is unprinted.** They change nothing that print
  tested: the fit, lip, groove and snaps are untouched (the checks above give the same
  figures as before). What is untested is the ledge itself: whether 3 mm is enough
  purchase for a fingertip, and whether 2 mm is stiff enough in PLA at 3 mm
  out from the wall.
* **The 12-dome risk below did not materialise** in this print. The closing
  force was reported as right. The numbers are kept because they are what to
  look at if a different material or printer changes that.
* **The case is 12 domes' worth of snap, not 4.** Each is 0.77 mm of interference
  against walls that have to flex, and the case closes along a 245 mm edge. Twelve
  against the single box's four is the only number here: how that adds up to a closing
  force depends on how the printed walls flex, which a mesh cannot say, but a lid that
  is hard to remove is a plausible first-print complaint. `BUMP_H` (and
  `DENT_DEPTH`) in the single box's parameters is the knob; the tray's long wall
  panels between dividers are what flex, so the first thing to look at after a
  print is whether the lid can be started at all.
* **y-face domes are weaker** than x-face ones (section 5); not noticeable in the
  first print.
* **The lid's dividers meet its front and back walls only above the groove roof**
  (they run 1 mm into the wall there); below the roof the groove is open, so near
  the seam each divider ends against empty groove, 0.15 above the tray's divider. It
  hangs from the ceiling along its whole length, so it is not weakly attached, but it
  is not attached at its ends below the roof.
* **No finger notches or thumb scoops** for lifting a stack out of a slot; the brief
  did not ask for them. A tray divider tops out at z = 73.40 against a ceiling at 98.05, so
  the top 24.6 mm of every stack stands clear for gripping with the lid off.
* **No label** (A7).
* **STL exports are not reproducible** (`solvespace-cli export-mesh` varies run to
  run); the `.slvs` is, byte for byte.

---

## 8. How to rebuild

```bash
python3 cad/build_case.py     # writes both .slvs
python3 cad/check_case.py     # verifies them
solvespace-cli export-mesh --chord-tol 0.02 --output deck_case_3x3_bottom.stl deck_case_3x3_bottom.slvs
```

Dimensions live in `cad/case_params.py`, almost all imported from
`../mtg-deck-boxes/cad/ugp100_params.py`; change them there and rebuild. The
reusable machinery (`slvs_shapes`, `slvs_check`, `mesh_rays`, `mesh_features`...) is
in `../utilities/`.
