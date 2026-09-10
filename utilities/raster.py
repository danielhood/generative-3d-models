"""Binary masks over a square mm grid: build them, combine them, measure
them. The shared substrate under `printability.py` and `pattern_trace.py`.

    from raster import Grid, mask_from_slice, mask_from_polygons, disc, NOT, AND, SUB

    g    = Grid(ppm=20.0, half=50.0)      # 0.05 mm/px over a 100 mm square
    mat  = mask_from_slice(g, tris, z=3.0)
    cuts = SUB(disc(g, 50.0), mat)
    print(area(g, cuts), "mm^2")

A mask is a plain `bytearray` of 0/1, one byte per pixel, row-major. Not a
PIL image, deliberately -- see the warning below.

WHY NOT ImageChops
------------------
`ImageChops.invert()` on a mode-"1" PIL image does not do what it looks like
it does. Composing masks with it produced a material mask covering
2045 mm^2 of a 7854 mm^2 disc for a design that is about 80 percent solid,
and did it silently (coasters/coaster_tree_of_life_spec.md section 6, D8).
PIL is used here only to *fill polygons*; every boolean operation is
explicit bytearray logic in this file.

The cheap check that catches this class of bug immediately, and is worth
writing every time you split a region in two:

    partition_error(g, disc(g, 50), [mat, cuts])   # mm^2 unaccounted for

Do not expect zero, and do not assert on a tight tolerance. Masks built two
different ways -- one by filling mesh triangles through PIL, one computed
analytically -- disagree along their shared boundary by a fraction of a
pixel, so the residual scales with the boundary's length: roughly
perimeter / ppm in mm^2 (about 16 mm^2 for a 100 mm disc at 20 px/mm).
`partition_error` reports that budget alongside the number. What it is for
is the other magnitude entirely -- the inversion bug above was off by
thousands of mm^2, not by a rim's worth of pixels.

RESOLUTION, AND WHAT `min` MEANS
--------------------------------
Everything here is quantised to 1/ppm mm. That is fine for widths and areas
and NOT fine for minima: a measured minimum width that halves when you
double `ppm` is not a feature of the geometry, it is a cusp (two holes
meeting at a point) being rendered one pixel wide. Re-measure at two
resolutions before believing any minimum. `printability.py` says the same
thing where it prints one.

Requires Pillow (for polygon fill only), like `mesh_rasterize.py`.
"""
import math

from mesh_slice import flat_triangles_at_z


