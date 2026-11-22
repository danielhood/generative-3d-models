# Adjustable deck case

A case with three lanes that run the full depth, and **movable dividers** that drop into
any lane at any of 37 or 38 positions, so a lane can be split into sections of any size in
6 mm steps. Parametric SolveSpace models of the tray, the lid and one divider.

It is the [3 x 3 case](../mtg-deck-case-3x3/) rethought: the outer shell (the single deck
box's walls, lip, groove, clearances and snap domes, and the 3 x 3 case's finger ledge) is
unchanged, because all of it printed well. Only the inside is new. Design rationale,
measurements and open items are in [`deck_case_adjustable_spec.md`](deck_case_adjustable_spec.md);
this file is how to *use* it.

**Status: modelled and mesh-verified. The divider and the slots were test-printed (a divider and a
short single-lane base) and fitted well; the full tray in this design has not been printed.** The shell is the
3 x 3 case's, which printed well with its lock and finger ledges. An earlier design (arms in 60 mm holes) was
printed, found too tight and too slow to print, and replaced; it is in [`archive/holes-and-arms/`](archive/holes-and-arms/).

| Path | What it is |
|---|---|
| `deck_case_adjustable_bottom.slvs` / `.stl` | the tray: floor, outer walls, lip, four 5 mm lane walls with slots, 12 snap domes, a finger ledge |
| `deck_case_adjustable_top.slvs` / `.stl` | the lid: ceiling, groove, 12 dimples, four 5 mm walls hanging to meet the tray's, a finger ledge |
| `deck_case_adjustable_divider.slvs` / `.stl` | **one** divider; print as many as you need (clone it in the slicer) |
| `deck_case_adjustable_bottom.3mf`, `deck_case_adjustable_top.3mf` | slicer projects for printing the tray and the lid |
| `cad/case_params.py` | every dimension; most are imported from the single box |
| `cad/build_case.py` | generates the three `.slvs` |
| `cad/check_case.py` | verifies all three on the exported meshes, with controls that must fail |
| `archive/` | the earlier holes-and-arms design, and the slot test that proved this one |

Needs `solvespace-cli` on the path and Python 3 (standard library only). The reusable machinery
is in [`../utilities/`](../utilities/). Run the commands below from this folder.

```bash
python3 cad/build_case.py     # writes the three .slvs
python3 cad/check_case.py     # verifies them (under a minute); exits 0 only if everything passes
solvespace-cli export-mesh --chord-tol 0.02 --output deck_case_adjustable_bottom.stl deck_case_adjustable_bottom.slvs
```

Open each `.slvs` in the SolveSpace GUI once after a rebuild: the checks are this repo's own, not SolveSpace's.

## How it works

```
 section across the case (looking front to back)

   outer wall | liner | lane 1 | wall | lane 2 | wall | lane 3 | liner | outer wall
   (unchanged)  5 mm    70 mm    5 mm   70 mm    5 mm   70 mm    5 mm   (unchanged)
```

* **Four 5 mm lane walls** run front to back: two partitions between the lanes, and a **liner** inside each
  outer wall. The outer walls carry the snap lip, which is only 1.85 mm thick and cannot hold a slot, so the
  liners sit inside it and the outer shell stays exactly as it was. The lid has four matching walls hanging down to
  meet them, with a 0.30 mm gap.
* **Slots.** Each lane face has vertical slots cut into it: 2 mm wide (along the lane), 3.5 mm into the wall,
  **25 mm deep from the wall top**, open at the top, every 6 mm. Below the slots every lane face is a plain flat wall.
* **Staggered.** A partition serves the lane on each side, and 3.5 mm slots from both faces of a 5 mm wall at the
  same position would cut it clean through. So lane 2's slots (set B) are **3 mm along** from lanes 1 and 3's (set A):
  the wall keeps 1.5 mm behind every slot, and a section through it zig-zags.
