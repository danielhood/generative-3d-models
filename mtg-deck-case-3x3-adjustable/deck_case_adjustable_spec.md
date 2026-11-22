# Design spec: adjustable deck case (tray, lid, divider)

Parts: `cad/build_case.py` -> `deck_case_adjustable_bottom.slvs` (the tray),
`deck_case_adjustable_top.slvs` (the lid), `deck_case_adjustable_divider.slvs` (one
divider), and `.stl` exports beside them
Parameters: `cad/case_params.py`  ·  Verification: `cad/check_case.py`
Source: the 3 x 3 case, `../mtg-deck-case-3x3/` (its spec: `deck_case_3x3_spec.md`), and
through it the single deck box, `../mtg-deck-boxes/`
Revision: rev B, 2026-11-22 (rev A, the holes-and-arms design, is in `archive/holes-and-arms/`); body clearance raised from 0.4 to 0.8 mm per side after rev B, see section 7
Status: **modelled and mesh-verified. The divider and the slots were test-printed and fitted well;
the full tray in this design is not printed.** The outer shell is the 3 x 3 case's, which printed
well in PLA with its finger ledges.

A case whose three lanes run the full depth, with movable dividers that hang by tabs in slots in
the lane walls. It is the 3 x 3 case with the inside rethought; the outside is unchanged, so the
lock, the finger ledge and the cards' fit carry over.

---

## 1. The brief, and how it is met

| # | Requirement | Result (measured off the exported meshes) |
|---|---|---|
| R1 | Three sections running front to back, movable dividers placeable in any of them, giving sections of variable size | three lanes of 69.9992 x 232.6976; 37 divider positions in lanes 1 and 3, 38 in lane 2, 6 mm apart |
| R2 | Dividers stay vertical, so cards cannot slide or tilt | 25 mm tabs, 0.2 mm clear in 2.0 slots, on both sides of the lane: about 0.5 degrees of lean |
| R3 | Lane walls stay smooth; the holding mechanism must not interrupt them | the lane faces measure 69.9992 across at every height below the slots, at a slot's y and between; the only break is the top 25 mm (R6) |
| R4 | Walls running front to back widened to 5 mm | four 5.000 walls: two partitions, two liners |
| R5 | A way to hold a divider vertical at any of many positions | vertical slots in the lane faces, 2.0 wide, 3.5 into the wall, 25 deep, every 6.0 mm |
| R6 | The divider's top flush with the wall top, so the lid's walls meet | the tabs' top is at 73.4034 = the wall top; the lid's walls hang to 73.7034 |
| R7 | Divider 1.6 mm thick; slot and divider thickness as already fitted | plate and tabs 1.600; slots 2.000 |
| R8 | The body continues 12 mm above the walls | 12.000 above the wall top; 12.65 under the lid's ceiling |
| R9 | The lid adjusted for the extra width | four 5 mm walls hang from the lid's ceiling to meet the tray's, 0.30 mm gap. Unchanged by the slots |
| R10 | Within the printer bed | **238.233 x 245.260** mm, margins 11.8 and 4.7 |
| R11 | Domes, dimples, finger ledge unchanged | the 3 x 3 case's: 12 domes, 12 dimples, ledge 3 mm proud, 2 mm thick |
| R12 | One divider modelled; cloned in the slicer | `deck_case_adjustable_divider.slvs` |
| R13 | Shorter print time than the first design | the depth of small features falls about 60% (5,600 mm of slot depth, 13,700 of hole depth). Not measured in hours |

---

## 2. History: why the design changed

Rev A held the divider by **arms** in 60 mm deep square holes, with 3 mm slits and 4 mm pitch (archived in
`archive/holes-and-arms/`). A printed test of one divider and the base (2026-11-19) found:

* the arms had to be pushed into the holes with force, and were flexible at 1.6 mm;
* the divider's body could bind between the slots;
* the base took about 24 hours to print, because of the holes over most of the height of the walls;
* but the dividers **slotted in nicely** between the slits by their tabs alone, with the arms removed.

The user proposed removing the holes and arms and extending the slits to 25 mm (and the tabs with them), the body
0.4 mm narrower each side, and a 6 mm pitch, keeping the slot width and tab thickness. A short single-lane test base
and the new divider were built and printed (`archive/slot-test/`) and the test was good (2026-11-22). This revision
applies it to the full tray.

## 3. What was settled, and how

Decided with the user before the build, from the sketches in the conversation.

