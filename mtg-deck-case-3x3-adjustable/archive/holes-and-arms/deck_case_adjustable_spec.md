# Design spec: adjustable deck case (tray, lid, divider)

Parts: `cad/build_case.py` -> `deck_case_adjustable_bottom.slvs` (the tray),
`deck_case_adjustable_top.slvs` (the lid), `deck_case_adjustable_divider.slvs` (one
divider), and `.stl` exports beside them
Parameters: `cad/case_params.py`  ·  Verification: `cad/check_case.py`
Source: the 3 x 3 case, `../mtg-deck-case-3x3/` (its spec: `deck_case_3x3_spec.md`), and
through it the single deck box, `../mtg-deck-boxes/`
Revision: rev A, 2026-11-17
Status: **modelled and mesh-verified; not printed.** The outer shell is the 3 x 3 case's,
which printed well in PLA with its finger ledges; the lane walls, holes, slits and dividers
are new and untested on a printer.

A case whose three lanes run the full depth, with movable dividers that hang in holes
in the lane walls. It is the 3 x 3 case with the inside rethought; the outside is
unchanged, so the lock, the finger ledge and the cards' fit carry over.

---

## 1. The brief, and how it is met

| # | Requirement | Result (measured off the exported meshes) |
|---|---|---|
| R1 | Three sections running front to back, movable dividers placeable in any of them, giving sections of variable size | three lanes of 69.9992 x 232.6976; 57 divider positions along each, 4 mm apart |
| R2 | Dividers stay vertical, so cards cannot slide or tilt | arms 0.2 mm clear in a 2 mm hole, 58 mm long in 60 mm holes, on both sides of the lane |
| R3 | Lane walls stay smooth; the holding mechanism must not interrupt them | the lane faces measure 69.9992 across at every hole and between holes, z = 6 to 70, below the slits; the only break is the top 3 mm (R6) |
| R4 | Walls running front to back widened to 5 mm | four 5.000 walls: two partitions, two liners |
| R5 | In the middle of each, vertical 2 x 2 mm square holes, 4 mm apart | 57 per wall, 2.000 square, centres -112 .. +112 at pitch 4.000, centred in the wall |
| R6 | Slits beside each hole so the divider drops in, its top flush with the wall tops | the top 3.000 mm of the lane-side skin cut away at every hole; the bridge fills it, top at 73.4034 = the wall top |
| R7 | Divider 1.6 mm thick, arms 1.6 wide, 1.6 space between each arm and the body | plate 1.600, arms 1.600; the slot is 1.8 from the body: see D3 |
| R8 | The body continues 12 mm above the walls | 12.000 above the wall top; 12.65 under the lid's ceiling |
| R9 | The lid adjusted for the extra width | four 5 mm walls hang from the lid's ceiling to meet the tray's, 0.30 mm gap |
| R10 | Within the printer bed | **238.233 x 245.260** mm, margins 11.8 and 4.7 |
| R11 | Domes, dimples, finger ledge unchanged | the 3 x 3 case's: 12 domes, 12 dimples, ledge 3 mm proud, 2 mm thick |
| R12 | One divider modelled; cloned in the slicer | `deck_case_adjustable_divider.slvs` |

---

## 2. What was settled, and how

Each was decided with the user before the build; the sketches that fixed them are in
the conversation.

| # | Question | Answer |
|---|---|---|
| Q1 | What is the "1.6 mm space between arm and body"? | The gap that **straddles the wall's 1.5 mm skin**: the body stays in the lane, the arm is in the hole, and the skin sits between them. The two numbers only fit under this reading |
| Q2 | The outer lanes' outer walls carry the 1.85 mm snap lip, which cannot hold a hole | **Liner walls**: a 5 mm slotted wall inside each outer wall (the user's option A). The outer shell stays exactly as printed |
| Q3 | Hole depth and arm length | holes 60 deep; arms 58 long (2 mm short of the bottom) |
| Q4 | Neighbouring lanes' dividers at the same position | cannot, by design: the shared hole is 2 mm and two arms do not fit |
| Q5 | The slits break the smooth face | accepted: the face is smooth below them, and the lanes' tops are open |
| Q6 | Interior depth | unchanged from the 3 x 3 case, 232.6976 |
| Q7 | The slot's width | 1.8 from the body: the body is 0.2 narrower than the lane, so 1.6 + 0.2 |
| Q8 | How the divider sits | it hangs on its bridges; the body ends 0.5 above the floor |

---

## 3. Dimensions

