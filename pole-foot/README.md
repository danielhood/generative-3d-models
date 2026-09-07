# Pole foot - 29 x 27 mm elliptical pole, PETG

Full design spec, verification method and build log: `pole_foot_spec.md`

`pole_foot.scad` is the source; both STLs are exported from it.

    openscad -o pole_foot.stl pole_foot.scad
    openscad -D 'part="fit_test"' -o fit_test_ring.stl pole_foot.scad

## Dimensions (as verified in the exported mesh)

| | |
|---|---|
| Overall | 32.80 x 30.80 x 44.00 mm |
| Socket depth | 40.00 mm |
| Floor under the pole | 4.00 mm |
| Side wall | 1.50 mm |
| Bore | 29.80 x 27.80 (0.40 mm uniform offset) |
| Ridge crest locus | on the nominal 29 x 27 ellipse |
| Ridges | 8 x 0.40 mm proud, Ø1.6 rounded crest, full 40 mm |
| Entry taper | ridges fade to the bore wall over the top 1.5 mm |
| Chamfers | 0.8 bottom outer, 0.6 top outer, 0.6 bore mouth, 0.6 socket floor |
| Material | 8.95 cm^3 |

## Fit

The bore is offset outward 0.4 mm and the ridges put 0.4 mm back, so the crests
land exactly on the nominal 29 x 27 ellipse - zero nominal clearance. The pole bears on eight
narrow lines instead of one loose wall, and a 0.4 mm PETG crest has enough give
to absorb print tolerance without splitting the wall.

Print `fit_test_ring.stl` first (10 mm, ~10 min). Then:

The crest locus is `offset(nominal, clearance - ridge_h)`, so with `ridge_h`
fixed at 0.4 the one knob is `clearance`:

- too tight -> raise `clearance` in 0.1 mm steps (0.5 -> crests 0.1 outside nominal)
- too loose -> lower it (0.3 -> crests 0.1 inside nominal, a firm press fit)

Re-export and the foot picks up the same change.

## Printing

Open end up, flat on the bed, no supports. Everything overhanging is a 45 deg
chamfer or a taper. 4+ perimeters is worth it here - at 1.5 mm the wall is
only ~4 lines at 0.4 mm, and the ridges want to be solid rather than
thin-wall gap fill. 100% infill for the 4 mm floor.

## Rendering previews

Always pass `--render`. Without it OpenSCAD exports the OpenCSG *preview*, which
approximates nested difference/hull/offset trees and will show defects that are
not in the STL:

    openscad --render -o preview_iso.png --imgsize=900,900 \
             --camera=0,0,22,62,0,25,155 --colorscheme=Tomorrow pole_foot.scad