| # | Question | Answer |
|---|---|---|
| Q1 | The outer lanes' outer walls carry the 1.85 mm snap lip, which cannot hold a slot | **Liner walls** (kept from rev A): a 5 mm slotted wall inside each outer wall. The outer shell stays exactly as printed |
| Q2 | Slots on both faces of a 5 mm wall at the same position would cut it through at 3.5 deep | **Stagger**: lane 2's slots are half a pitch (3 mm) along from lanes 1 and 3's |
| Q3 | Slot depth into the wall, and the tab | slots 3.5 deep leaving 1.5; the tab reaches 3.2, stopping 0.3 short of the bottom |
| Q4 | Tab height | 25, equal to the slot depth, so the divider hangs on its tab bottoms, top flush |
| Q5 | Slot positions | 37 for lanes 1 and 3 (y = -108 .. +108, one at 0); 38 for lane 2 (y = -111 .. +111) |
| Q6 | The slot-test base | only the middle lane; no front or back wall; a 1 mm floor; 6 slots |

---

## 4. Dimensions

| | |
|---|---|
| lanes | 3 x 69.9992 (the single box's cavity width), 232.6976 long |
| lane walls | 5.000, at x = -112.4988, -37.4996, +37.4996, +112.4988 (centres) |
| interior | 229.9976 x 232.6976 |
| exterior | **238.2328 x 242.2600**, plus the ledge: 238.2328 x 245.2600 |
| tray | 73.5534 tall; lid 34.4966; card space 94.05 (all as the 3 x 3 case) |
| wall tops | tray 73.4034; lid walls hang to 73.7034 |
| slots | 2.0 wide (y), 3.5 into the wall, from z = 48.4034 to the top; set A 37 at y = -108 + 6k, set B 38 at y = -111 + 6k |
| faces | A on the liners' and partitions' faces towards lanes 1 and 3; B on the partitions' faces towards lane 2 |
| divider | body 68.3992 x 1.6 (x by y), z = 4.8 .. 85.4034; tabs 4.0 out from the body, z = 48.4034 .. 73.4034; 76.3992 wide over the tabs |
| snap domes | at z = 70.2105: front/back at x = -74.999, 0, +74.999; sides at y = -78.099, 0, +78.099 |

---

## 5. Decisions

**D1 — The shell is not touched.** The outer wall, lip, groove, clearances, domes, dimples, mouth bevel and
finger ledge are the 3 x 3 case's, imported or copied unchanged. The lid's `.slvs` is byte for byte what it was in
rev A, so its STL was not regenerated.

**D2 — Liners, not thicker outer walls.** (Unchanged from rev A.) The lip is the inner 1.85 mm of the outer wall
above the seam; a slot cannot be cut into it without cutting the lock. A liner against the cavity wall gives the outer
lanes the same 5 mm slotted wall as the partitions, at the cost of 10 mm of width, and leaves the lock alone. A liner
also runs 1 mm into the outer wall, so it joins by overlap rather than by sharing the cavity wall's plane.

**D3 — Staggered slots.** A partition's two faces carry different sets: set A (lanes 1 and 3) at multiples of 6, set B
(lane 2) 3 mm along. Their y ranges ([6m-1, 6m+1] and [6m+2, 6m+4]) never overlap, leaving a 1 mm full-thickness web
between neighbours, so the wall is 1.5 mm at the thinnest, anywhere. Without the stagger the partitions are cut through
(measured: thinnest 0.000). A side effect: dividers in neighbouring lanes can never share a position, and can be 3 mm
apart, where the first design forced a 4 mm stagger.

**D4 — A hanging divider, one flat profile.** The divider is a single polygon in the x-z plane, extruded 1.6, so the
plate and tabs are one extrude and print as one flat piece. Its tab bottoms rest on the slots' floors and its tops are
flush with the wall tops; the divider hangs from them, and the slots keep it vertical. The profile is 12 lines pinned
vertex by vertex (two plane distances each): 48 unknowns, 48 equations, 0 DOF.

**D5 — The slots are drawn once and repeated.** One slot per face (four faces of set A in one sketch, two of set B in
another), extruded as a cutter, then SolveSpace's "step translating" repeats each set 37 or 38 times
(`Sketch.translate`; the count includes the original and the group stores half the step, both pinned by
`utilities/selftest.py`). 224 slots cost two sketches, two extrudes and two repeat groups, and the pitch and count are
editable in the GUI.

**D6 — Each slot reaches 1 mm into the lane, in air.** So no cutter face lies in the wall's own face (the coplanar-face
rule of D3 in the 3 x 3 spec).

**D7 — Slot positions are symmetric about y = 0.** Set A has an odd count (37), so there is a slot at y = 0; set B has
one more, centred between. The end slots are 7.3 mm (A) and 4.35 mm (B) from the front and back walls.