| | |
|---|---|
| lanes | 3 x 69.9992 (the single box's cavity width), 232.6976 long |
| lane walls | 5.000, at x = -112.4988, -37.4996, +37.4996, +112.4988 (centres) |
| interior | 229.9976 x 232.6976 |
| exterior | **238.2328 x 242.2600**, plus the ledge: 238.2328 x 245.2600 |
| tray | 73.5534 tall; lid 34.4966; card space 94.05 (all as the 3 x 3 case) |
| wall tops | tray 73.4034; lid walls hang to 73.7034 |
| holes | 2.0 x 2.0, 60.0 deep (bottom z = 13.4034), 57 per wall, y = -112 + 4k |
| slits | top 3.0 of the lane-side skin, 2.0 wide along y; partitions both sides, liners lane side |
| divider | body 69.5992 x 1.6 (x by y), z = 4.5 .. 85.4034; arms 1.6 wide, z = 15.4034 .. 73.4034; bridges z = 70.4034 .. 73.4034; 76.3992 wide overall |
| snap domes | at z = 70.2105: front/back at x = -74.999, 0, +74.999; sides at y = -78.099, 0, +78.099 |

---

## 4. Decisions

**D1 — The shell is not touched.** The outer wall, lip, groove, clearances, domes,
dimples, mouth bevel and finger ledge are the 3 x 3 case's, imported or copied
unchanged, because the 3 x 3 case printed with a lock "neither too tight nor too
loose". Every check on them is the 3 x 3 case's check, with the same numbers.

**D2 — Liners, not thicker outer walls.** The lip is the inner 1.85 mm of the outer
wall above the seam; a 2 mm hole and a slit cannot pass through it without cutting the
lock. A liner against the cavity wall gives the outer lanes the same 5 mm slotted wall
as the partitions, at the cost of 10 mm of width, and leaves the lock alone. A liner
also runs 1 mm into the outer wall, so it joins by overlap rather than by sharing the
cavity wall's plane.

**D3 — The divider's slot is 1.8 from the body, not 1.6.** The arm's lane-side face is
1.6 from the *lane face* (so 0.1 clear of the 1.5 mm skin), and the body is 0.2 inside
the lane face on each side so it cannot jam. Measured from the body the slot is
therefore 1.8. Cutting it 1.6 from the body would leave 1.4 mm for a 1.5 mm skin.

**D4 — A hanging divider, one flat profile.** The divider is a single polygon in the
x-z plane, extruded 1.6, so the plate, arms and bridges are one extrude and print as
one flat piece. The bridge is exactly as tall as the slit (3 mm), so its underside rests
on the skin under the slit and its top is flush with the wall top; the divider hangs from
its two bridges, and the arms only keep it vertical. The profile is 16 lines pinned
vertex by vertex (two plane distances each): 64 unknowns, 64 equations, 0 DOF.

**D5 — The holes are drawn once and repeated.** One 2 x 2 hole per wall (four in one
sketch), extruded as a cutter, then SolveSpace's "step translating" repeats it 57 times;
likewise one slit per wall. 456 holes and slits cost two sketches, two extrudes and two
repeat groups, and the pitch and count are editable in the GUI. The writer gained
`Sketch.translate`. **Found by measuring** (and pinned by `utilities/selftest.py`): the
group stores *half* the step, as an extrude stores half its length, and the count
*includes* the original. A stored 4.0 gave holes 8 apart.

**D6 — The slit is wider than the lane face, in air.** Each slit cutter reaches 1 mm past
the lane face into the lane, so no cutter face lies in the wall's own face (the same
coplanar-face rule as D3 of the 3 x 3 spec). A partition's slit cuts its whole 5 mm
width across the hole (the hole is in the middle, so that is hole plus both skins), so
either neighbour can use it.

**D7 — Hole positions are symmetric about y = 0.** 57 holes at pitch 4, the end holes
at least 2 mm from the front and back walls (they are 3.35). Hole 28 is at y = 0.

---

## 5. Verification

`python3 cad/check_case.py` (about a minute) exports all three and measures the meshes.
**All checks pass.**

* every sketch group of all three parts is 0 DOF, 0 redundant;
* each part is one watertight shell (tray 12 914 triangles, 774 433 mm^3; lid 4 714,
  461 126; divider 60, 9 324);
* footprint, lanes, walls, lip, groove, clearances, heights, card space as in 1;
* all four lane walls: 57 holes each, 2.000 wide, centres at -112 + 4k to 0.001,
  bottoms at z = 13.4034, tops between holes at 73.4034; slits on exactly the right skins
  at 70.4034 (partitions both sides, liners the lane side only, outer skin full height);
* lane faces smooth: 69.9992 across at holes and between them, z = 6 to 70;
* the lid: four walls hanging to 73.7034, 0.30 over the tray's, each one unbroken front
  to back;
