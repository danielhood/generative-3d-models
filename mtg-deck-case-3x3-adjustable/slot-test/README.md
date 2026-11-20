# Slot-and-tab divider: the test pieces

A first printed test of the adjustable case (square holes, dividers with arms) found the
dividers too tight and their arms flexible, and the base took about 24 h to print. The
dividers did slot in nicely by their **tabs alone** in the 3 mm slits. So the design
changes: **no holes and no arms**; the slits become vertical **slots** cut into the lane
faces, 25 mm deep from the wall top, at a 6 mm pitch; the divider's tabs grow to 25 mm
so they slide down the slots and hold the divider vertical.

These are the **test pieces** only: one divider and a short single-lane base, to prove
the fit before the full tray is changed. The full tray and lid in the folder above are
still the hole-and-arm design (PR #7) and are **not** changed here.

**Status: modelled and mesh-verified; not printed.**

| Path | What it is |
|---|---|
| `slot_divider.slvs` / `.stl` | the new divider: body, two 25 mm tabs, no arms |
| `slot_test_base.slvs` / `.stl` | a short base: the middle lane's two partition walls, 1 mm floor, 6 lane slots |
| `cad/slot_params.py` | every dimension; shared ones come from `../cad/case_params.py` |
| `cad/build_slot_test.py` | generates both `.slvs` |
| `cad/check_slot_test.py` | verifies both on the exported meshes, with controls that must fail |

```bash
python3 cad/build_slot_test.py    # writes both .slvs
python3 cad/check_slot_test.py    # verifies them (a few seconds); exits 0 only if everything passes
solvespace-cli export-mesh --chord-tol 0.02 --output slot_test_base.stl slot_test_base.slvs
```

## What changed from the holes-and-arms design

| | Holes and arms | Slots and tabs |
|---|---|---|
| holding the divider | arms in 60 mm deep 2 x 2 holes | 25 mm tabs in 25 mm deep slots |
| slot / slit | 3 mm deep, over a hole | **25 mm** deep, cut into the lane face, 3.5 into the wall |
| positions | every 4 mm | every **6 mm** |
| divider body, off each lane face | 0.2 | **0.4** |
| slot width, tab thickness | 2.0, 1.6 | **2.0, 1.6 (unchanged: they fitted)** |

### The two faces of a partition are staggered

A partition serves the lane on each side, and 3.5 mm slots from both faces of a 5 mm wall at
the same position would cut it clean through. So **lane 2's slots (set B) are 3 mm along from
lanes 1 and 3's (set A)**: the wall keeps 1.5 mm behind every slot, and a section through it
zig-zags. A side effect: dividers in neighbouring lanes can now be 3 mm apart (before, they
could not share a position at all).

## The test base

Two 5 mm partition walls 70 mm apart (the middle lane), 48 mm long, on a 1 mm floor; no
front or back wall. 73.4 mm tall, **as tall as the real walls**: the divider hangs about 44 mm
below its tabs, so a shorter base would need a shorter divider.

* **Lane-side slots (set B)**: six on each wall, at y = -15, -9, -3, +3, +9, +15. These are the
  six divider positions.
* **Outer-side slots (set A)**: seven on the outside face of each wall, at y = -18 ... +18.
  They are what lanes 1 and 3 would use, and they put slots in both faces of the wall so the
  1.5 mm webs are really tested. A divider stood against the outside of a wall engages
  them with one tab (its other tab is in air).

## The divider

A flat profile, pinned vertex by vertex and extruded 1.6 mm: a 69.2 mm wide body (0.4 mm off each
lane face), 12 mm above the wall top, ending 0.5 mm above the real tray's floor (4 mm), with a tab at
each top corner that reaches 3.2 mm into the wall, is 25 mm tall, has its top flush with the wall
top, and stops 0.3 mm short of the slot's bottom. It **hangs** on its tab bottoms, which rest on
the slots' floors. It prints **lying flat** (its model stands in the x-z plane; rotate it 90 degrees
about x in the slicer).

## Using the test

1. Print the base and one or more dividers.
2. Drop a divider into lane 2 from above, tabs over a pair of slots, until the tabs rest on
   the slot floors. It should drop in under its own weight, hang straight, and not bind between
   the walls.
3. Try all six positions; try a divider against the outside of a wall (the A slots); try a divider
   in lane 2 at y = +3 with another standing against the left wall's outside at y = 0.
4. Look at the walls at the slots: they are 1.5 mm thick at the thinnest.

Things to look at first: whether the tab is too tight or too loose in the 2.0 slot (0.2 mm each
side) and how much the divider can lean (a 25 mm tab in a 2.0 slot allows about 0.5 degrees);
whether 3.5 deep leaves the wall stiff enough; and print time against the old base.

## Verification

`check_slot_test.py` measures the exported meshes: every sketch fully constrained; one watertight
shell each; the base's size, floor and lane width (smooth below the slots); all slot positions,
widths, pitch, depth and floors on both faces of both walls; the stagger (the walls never thinner
than 1.5 mm, scanning every 0.25 mm); the divider's size, body, tabs and thickness; and **the
divider placed in each of lane 2's six slots and in the outer slots**: no overlap, tabs 0.2 mm clear
in y, tip 0.3 mm short of the slot's bottom, body 0.4 mm off both lane faces, resting on the slot
floors with the tops flush, body 3.5 mm above the floor. Two neighbours, one in lane 2 and one
standing against the wall outside, 3 mm apart, coexist. Committed STLs are checked against fresh
exports. Controls that must fail, and do: a base without slots, slots at the same positions on
both faces (cuts the wall through), a divider with tabs reaching 3.6 into the 3.5 slot, and an
STL of the wrong part.

## What comes next

If the test fits, the full tray changes the same way (slots instead of holes and slits, set A on
lanes 1 and 3's faces and set B on lane 2's, with the lid unchanged) and the check script, spec and
README are updated; `case_params.py` already holds the shared dimensions.