---

## 6. Verification

`python3 cad/check_case.py` (under a minute) exports all three and measures the meshes. **All checks pass.**

* every sketch group of all three parts is 0 DOF, 0 redundant;
* each part is one watertight shell (tray 8 290 triangles, 793 031 mm^3; lid 4 714, 461 126; divider 44, 9 246);
* footprint, lanes, walls, lip, groove, clearances, heights, card space as in 1;
* all six lane faces' slots: positions to 0.001, 2.000 wide, floors at z = 48.4034, the wall top between slots at
  73.4034; each wall keeps 1.500 behind a slot and its full 5.000 between; the partitions are never thinner than 1.500
  scanning every 0.25 mm of y;
* lane faces smooth: 69.9992 across, z = 6 to 45, at slots and between;
* the lid: four walls hanging to 73.7034, 0.30 over the tray's, each one unbroken front to back;
* 12 domes and 12 dimples measure to their design; both ledges, 17 stations each;
* tray and lid overlap nowhere over 2 280 columns; the domes seat in the dimples with the same 0.025 / 0.091 apex gaps
  as the 3 x 3 case;
* **the divider, placed in lanes 1, 2 and 3 at the first, middle and last slots**: no overlap with the tray or lid, tabs
  0.200 clear in y, tips 0.300 short of the slot bottom, body 0.800 off each lane face, tab bottoms resting on the slot
  floors, tops flush, body 0.8 above the floor, 12.000 above the wall;
* a lane 1 divider at y = 0 and a lane 2 divider at y = +3 share the left partition, one tab on each face, without
  overlap;
* the committed STLs match a fresh export of their `.slvs`.

**Controls that must fail, and do:** a tray without slots fails the slot test 18 ways; slots on both faces at the same
positions cut the partitions through (thinnest 0.000); a divider with 3.6 mm tabs overlaps the tray by 25 mm; the same
divider against a tray without slots overlaps by 25 mm; a lid without dimples overlaps the domes by 2.54 mm; a tray
and a lid without the ledge fail the ledge test 17 ways each; the tray's STL checked as the lid's fails.

`utilities/slvs_check.py` on all three: one shell each; constraints survive a reload (tray 364 -> 364, lid 309 -> 309,
divider 39 -> 39); every sketch is restored after perturbing by up to 0.15 mm on all six seeds. At 0.3 mm one of five
seeds on the tray does not restore: the lip's 0.55 mm corner radius flipping to its other valid solution (the caveat in
`slvs_check.py`); `dof_report` says 0 DOF.

---

## 7. Open items and risks

* **The full tray is not printed.** The slots, tabs, stagger and fits were proved by the test print; what the full tray
  adds (four walls, 224 slots, the liners, the shell around them) is verified by mesh only.
* **Print time** should fall a lot against the first design's 24 h but is not measured.
* **Thin walls at slots.** 1.5 mm of wall behind a slot, 25 mm tall, in PLA, was fine in the test base; the full tray's
  partitions are about 233 mm long, supported at both ends, and the liners are backed by the outer wall.
* **Slot edges.** The top 25 mm of each lane face is notched every 6 mm (2 mm wide, 4 mm of smooth face between); the lane's
  top is otherwise open. A card edge cannot wedge in a 2 mm slot, but cards that rub the face are the thing to watch.
* **Only 6 mm steps.** A divider position is one of 37 or 38.
* **The fits are tight for FDM** (0.2 mm each side in the slot, 0.3 mm at the tip) but fitted in the test, which had a 0.4 mm
  body clearance. It is now 0.8 mm per side (more room between the body and the lane walls, the tabs 0.4 mm longer so they
  reach the same 3.2 into the wall): that change is **untested**. A different printer may need the fits opened further (`SLOT_W`, `TAB_REACH`, `BODY_CLEAR`).
* **STL exports are not reproducible** (`solvespace-cli export-mesh` varies run to run); the `.slvs` is, byte for byte.

---

## 8. How to rebuild

```bash
python3 cad/build_case.py     # writes the three .slvs
python3 cad/check_case.py     # verifies them
solvespace-cli export-mesh --chord-tol 0.02 --output deck_case_adjustable_bottom.stl deck_case_adjustable_bottom.slvs
```

Dimensions live in `cad/case_params.py`, almost all imported from `../mtg-deck-boxes/cad/ugp100_params.py`. The reusable
machinery (`slvs_shapes`, `slvs_write.translate`, `slvs_check`, `mesh_rays`, `mesh_features`...) is in `../utilities/`.
