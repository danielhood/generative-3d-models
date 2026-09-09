"""Will this flat-extruded part actually survive being printed?

    python3 printability.py part.stl [z] [px_per_mm]

    from printability import report, widths, erosion_connectivity
    report("coaster.stl", z=3.0)

Two questions, both answered against the exported mesh's own top face --
no OpenSCAD, no slicer, no source polygons:

  1. HOW THIN DOES THE MATERIAL GET, and how thin do the holes get?
     Measured as 2 x the distance-to-edge at the ridge (local maxima) of
     the distance field, which is the width of a ribbon at its waist rather
     than the distance from some arbitrary interior point.

  2. DOES IT STAY IN ONE PIECE?  `erosion_connectivity` shrinks the part by
     a series of radii and counts connected components. This is the test
     that predicts a real failure, and it is NOT the same question as
     `mesh_check.py`'s shell count: a mesh can be a single watertight shell
     in CAD and still come off the bed in pieces, because CAD is happy to
     join two lobes at a cusp of literally zero width and call it connected.
     Eroding by r asks "is it still one piece once every feature thinner
     than 2r is gone", which is what a 0.4 mm nozzle is really doing to you.

Read the two together. Percentiles alone are reassuring and incomplete --
a part can post a healthy median width and still hang on three threads.

WORKED EXAMPLE (coasters/coaster_tree_of_life_spec.md, sections 3 and 7).
The Insert-tree.stl source artwork, scaled to a 100 mm coaster, measures a
0.36 mm median ribbon in its border. Run through this file it fails plainly:

    erode 0.20 mm ->  135 pieces | main 2841.3 mm^2 | shed 2224.59 mm^2

that shed piece being the entire rim, r 38.8..50.0, falling off the middle
of the coaster -- exactly the failure that had been reported from a real
print, and invisible to every other check in this folder. The rebuilt part
holds one piece through 0.30 mm and sheds 0.12 mm^2 of dust at 0.40 mm.

INTERPRETING THE EROSION LADDER, roughly, for a 0.4 mm nozzle:
    survives 0.20 mm  -- minimum ~0.4 mm connections. One extrusion. Fragile.
    survives 0.30 mm  -- minimum ~0.6 mm. Acceptable.
    survives 0.40 mm  -- minimum ~0.8 mm, two perimeters. Comfortable.
A few specks shedding is fine; watch the `largest loose` column, because
that is where "a bit of dust" and "the rim fell off" differ.

A NOTE ON `min`. A reported minimum that halves when you double px_per_mm
is a cusp -- two holes meeting at a point -- not a ribbon, and it is a
raster artefact rather than a feature. Re-measure at two resolutions before
believing one, and trust the erosion ladder over `min` for anything
structural.

Requires Pillow, via raster.py.
"""
import math
import sys

from edt import edt2d
from raster import (Grid, SUB, area, component_order, components, disc,
                    mask_from_slice)
from stl_io import load_stl


def _masks(path, z, g):
    mat = mask_from_slice(g, load_stl(path), z)
    cut = SUB(disc(g, g.half), mat)
    return mat, cut


def ridge_widths(g, mask, keep=None):
    """Widths (mm) at the ridge of the distance field: 2 x distance-to-edge
    at every local maximum. `keep(i)` optionally restricts to a region."""
    sq = edt2d(list(mask), g.w, g.h)
    out = []
    w, h = g.w, g.h
    for y in range(1, h - 1):
        b = y * w
        for x in range(1, w - 1):
            i = b + x
            if not mask[i] or (keep and not keep(i)):
                continue
            d0 = sq[i]
            if d0 >= sq[i - 1] and d0 >= sq[i + 1] and d0 >= sq[i - w] and d0 >= sq[i + w]:
                out.append(2 * math.sqrt(d0) / g.ppm)
    out.sort()
    return out


def _pct(ws, p):
    return ws[min(len(ws) - 1, int(len(ws) * p / 100))]


