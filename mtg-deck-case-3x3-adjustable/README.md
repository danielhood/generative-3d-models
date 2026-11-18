# Adjustable deck case

A case with three lanes that run the full depth, and **movable dividers** that drop
into any lane at any of 57 positions, so a lane can be split into sections of any size
in 4 mm steps. Parametric SolveSpace models of the tray, the lid and one divider.

It is the [3 x 3 case](../mtg-deck-case-3x3/) rethought: the outer shell (the single
deck box's walls, lip, groove, clearances and snap domes, and the 3 x 3 case's finger
ledge) is unchanged, because all of it printed well. Only the inside is new. Design
rationale, measurements and open items are in
[`deck_case_adjustable_spec.md`](deck_case_adjustable_spec.md); this file is how to
*use* it.

**Status: modelled and mesh-verified; not printed.** The shell is the 3 x 3 case's, which
printed well in PLA with its lock and finger ledges; the lane walls, holes and dividers
have not been printed.

| Path | What it is |
|---|---|
| `deck_case_adjustable_bottom.slvs` / `.stl` | the tray: floor, outer walls, lip, four 5 mm lane walls with holes and slits, 12 snap domes, a finger ledge |
| `deck_case_adjustable_top.slvs` / `.stl` | the lid: ceiling, groove, 12 dimples, four 5 mm walls hanging to meet the tray's, a finger ledge |
| `deck_case_adjustable_divider.slvs` / `.stl` | **one** divider; print as many as you need (clone it in the slicer) |
| `cad/case_params.py` | every dimension; most are imported from the single box |
| `cad/build_case.py` | generates the three `.slvs` |
| `cad/check_case.py` | verifies all three on the exported meshes, with controls that must fail |

Needs `solvespace-cli` on the path and Python 3 (standard library only). The reusable
machinery is in [`../utilities/`](../utilities/). Run the commands below from this folder.

```bash
python3 cad/build_case.py     # writes the three .slvs
python3 cad/check_case.py     # verifies them (about a minute); exits 0 only if everything passes
solvespace-cli export-mesh --chord-tol 0.02 --output deck_case_adjustable_bottom.stl deck_case_adjustable_bottom.slvs
```

Open each `.slvs` in the SolveSpace GUI once after a rebuild: the checks are this
repo's own, not SolveSpace's.

## How it works

```
 section across the case (looking front to back)

   outer wall | liner | lane 1 | wall | lane 2 | wall | lane 3 | liner | outer wall
   (unchanged)  5 mm    70 mm    5 mm   70 mm    5 mm   70 mm    5 mm   (unchanged)
```

* **Four 5 mm lane walls** run front to back: two partitions between the lanes, and a
  **liner** inside each outer wall. The outer walls carry the snap lip, which is only
  1.85 mm thick and cannot hold a hole, so the liners sit inside it and the outer shell
  stays exactly as it was. The lid has four matching walls hanging down to meet them,
  with a 0.30 mm gap.
* **Holes.** Each lane wall has a column of 57 square holes, 2 x 2 mm, centred in the
  wall, at 4 mm pitch (y = -112 to +112), **60 mm deep** from the wall top. That leaves a
  1.5 mm skin each side of every hole, so the lane faces are smooth.
* **Slits.** Over each hole, the top 3 mm of the lane-side skin is cut away, 2 mm wide.
  A partition is slit on both sides, so a divider from either neighbouring lane can use
  its holes; a liner on its lane side only. Below the slits, every lane face is a
  plain flat wall.
* **The divider** is a flat 1.6 mm plate, 69.6 mm wide, with a **bridge** and an **arm** at
  each top corner. The arm (1.6 x 1.6, 58 mm long) goes down the hole; the bridge (3 mm
  tall) fills the slit and rests on the skin under it, so the divider **hangs** from its
  two bridges with its top flush with the wall top; and the **slot** between arm and
  body (1.8 mm: the 1.6 mm gap for the 1.5 mm skin, plus 0.2 mm of side play) straddles
  the skin. The body stands 12 mm above the wall top, to support the upper part of the
  cards, and ends 0.5 mm above the floor.

### Using it

* Lower a divider into a lane from above: line its arms up over a pair of holes (the
  same hole number in the two walls either side of the lane), and let it drop until the
  bridges rest on the slits' floors. The body stays vertical.
* Positions are the 57 holes, y = -112, -108, ... , +112 (hole 0 is nearest the front).
  Two dividers N holes apart are 4 x N mm apart, centre to centre.
* **Dividers in neighbouring lanes cannot be at the same hole**: they would share the
  partition's hole and the arms collide. One hole (4 mm) apart is fine. Lanes 1 and 3
  are not neighbours, so they can use the same hole.
* The lid closes over the dividers: they stand 12.65 mm under its ceiling.

## The variables

All in `cad/case_params.py`. "Imported" means it comes from the single box's
`mtg-deck-boxes/cad/ugp100_params.py`, so retuning the single box retunes this case too.

**The lanes and the shell**

