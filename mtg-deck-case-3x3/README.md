# 3 x 3 deck case

Parametric SolveSpace models of a case that holds nine of the Ultra Guard Pro
100+ deck box's card slots in a 3 x 3 grid: one tray, one lid. It is the
[single deck box](../mtg-deck-boxes/) multiplied, with a flat seam and snaps on
all four sides. **Printed in PLA; the lid's fit and snap are right as designed**
(see Print status). Design rationale, measurements and open items are in
[`deck_case_3x3_spec.md`](deck_case_3x3_spec.md); this file is how to *use* it.

| Path | What it is |
|---|---|
| `deck_case_3x3_bottom.slvs` / `.stl` | the tray: floor, outer walls, lip, 9 slots, 12 snap domes |
| `deck_case_3x3_top.slvs` / `.stl` | the lid: ceiling, groove, 12 dimples, front-to-back dividers |
| `cad/case_params.py` | every dimension of the case; most are imported from the single box |
| `cad/build_case.py` | generates both `.slvs` |
| `cad/check_case.py` | verifies both on the exported meshes, including a control that must fail |

Needs `solvespace-cli` on the path and Python 3 (standard library only). The
reusable machinery is in [`../utilities/`](../utilities/). Run the commands below
from this folder.

```bash
python3 cad/build_case.py     # writes both .slvs
python3 cad/check_case.py     # verifies them (~20 s); exits 0 only if everything passes
solvespace-cli export-mesh --chord-tol 0.02 --output deck_case_3x3_bottom.stl deck_case_3x3_bottom.slvs
```

Open each `.slvs` in the SolveSpace GUI once after a rebuild. The checks are this
repo's own, not SolveSpace's, and an earlier project passed every check and
still came up with "unsolvable constraint" messages there.

## The overall size

| | |
|---|---|
| exterior | 224.23 x 245.06 mm (bed limit 250 x 250; `case_params.py` asserts it) |
| tray | 73.55 tall: floor 4.0, walls to z = 67.55, lip to 73.55 |
| lid | 34.50 tall (z = 67.55 .. 102.05) |
| card space | 94.05 in every slot, as in the single box |
| slot | 69.9992 x 76.4992 (x by y), the single box's cavity exactly |

## Design assumptions (confirmed)

The brief left these open. They were stated in the spec and **confirmed as
correct on 2026-11-08**, after the first print. The variable is what to edit if
one ever needs to change.

| # | Question | Decision | Variable |
|---|---|---|---|
| A1 | Which height is "the back (tall) edge" of the single bottom | its bounding-box height **including the lip, 73.553**: the tray is that tall and its outer walls stop 6 mm lower, at the seam (z = 67.553). Reading it as the back wall's top (68.824) would put the seam 1.27 mm higher | `TRAY_H` |
| A2 | Total height | **102.05**, the single box's, so the same 94.05 of card space; the lid is the remaining 34.50 | `H_TOTAL` |
| A3 | How the two halves' dividers meet | tray dividers stop 0.15 under the lip-top plane and lid dividers start 0.15 over the groove roof: a 0.30 gap, so the lip and roof own the seam | `DIV_GAP` |
| A4 | Slot orientation | the single box's: 70 across x, 76.5 deep along y. (Swapped would be 243.7 x 225.6, which also fits) | `SLOT_X`, `SLOT_Y` |
| A5 | Dome height above the seam | the mean of the single box's two domes (2.505 and 2.809 above its sloping seam): **2.657** | `DOME_ABOVE_SEAM` |
| A6 | The mouth bevel | included, the single box's 0.6 x 0.6 lead-in | `MOUTH_CHAMFER` |
| A7 | A label | none | n/a (the single box's `relabel.py` does not apply here) |

## What each variable controls

In `cad/case_params.py`. "Imported" means it comes from the single box's
`mtg-deck-boxes/cad/ugp100_params.py`, so retuning the single box retunes the
case too; to change it for the case alone, assign a number here instead.

**The grid**

| Variable | Value | Controls |
|---|---|---|
| `N_COLS`, `N_ROWS` | 3, 3 | number of slots across x and along y. Everything else, the snap positions and the dividers included, follows. The `BED` assert stops a grid that does not fit |
| `INNER_T` | 3.0 | divider thickness |
| `SLOT_X`, `SLOT_Y` | imported | one slot's size, the single box's cavity. The critical dimensions for the cards |
| `PITCH_X`, `PITCH_Y` | derived | slot centre to slot centre: slot plus one divider |
| `IN_HX`, `IN_HY` | derived | half the interior of the whole case |
| `WALL_X`, `WALL_Y` | imported | outer wall thickness (4.1176 across x, 4.7812 across y) |
| `EXT_HX`, `EXT_HY` | derived | half the exterior; this is what has to stay under `BED` |
| `EXT_CORNER_R` | imported | the look of the exterior corners only |

**The seam, lip and groove (what holds the halves together)**

| Variable | Value | Controls |
|---|---|---|
| `LIP_H` | imported (6.0) | how far the lip rises above the seam, so how deep the lid engages |
| `LIP_HX`, `LIP_HY`, `LIP_CORNER_R` | derived / imported | the lip's outline (the single box's lip thickness, around the bigger perimeter) |
| `CLEAR_X`, `CLEAR_Y` | imported (0.0118, 0.0781) | lip-to-groove clearance per side. **The fit.** Opening these up loosens the lid |
| `GROOVE_HX`, `GROOVE_HY` | derived | the groove's outline: lip plus clearance |
| `MOUTH_CHAMFER`, `CHAMFER_OVER` | imported (0.6) | the lead-in bevel that lets the lid start without perfect alignment; 0 for none |