* 12 domes and 12 dimples measure to their design, three per face and no others;
* both ledges, 17 stations each;
* tray and lid overlap nowhere over 2 280 columns; the domes seat in the dimples with the
  same 0.025 / 0.091 apex gaps as the 3 x 3 case;
* **the divider, placed in lanes 1, 2 and 3 at the first, middle and last holes**: no
  overlap with the tray or lid over a fine grid, arms 0.200 clear in y, 0.1 / 0.3 in x,
  body 0.2 off each lane face, bridge resting on the slit floor with its top at the wall
  top, 12.000 above the wall, bottom 0.5 above the floor;
* neighbouring lanes' dividers collide at the same hole (58 mm of overlap in the shared
  hole) and clear one hole (4 mm) apart;
* the committed STLs match a fresh export of their `.slvs`.

**Controls that must fail, and do:** a tray without holes fails the hole test 18 ways; a
tray without the ledge, and a lid without it, fail the ledge test 17 ways each; a lid
without dimples overlaps the domes by 2.54 mm; a divider with a 1.3 slot is caught as
overlapping the tray by 55 mm; a tray without holes overlaps a divider by 58 mm; the
tray's STL checked as the lid's fails.

`utilities/slvs_check.py` on all three: the mesh is one shell; the constraints survive a
reload (tray 388 -> 388, lid 309 -> 309, divider 51 -> 51); every sketch is restored
after perturbing ~540 / 430 / 67 parameters by up to 0.3 mm, **except** one seed of five
on the tray at 0.3 mm. That is the lip's 0.55 mm corner radius (the same rounded
rectangle the single box and 3 x 3 case use) flipping to its other valid solution when
its parameters move by more than half its radius; `slvs_check.py` documents this. It
restores on all six seeds at 0.15 mm, the lip group alone reproduces it, and
`dof_report` says 0 DOF. Not a missing constraint.

### Two bugs in the check itself, worth remembering

* **A ray cast along an axis needs air at both ends of its window.** The divider checks
  cut the tray down to a window near the divider so the ray casts run quickly. A window
  that cut a 2 mm web in half left an unmatched hit, which flipped the in/out parity of
  every later hit on the ray and silently lost every span. The fix: windows whose edges
  are hole centres (air), opened out past the front and back walls near the ends.
* **A smoothness test compared the wrong thing**: across x at a hole, the gaps include the
  hole's 2.0 in each wall as well as the three lanes, and below the holes' bottom they
  do not. It now states both expectations.

---

## 6. Open items and risks

* **Not printed.** The whole of what is new rests on mesh verification.
* **The fits are tight for FDM.** An arm has 0.2 mm clear in y, 0.1 mm beside the skin
  and 0.3 mm on the far side; the body 0.2 mm off each lane face. If a print makes the
  dividers bind, open `SKIN_GAP`, `ARM_W` and `BODY_CLEAR` and rebuild; the lock, lip and
  groove are untouched by these.
* **Thin, tall features.** The divider's arms are 1.6 x 1.6 mm and 58 mm long, printed
  lying flat; the 60 mm holes are 2 mm square channels, printed upright. Both are within
  what FDM prints but are the first things to look at.
* **Print time.** 228 holes and 228 slits in the tray add many small perimeters.
* **Slit edges.** The top 3 mm of each lane face is notched every 4 mm; the lane's top is
  otherwise open. Cards that rub the face at the top of a stack are the thing to watch.
* **Only 4 mm steps.** A divider position is one of 57; sections are multiples of 4 mm.
* **The lane faces' smoothness is measured on the mesh at 0.02 mm chord tolerance**, which
  is fine for flat faces.
* **The 12-snap lock and the finger ledge** are the 3 x 3 case's, which has been printed
  with both; the user reports they "work very well" (2026-11-17), so they are not changed.
* **STL exports are not reproducible** (`solvespace-cli export-mesh` varies run to run);
  the `.slvs` is, byte for byte.

---

## 7. How to rebuild

```bash
python3 cad/build_case.py     # writes the three .slvs
python3 cad/check_case.py     # verifies them
solvespace-cli export-mesh --chord-tol 0.02 --output deck_case_adjustable_bottom.stl deck_case_adjustable_bottom.slvs
```

Dimensions live in `cad/case_params.py`, almost all imported from
`../mtg-deck-boxes/cad/ugp100_params.py`. The reusable machinery (`slvs_shapes`,
`slvs_write.translate`, `slvs_check`, `mesh_rays`, `mesh_features`...) is in `../utilities/`.