def widths(path, z, ppm=20.0, half=50.0, r_range=None, verbose=True):
    """Ridge-width distributions for material and for holes, in mm."""
    g = Grid(ppm=ppm, half=half)
    mat, cut = _masks(path, z, g)
    keep = None
    if r_range:
        lo, hi = r_range
        rad = g.radius_field()
        keep = lambda i: lo <= rad[i] <= hi
    res = {"material": ridge_widths(g, mat, keep),
           "cut": ridge_widths(g, cut, keep)}
    if verbose:
        for name in ("material", "cut"):
            ws = res[name]
            if not ws:
                print("   %-9s none" % name)
                continue
            print("   %-9s min %.2f  p1 %.2f  p5 %.2f  p25 %.2f  p50 %.2f  max %.2f  (n=%d)"
                  % (name, ws[0], _pct(ws, 1), _pct(ws, 5), _pct(ws, 25),
                     _pct(ws, 50), ws[-1], len(ws)))
        print("   NOTE: a `min` that halves when you double px_per_mm is a cusp --")
        print("         two holes meeting at a point -- not a ribbon. Trust the")
        print("         erosion ladder below over `min` for anything structural.")
    return res


def erosion_connectivity(path, z, ppm=25.0, half=50.0,
                         radii=(0.0, 0.10, 0.20, 0.30, 0.40, 0.50),
                         verbose=True):
    """Erode by each radius; report piece count, main-body area, shed area."""
    g = Grid(ppm=ppm, half=half)
    mat, _ = _masks(path, z, g)
    sq = edt2d(list(mat), g.w, g.h)
    mm2 = 1.0 / (g.ppm * g.ppm)
    rows = []
    for r in radii:
        rr = (r * g.ppm) ** 2
        er = bytearray(1 if sq[i] > rr else 0 for i in range(g.n))
        _, sizes = components(er, g.w, g.h)
        order = component_order(sizes)
        if not order:
            rows.append((r, 0, 0.0, 0.0, 0.0))
            if verbose:
                print("   erode %.2f mm -> nothing left" % r)
            continue
        main = sizes[order[0]] * mm2
        shed = sum(sizes[i] for i in order[1:]) * mm2
        big = sizes[order[1]] * mm2 if len(order) > 1 else 0.0
        rows.append((r, len(order), main, shed, big))
        if verbose:
            print("   erode %.2f mm -> %4d pieces | main %7.1f mm^2 | shed %7.2f mm^2 | largest loose %.3f mm^2"
                  % (r, len(order), main, shed, big))
    return rows


def mask_report(g, mat, label="mask", radii=(0.0, 0.10, 0.20, 0.30, 0.40)):
    """The same erosion ladder on a mask you already have, rather than an
    STL -- for measuring a *source* insert before committing to it, which
    is the check that would have caught the Tree of Life border on day one.
    """
    sq = edt2d(list(mat), g.w, g.h)
    mm2 = 1.0 / (g.ppm * g.ppm)
    print("%s   material %.1f mm^2" % (label, area(g, mat)))
    for r in radii:
        rr = (r * g.ppm) ** 2
        er = bytearray(1 if sq[i] > rr else 0 for i in range(g.n))
        _, sizes = components(er, g.w, g.h)
        order = component_order(sizes)
        if not order:
            continue
        main = sizes[order[0]] * mm2
        shed = sum(sizes[i] for i in order[1:]) * mm2
        big = sizes[order[1]] * mm2 if len(order) > 1 else 0.0
        print("   erode %.2f mm -> %4d pieces | main %7.1f mm^2 | shed %7.2f mm^2 | largest loose %.3f mm^2"
              % (r, len(order), main, shed, big))


def report(path, z, ppm=20.0, half=50.0):
    print("file  %s   (top face z=%.2f)" % (path, z))
    widths(path, z, ppm=ppm, half=half)
    print()
    erosion_connectivity(path, z, half=half)


if __name__ == "__main__":
    p = sys.argv[1]
    z = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
    ppm = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
    report(p, z, ppm=ppm)