class Grid:
    """A square raster covering [-half, +half] mm in both axes.

    `half` is a half-width in mm, so a 100 mm coaster wants half=50."""

    def __init__(self, ppm=20.0, half=50.0):
        self.ppm = float(ppm)
        self.half = float(half)
        self.w = self.h = int(2 * self.half * self.ppm)
        self.n = self.w * self.h

    def to_px(self, pt):
        return (self.w / 2 + pt[0] * self.ppm, self.h / 2 - pt[1] * self.ppm)

    def to_mm(self, i):
        return ((i % self.w - self.w / 2) / self.ppm,
                (self.h / 2 - i // self.w) / self.ppm)

    def radius_field(self):
        """Radius in mm of every cell. Cache it -- it is not cheap and most
        callers want it more than once."""
        return [math.hypot(*self.to_mm(i)) for i in range(self.n)]

    def __repr__(self):
        return "Grid(ppm=%g, half=%g) -> %dx%d px, %.4f mm/px" % (
            self.ppm, self.half, self.w, self.h, 1.0 / self.ppm)


def blank(g):
    return bytearray(g.n)


def _fill(g, polys):
    from PIL import Image, ImageDraw
    im = Image.new("1", (g.w, g.h), 0)
    d = ImageDraw.Draw(im)
    for p in polys:
        if len(p) >= 3:
            d.polygon([g.to_px(q) for q in p], fill=1)
    return bytearray(1 if v else 0 for v in im.get_flattened_data())


def mask_from_slice(g, tris, z, scale=1.0):
    """Fill the flat face of a mesh at height `z`. `scale` is applied about
    the origin first, so a native-scale source can be rasterized straight at
    part scale."""
    flat = flat_triangles_at_z(tris, z)
    if scale != 1.0:
        flat = [tuple((p[0] * scale, p[1] * scale) for p in t) for t in flat]
    return _fill(g, flat)


def mask_from_polygons(g, polys, scale=1.0):
    if scale != 1.0:
        polys = [[(x * scale, y * scale) for x, y in p] for p in polys]
    return _fill(g, polys)


def disc(g, r):
    """Analytic, NOT a drawn ellipse.

    PIL's `ellipse` is inscribed in its bounding box and lands about half a
    pixel inside the true circle, which does not agree with the same circle
    arriving as mesh triangles through `mask_from_slice`. Subtracting one
    from the other then leaves a one-pixel ring of phantom "hole" all the
    way around the part -- harmless to areas, but it injects a thousand
    spurious hairline measurements into any width statistic taken over the
    result. Computing membership directly keeps `disc` consistent with
    `to_px`/`to_mm` and with the mesh."""
    rr = (r * g.ppm) ** 2
    out = bytearray(g.n)
    cx = g.w / 2.0
    cy = g.h / 2.0
    for i in range(g.n):
        dx = (i % g.w) - cx
        dy = (i // g.w) - cy
        if dx * dx + dy * dy <= rr:
            out[i] = 1
    return out


def annulus(g, r_in, r_out):
    return SUB(disc(g, r_out), disc(g, r_in))


def NOT(a):
    return bytearray(0 if v else 1 for v in a)


def AND(a, b):
    return bytearray(1 if (a[i] and b[i]) else 0 for i in range(len(a)))


def OR(a, b):
    return bytearray(1 if (a[i] or b[i]) else 0 for i in range(len(a)))


def SUB(a, b):
    """a minus b."""
    return bytearray(1 if (a[i] and not b[i]) else 0 for i in range(len(a)))


def area(g, mask):
    """mm^2."""
    return sum(mask) / (g.ppm * g.ppm)


def partition_error(g, whole, parts, perimeter_mm=None, verbose=True):
    """mm^2 of `whole` not accounted for by `parts` (plus any overlap).

    Sanity check for mask algebra. Returns (error_mm2, budget_mm2), where
    the budget is the boundary-quantisation residual you should expect
    anyway -- see the module docstring. An error inside the budget means
    the split is fine; an error many times larger means a logic bug, which
    is the case this exists to catch."""
    n = len(whole)
    covered = bytearray(n)
    overlap = 0
    for m in parts:
        for i in range(n):
            if m[i]:
                if covered[i]:
                    overlap += 1
                covered[i] = 1
    missing = sum(1 for i in range(n) if whole[i] and not covered[i])
    extra = sum(1 for i in range(n) if covered[i] and not whole[i])
    err = (missing + extra + overlap) / (g.ppm * g.ppm)
    if perimeter_mm is None:
        perimeter_mm = 2 * math.pi * g.half
    budget = perimeter_mm / g.ppm
    if verbose:
        verdict = "OK" if err <= budget else "!! LOGIC BUG -- %.0fx the boundary budget" % (err / budget if budget else 0)
        print("partition_error %.2f mm^2 (boundary budget ~%.1f mm^2)  %s"
              % (err, budget, verdict))
    return err, budget


def iou(a, b):
    """Intersection over union. The orientation test: see pattern_trace."""
    inter = union = 0
    for i in range(len(a)):
        if a[i] or b[i]:
            union += 1
            if a[i] and b[i]:
                inter += 1
    return inter / union if union else 0.0


def components(mask, w, h):
    """4-connected labelling. Returns (labels, sizes) with sizes[0] unused,
    so component k has sizes[k] pixels. Iterative -- these rasters are
    millions of cells and recursion will not survive them."""
    lab = [0] * (w * h)
    cur = 0
    sizes = [0]
    for s in range(w * h):
        if mask[s] and lab[s] == 0:
            cur += 1
            n = 0
            stack = [s]
            lab[s] = cur
            while stack:
                p = stack.pop()
                n += 1
                x, y = p % w, p // w
                for q, ok in ((p - 1, x > 0), (p + 1, x < w - 1),
                              (p - w, y > 0), (p + w, y < h - 1)):
                    if ok and mask[q] and not lab[q]:
                        lab[q] = cur
                        stack.append(q)
            sizes.append(n)
    return lab, sizes


def component_order(sizes):
    """Component labels, largest first."""
    return sorted(range(1, len(sizes)), key=lambda i: -sizes[i])


def save(g, mask, path, fg=(25, 90, 70), bg=(255, 255, 255), size=None):
    """Write a mask to a PNG. The ground-truth look, same spirit as
    mesh_rasterize.py -- when a number surprises you, render it."""
    from PIL import Image
    im = Image.new("RGB", (g.w, g.h), bg)
    px = im.load()
    for i in range(g.n):
        if mask[i]:
            px[i % g.w, i // g.w] = fg
    if size:
        im = im.resize((size, size), Image.LANCZOS)
    im.save(path)
    return path


def save_width_map(g, mask, path, bands=((0.6, (230, 40, 40)),
                                         (0.9, (240, 150, 40)),
                                         (1.2, (230, 220, 70))),
                   ok=(70, 80, 95), bg=(16, 16, 20), size=None):
    """Colour every cell by its local width (2 x distance to the nearest
    hole). Reads at a glance: solid red means a region that is thin
    everywhere, which is what an unprintable band looks like."""
    from PIL import Image

    from edt import edt2d
    sq = edt2d(list(mask), g.w, g.h)
    im = Image.new("RGB", (g.w, g.h), bg)
    px = im.load()
    for i in range(g.n):
        if not mask[i]:
            continue
        wdt = 2 * math.sqrt(sq[i]) / g.ppm
        col = ok
        for lim, c in bands:
            if wdt < lim:
                col = c
                break
        px[i % g.w, i // g.w] = col
    if size:
        im = im.resize((size, size), Image.LANCZOS)
    im.save(path)
    return path