**Heights**

| Variable | Value | Controls |
|---|---|---|
| `TRAY_H` | 73.5534 | overall tray height including its lip (A1) |
| `Z_LIP` | `TRAY_H` | the lip top, which is also the groove roof |
| `Z_S` | `TRAY_H - LIP_H` | the seam, where the outer walls of the two halves meet |
| `FLOOR_T`, `CEIL_T`, `INT_H` | imported (4, 4, 94.05) | the floor, the ceiling and the card space between |
| `H_TOTAL` | 102.05 | overall assembled height (A2) |
| `Z_CEIL`, `LID_H` | derived | underside of the ceiling, and the lid's height |

**Dividers**

| Variable | Value | Controls |
|---|---|---|
| `DIV_GAP` | 0.15 | gap between each half's dividers and the seam planes (A3). Not cosmetic: a divider ending exactly in the lip-top or roof plane puts a coplanar face into SolveSpace's boolean, which it handles worst. Keep it above 0 |
| `DIV_TRAY_TOP`, `DIV_LID_BOTTOM` | derived | where the tray's dividers stop and the lid's start |
| `DIV_BASE_Z` | 1.0 | tray dividers start inside the floor, so they join it |
| `DIV_OVERLAP` | 1.0 | how far a divider runs into the wall (or ceiling) at its ends |
| `DIV_X`, `DIV_Y` | derived | divider positions. The tray has both; **the lid has `DIV_X` only** (front-to-back), so a stack that leans cannot be met by a left-right wall in the lid |

**The snap**

| Variable | Value | Controls |
|---|---|---|
| `BUMP_H`, `BUMP_SPHERE_R` | imported (0.7721) | dome height and sphere. Snap strength |
| `DENT_DEPTH`, `DENT_SPHERE_R` | imported (0.7857) | dimple depth and sphere. Change dome and dimple together: the dome seats with `CLEAR + (DENT_DEPTH - BUMP_H)` to spare |
| `DOME_ABOVE_SEAM`, `DOME_Z` | 2.657 | the snap's height on the lip (A5) |
| `SLOT_CENTRES_X`, `SLOT_CENTRES_Y` | derived | where the three domes on each side go: one centred on each slot |

`OVER` (2.0) is how far a cutter reaches past a part where it does not matter.

## Print status

**First print complete, PLA, 2026-11-08:** the lid locks "perfectly", neither
too tight nor too loose, with the same feel as prints of the single box's
original STLs (printed in both PLA and PETG). Original-STL and rebuilt
single-box halves also interchange: an original top on a new bottom, and the
reverse, both fit. So the 12-dome snap, the main risk recorded in the spec, did
not turn out to be a problem, and the front/back snap being slightly looser by
design (0.092 mm against 0.025 mm; spec section 5) was not reported as a problem.
PETG has not been tried for the case.

## Verification

`check_case.py` exports both parts through SolveSpace and measures the meshes:
every sketch fully constrained; one watertight shell each; footprint, slots,
walls, lip, clearances, heights and dividers against the figures above; all 12
domes and 12 dimples measured to their parameters, with no extras; the pair
overlapping nowhere over about 2,900 sampled columns; and a control, a lid built
without dimples, which must (and does) overlap by 2.54 mm so the engagement
test is known to be able to fail. `../utilities/slvs_check.py` additionally
checks that the constraints survive a reload and a perturbation.

`solvespace-cli export-mesh` is not reproducible: it gives different
triangulations on every run, so an STL can show as modified when nothing
changed. The `.slvs` rebuilds byte for byte. Regenerate an STL only when the
design changed.
