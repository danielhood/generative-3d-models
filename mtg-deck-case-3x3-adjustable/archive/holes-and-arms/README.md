# Adjustable case, first design: dividers with arms in square holes (archived)

**Superseded on 2026-11-22 by the slot-and-tab design in the folder above.** Kept for reference: the
models, the scripts that generate and check them, and the design spec as they were in PR #7 before the change.

## What it was

A deck case with three lanes running the full depth, and movable dividers that hang in the lane
walls. The shell (single box walls, lip, groove, snap domes, finger ledge) is the 3 x 3 case's. Inside:
four 5 mm lane walls (two partitions, two liners inside the outer walls), each with a column of
**57 square holes, 2 x 2 mm, 4 mm apart, 60 mm deep**, centred in the wall, and a **3 mm slit** through the
lane-side skin over each hole. The divider was a flat 1.6 mm plate, 69.6 mm wide, with a **bridge** (3 mm tall,
filling the slit) and a **58 mm arm** at each top corner: the arm went down the hole, the bridge rested on the
skin under the slit, and a 1.8 mm slot between arm and body straddled the 1.5 mm skin. The body stood 12 mm
above the walls. Dividers in neighbouring lanes could not use the same hole (they share it).

| Dimension | Value |
|---|---|
| case | 238.23 x 245.26 mm (with the 3 mm finger ledge) |
| hole | 2.0 x 2.0, 60 deep, 4 mm pitch, 57 per wall |
| slit | top 3 mm of the lane-side skin, 2 mm wide |
| divider body | 69.6 wide, 0.2 off each lane face |
| arm / bridge | 1.6 wide, 58 long / 3 tall |

## What the printed test found

A divider and the base were printed (2026-11-19):

* the arms had to be **pushed into the holes with some force**, and were **quite flexible** at 1.6 mm;
* the divider **body could bind** between the walls;
* the base took about **24 hours** to print, because of the 60 mm holes over most of the height of the walls;
* with the arms removed and the tabs (bridges) kept, the dividers **slotted in nicely** between the slits.

So the arms and holes were dropped: the slits became 25 mm deep slots cut into the lane faces, the tabs grew to
25 mm, the pitch went from 4 to 6 mm, the body came 0.4 mm off each lane face, and the two faces of a partition
were staggered by 3 mm so a 5 mm wall keeps 1.5 mm behind every slot. The slot width (2.0) and the tab thickness
(1.6) were kept: they fitted. See [`../slot-test/`](../slot-test/) and the current design.

## Files

| Path | What it is |
|---|---|
| `deck_case_adjustable_bottom.slvs` / `.stl` | the tray |
| `deck_case_adjustable_top.slvs` / `.stl` | the lid (the current lid is the same geometry and is unchanged) |
| `deck_case_adjustable_divider.slvs` / `.stl` | the divider with arms |
| `deck_case_adjustable_spec.md` | the design spec as it was |
| `cad/case_params.py`, `build_case.py`, `check_case.py` | the generator and the checks |

## Rebuilding it

The scripts were moved here with their paths corrected, and still work (the rebuild is byte for byte the same as
the archived `.slvs`, and the checks pass). From this folder:

```bash
python3 cad/build_case.py     # rewrites the three .slvs here
python3 cad/check_case.py     # about a minute; exits 0 only if everything passes
```

The copy in git history before this archive is commit `0118362`.