* **The divider** is a flat 1.6 mm plate, 68.4 mm wide (0.8 mm off each lane face), with a **25 mm tall tab** at each
  top corner. Each tab reaches 3.2 mm into the wall, so it stops 0.3 mm short of the slot's bottom, and slides down the
  slot; the divider **hangs on its tab bottoms**, with its top flush with the wall top, held vertical by the tabs in
  the slots. The body stands 12 mm above the wall top, to support the upper part of the cards, and ends 0.8 mm above
  the floor.

### Using it

* Lower a divider into a lane from above: line its tabs up over a pair of slots (the same slot number on the two walls
  either side of the lane) and let it drop until the tabs rest on the slot floors.
* **Positions.** Lanes 1 and 3 use set A: 37 slots at y = -108, -102, ..., +108 (one at y = 0). Lane 2 uses set B: 38
  slots at y = -111, -105, ..., +111. Slot 1 is nearest the front. Two dividers N slots apart are 6 x N mm apart, centre to
  centre.
* **Neighbours.** Dividers in neighbouring lanes are never at the same position (set B is 3 mm from set A, so they
  are always at least 3 mm apart); dividers in lanes 1 and 3 may share a position.
* The lid closes over the dividers: they stand 12.65 mm under its ceiling.

## The variables

All in `cad/case_params.py`. "Imported" means it comes from the single box's `mtg-deck-boxes/cad/ugp100_params.py`,
so retuning the single box retunes this case too.

**The lanes and the shell**

| Variable | Value | Controls |
|---|---|---|
| `N_LANES` | 3 | lanes across x. The snap positions follow |
| `LANE_W` | imported (69.9992) | one lane's width, the single box's cavity: the critical dimension for the cards |
| `WALL_T` | 5.0 | the four lane walls' thickness; with `SLOT_DEPTH` it sets what is left at a slot |
| `IN_HX`, `IN_HY` | derived | half the interior. `IN_HY` is the 3 x 3 case's depth, unchanged |
| `EXT_HX`, `EXT_HY` | derived | half the exterior; `2 * EXT_HX` is 238.23. `BED` asserts it fits |
| `WALL_X`, `WALL_Y`, `LIP_*`, `CLEAR_*`, `GROOVE_*`, `MOUTH_CHAMFER` | imported | the single box's outer wall, lip, groove and bevel, untouched |
| `LEDGE_*` | as the 3 x 3 case | the finger ledge (3 mm proud, 2 mm thick); see that README |
| `TRAY_H`, `Z_S`, `Z_LIP`, `H_TOTAL`, `Z_CEIL` | as the 3 x 3 case | heights |
| `DIV_GAP` | 0.15 | gap from each half's walls to the seam planes (a 0.30 mm gap where they meet). Keep above 0 |
| `WALL_TOP` | 73.40 | the tray's lane walls' top, and the tabs' top |
| `WALL_OVERLAP` | 1.0 | how far a wall runs into the front/back wall (and a liner into the outer wall) so it joins by overlap |

**The slots**

| Variable | Value | Controls |
|---|---|---|
| `SLOT_W` | 2.0 | the slot's width along the lane. The tab is 1.6, so 0.2 clear each side |
| `SLOT_DEPTH` | 3.5 | how far into the wall from the lane face; it leaves `WALL_T - SLOT_DEPTH` (1.5) behind the slot. The tab must stop short of it |
| `SLOT_H` | 25.0 | the slot's depth from the wall top, and the tab's height. A taller tab holds the divider more rigidly |
| `SLOT_PITCH` | 6.0 | the spacing of positions along the lane: the section-size step |
| `STAGGER` | derived (3.0) | how far set B is along from set A: half a pitch |
| `SKIN` | derived (1.5) | what is left of a wall behind a slot |
| `SLOT_FLOOR` | derived (48.40) | the slot's bottom, where a tab rests |
| `SLOT_MARGIN` | 2.0 | the end slots' distance from the front and back walls |
| `N_A`, `N_B`, `A_YS`, `B_YS` | derived (37, 38) | the number of slots in each set and where they are; symmetric about y = 0 |
| `SLOT_FACES` | derived | the six lane faces that carry slots, which way the wall lies from each, and which set |