| Variable | Value | Controls |
|---|---|---|
| `N_LANES` | 3 | lanes across x. The snap positions follow |
| `LANE_W` | imported (69.9992) | one lane's width, the single box's cavity: the critical dimension for the cards |
| `WALL_T` | 5.0 | the four lane walls' thickness; with `HOLE`, sets the skin |
| `IN_HX`, `IN_HY` | derived | half the interior. `IN_HY` is the 3 x 3 case's depth, unchanged |
| `EXT_HX`, `EXT_HY` | derived | half the exterior; `2 * EXT_HX` is 238.23. `BED` asserts it fits |
| `WALL_X`, `WALL_Y`, `LIP_*`, `CLEAR_*`, `GROOVE_*`, `MOUTH_CHAMFER` | imported | the single box's outer wall, lip, groove and bevel, untouched |
| `LEDGE_*` | as the 3 x 3 case | the finger ledge (3 mm proud, 2 mm thick); see that README |
| `TRAY_H`, `Z_S`, `Z_LIP`, `H_TOTAL`, `Z_CEIL` | as the 3 x 3 case | heights |
| `DIV_GAP` | 0.15 | gap from each half's walls to the seam planes (a 0.30 mm gap where they meet). Keep above 0 |
| `WALL_TOP` | 73.40 | the tray's lane walls' top, and the divider bridges' top |
| `WALL_OVERLAP` | 1.0 | how far a wall runs into the front/back wall (and a liner into the outer wall) so it joins by overlap |

**The holes and slits**

| Variable | Value | Controls |
|---|---|---|
| `HOLE` | 2.0 | the hole's width and depth into the wall (square) |
| `SKIN` | derived (1.5) | the wall either side of a hole |
| `HOLE_PITCH` | 4.0 | the spacing of positions along the lane: the section-size step |
| `HOLE_DEPTH` | 60.0 | how deep, from the wall top. Deeper holds a divider more rigidly |
| `SLIT_H`, `SLIT_W` | 3.0, 2.0 | the slit's depth below the wall top, and its width along y |
| `HOLE_MARGIN` | 2.0 | the end holes' distance from the front and back walls |
| `HOLE_N`, `HOLE_Y0`, `HOLE_YS` | derived (57, -112) | the number of holes and where they are; symmetric about y = 0 |

**The divider**

| Variable | Value | Controls |
|---|---|---|
| `DIV_T` | 1.6 | plate thickness (y) |
| `ARM_W` | 1.6 | arm width; its thickness is `DIV_T` (one extrude) |
| `ARM_LEN` | 58.0 | arm length from the wall top; must be shorter than `HOLE_DEPTH` |
| `BRIDGE_H` | `SLIT_H` | bridge height; it fills the slit exactly, so the top is flush and it hangs |
| `SKIN_GAP` | 1.6 | lane face to the arm's lane-side face: holds the 1.5 mm skin (0.1 play) |
| `BODY_CLEAR` | 0.2 | the body is this much narrower than the lane, each side |
| `DIV_ABOVE` | 12.0 | how far the body stands above the wall top |
| `DIV_FLOOR_CLEAR` | 0.5 | how far the body's bottom is above the floor |

Asserts in `case_params.py` stop a divider that cannot fit: the arm must clear the skin
and stay inside the hole, and the divider's top must clear the lid.

## Printing

Suggestions that follow from the geometry. **None has been tried.**

* **The tray** is 238.23 x 245.26 mm: 11.8 mm under a 250 mm bed in x and **4.7 mm in
  y**, so, as with the 3 x 3 case, a brim will not fit in y; check the slicer's usable
  area. Print it as it stands, the finger ledge flat on the bed. **The lid** upside down,
  its ledge on the bed.
* **The divider** prints **lying flat**: its model stands up (the plate in the x-z plane),
  so rotate it 90 degrees about x in the slicer. Its arms and bridges then lie in the
  print plane, which is the strong direction. Clone it for as many as you want.
* **Fit is set by print tolerance.** The arm has 0.2 mm of clearance either side in a
  2 mm hole and 0.1 mm beside the skin; that is tight for FDM. If dividers bind, open the
  clearances up (`SKIN_GAP`, `ARM_W`, `BODY_CLEAR`) and rebuild; if they rattle, close them.
  The first thing to look at is whether a divider drops in and hangs straight.
* **1.6 mm** is four lines at a 0.4 mm line width: the plate, arms and bridges depend on it.
* **The holes** are 60 mm tall square channels, open at the top, so print vertically with
  no supports needed. The 456 holes and slits add a lot of small perimeters; expect a
  slower print than the 3 x 3 tray.

## Verification

`check_case.py` exports all three parts through SolveSpace and measures the meshes: every
sketch fully constrained; one watertight shell each; footprint, lanes, walls, lip,
clearances and heights against the figures above; all 57 holes in each of the four walls
(position, width, depth) and every slit (which skins, how deep); that every lane face is
smooth below the slits; all 24 snap features; the ledges; tray and lid overlapping
nowhere; and **the divider placed in every lane** at the first, middle and last holes:
no overlap with the tray or lid, 0.2 mm clear in y, 0.1 / 0.3 mm in x, body 0.2 mm off
each lane face, the bridge resting on the slit floor with its top flush, 12.0 mm above the
wall, and the neighbours rule (collides at the same hole, clear one hole apart). The
committed STLs are checked against a fresh export of their `.slvs`. Controls that must
fail, and do: a tray without holes, a tray without the ledge, a lid without dimples, a
divider whose slot cannot take the skin, an STL of the wrong part.

`solvespace-cli export-mesh` is not reproducible, so an STL can differ from run to run;
the `.slvs` rebuilds byte for byte. Regenerate an STL only when the design changed.