**The divider**

| Variable | Value | Controls |
|---|---|---|
| `DIV_T` | 1.6 | plate and tab thickness (y). Unchanged from the first design: it fitted |
| `TAB_REACH` | 3.2 | how far a tab goes into the wall from the lane face; must be less than `SLOT_DEPTH` |
| `TAB_GAP` | derived (0.3) | how far a tab stops short of the slot's bottom |
| `TAB_H` | `SLOT_H` | the tab's height: as tall as the slot, so the divider hangs on it |
| `BODY_CLEAR` | 0.8 | the body is this much narrower than the lane, each side (0.2 in the first design, 0.4 in the slot test). The tabs lengthen with it, so they still reach `TAB_REACH` into the wall and the divider is the same width over its tabs |
| `DIV_ABOVE` | 12.0 | how far the body stands above the wall top |
| `DIV_FLOOR_CLEAR` | 0.8 | how far the body's bottom is above the floor. The divider hangs on its tabs, so this is the gap left under it; it is 0.5 in the archived slot test |

Asserts in `case_params.py` stop a divider that cannot fit: the tab must stop short of the slot's bottom and the
divider's top must clear the lid.

## Printing

Suggestions that follow from the geometry and the earlier prints. The test base and divider printed well; the full
tray in this design has not been printed.

* **The tray** is 238.23 x 245.26 mm: 11.8 mm under a 250 mm bed in x and **4.7 mm in y**, so, as with the 3 x 3
  case, a brim will not fit in y; check the slicer's usable area. Print it as it stands, the finger ledge flat on the
  bed. **The lid** upside down, its ledge on the bed.
* **The divider** prints **lying flat**: its model stands up (the plate in the x-z plane), so rotate it 90 degrees
  about x in the slicer. Clone it for as many as you want.
* **Print time.** The first design's 60 mm deep holes made the base take about 24 h. The slots here are 25 mm deep, so
  there is about 60% less depth of small feature to print (about 5,600 mm of slot depth against 13,700 of hole depth);
  how that translates into hours is for you to find out.
* **Fit is set by print tolerance.** The tab has 0.2 mm clear either side in the slot and 0.3 mm at the tip; the body
  is 0.8 mm off each lane face (0.4 in the test print, which fitted; the extra is for more clearance and is untested); if a different printer or material changes that, open them up
  (`SLOT_W`, `TAB_REACH`, `BODY_CLEAR`) and rebuild.
* **1.6 mm** is four lines at a 0.4 mm line width: the plate and tabs depend on it.

## Verification

`check_case.py` exports all three parts through SolveSpace and measures the meshes: every sketch fully constrained;
one watertight shell each; footprint, lanes, walls, lip, clearances and heights against the figures above; all six lane
faces' slots (positions, width, pitch, floors, wall top between slots), what each wall keeps behind a slot (1.5) and
between (5.0), and that the partitions are never thinner than 1.5 mm anywhere (scanned every 0.25 mm); that every lane
face is smooth below the slots; all 24 snap features; the ledges; tray and lid overlapping nowhere; and **the divider
placed in every lane** at the first, middle and last slots: no overlap with the tray or lid, tabs 0.2 mm clear in y and
0.3 mm short of the slot's bottom, body 0.8 mm off each lane face, tabs resting on the slot floors with their tops flush,
body 0.8 mm above the floor, 12.0 mm above the wall; and neighbours 3 mm apart, one tab on each face of a partition,
coexisting. The committed STLs are checked against a fresh export of their `.slvs`. Controls that must fail, and do: a
tray without slots, slots on both faces at the same positions (the partitions are cut through), a tray without the
ledge, a lid without dimples, a divider whose tabs reach 3.6 into the 3.5 slot, an STL of the wrong part.

`solvespace-cli export-mesh` is not reproducible, so an STL can differ from run to run; the `.slvs` rebuilds byte for
byte. Regenerate an STL only when the design changed.
