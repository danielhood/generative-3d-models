"""Source insert -> verified 2D polygons -> a pattern `.scad` module.

The end-to-end pipeline that every coaster in this repo has needed, plus the
two checks that each of them got wrong at least once. Pairs with
`dxf_trace.py` (which parses and repairs) and
`projection_trace_recipe.scad` (which produces the DXF).

    from pattern_trace import trace_dxf, orientation_iou, emit_scad

    polys = trace_dxf("out.dxf", keep=lambda rmin, rmax: rmin < 39)
    orientation_iou(polys, source_tris, z=58.0, r_clip=41.3)   # CHECK IT
    emit_scad(polys, "pattern.scad", "my_pattern_native", header=...)

THE TWO CHECKS, AND WHY THEY ARE NOT OPTIONAL
---------------------------------------------
A `projection()` trace hands you closed loops and no interpretation. Every
coaster in this repo has been bitten by getting one of these wrong:

 1. WHAT DOES A LOOP MEAN -- artwork, or the hole around it?
    `sense_of()` asks the source mesh instead of guessing. Getting this
    backwards cost the Helm of Awe build a phantom "OpenSCAD quirk" and a
    pile of unnecessary scaffolding (coaster_yggdrasil_spec.md section 6,
    F1). It is one function call.

 2. WHICH WAY UP, AND FROM WHICH SIDE?
    `orientation_iou()` scores the trace against the source mesh's own face
    under all four in-plane flips. Nothing else catches this: every derived
    number -- area, radii, component counts, width distributions -- is
    identical under a mirror and every one of them will agree with every
    other while the part is upside down (coaster_tree_of_life_spec.md
    section 6, D6a; that trace scored 0.94 correct against 0.28 flipped).

Requires Pillow, via `raster.py`.
"""
import math

from dxf_trace import (drop_spurs, group_into_components, is_clean_walk,
                       parse_dxf_lines, polygon_area, trace_faces,
                       walk_polygon)


def component_polygons(edges, min_area=0.02):
    """One component's edge list -> its simple polygons, counter-clockwise.

    Tries `walk_polygon` first and falls back to `trace_faces` for the
    self-touching components that defeat it, so callers stop having to
    special-case `dxf_trace`'s documented C2 failure mode. Returns a list
    because a genuinely self-touching component yields more than one.

    Every polygon then goes through `drop_spurs`, which deletes zero-area
    excursions. Do not skip that on the grounds that they enclose no area:
    a polygon that touches itself at a point extrudes into a mesh that is
    correct in every respect except that it is not watertight, and both
    paths above can emit one (coasters/coaster_triskele_spec.md, E2)."""
    loop = walk_polygon(edges)
    if is_clean_walk(loop, edges):
        p = loop[:-1]
        return [drop_spurs(p if polygon_area(p) > 0 else p[::-1])]
    return [drop_spurs(f) for f in trace_faces(edges) if polygon_area(f) > min_area]


def trace_dxf(path, keep=None, min_area=0.02, verbose=True):
    """Parse a DXF, split into components, repair and orient them.

    `keep(rmin, rmax)` filters components by their radial extent from the
    origin -- the usual way to separate artwork from an insert's own frame,
    registration marks or (here) a border being replaced. Look at the radius
    histogram before choosing a threshold; there is normally an obvious gap.
    """
    comps = group_into_components(parse_dxf_lines(path))
    polys, clean, repaired, skipped = [], 0, 0, 0
    for edges in comps.values():
        pts = {p for e in edges for p in e}
        rs = [math.hypot(x, y) for x, y in pts]
        rmin, rmax = min(rs), max(rs)
        if keep and not keep(rmin, rmax):
            skipped += 1
            continue
        got = component_polygons(edges, min_area=min_area)
        if len(got) == 1 and is_clean_walk(walk_polygon(edges), edges):
            clean += 1
        else:
            repaired += 1
        polys.extend(got)
    if verbose:
        print("trace_dxf: %d components kept (%d clean, %d repaired), %d filtered out"
              % (clean + repaired, clean, repaired, skipped))
        print("           -> %d polygons, %d points, %.2f mm^2 total area"
              % (len(polys), sum(len(p) for p in polys),
                 sum(polygon_area(p) for p in polys)))
    return polys


def nested(polys):
    """Indices of polygons that lie inside another one.

    A hit means the trace picked up an island of material sitting inside a
    hole. Emitting it alongside the holes would fill that island in, so
    either drop it or subtract it separately -- do not ignore this."""
    def bb(p):
        xs = [q[0] for q in p]
        ys = [q[1] for q in p]
        return min(xs), max(xs), min(ys), max(ys)

    def inside(pt, poly):
        x, y = pt
        c = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
                c = not c
        return c

    boxes = [bb(p) for p in polys]
    out = []
    for i, p in enumerate(polys):
        for j, q in enumerate(polys):
            if i == j:
                continue
            if (boxes[i][0] >= boxes[j][0] and boxes[i][1] <= boxes[j][1]
                    and boxes[i][2] >= boxes[j][2] and boxes[i][3] <= boxes[j][3]
                    and inside(p[0], q)):
                out.append(i)
                break
    return out


def interior_point(poly):
    """A point guaranteed to lie inside a simple polygon.

    NOT the centroid. The area centroid of a long curved ribbon -- which is
    what most Celtic knotwork traces into -- routinely falls outside the
    ribbon, so a centroid-based test reports whatever happens to be next
    door. On the Tree of Life's 62 knot polygons the centroid test came back
    28/62, an even split that looks like "the trace mixes artwork and
    background" and is really just the centroid missing.

    Casts a scanline across the polygon at a height chosen to miss every
    vertex, and returns the midpoint of the first interior span."""
    ys = sorted({y for _, y in poly})
    if len(ys) < 2:
        return poly[0]
    mid = len(ys) // 2
    y = (ys[mid - 1] + ys[mid]) / 2.0 if len(ys) > 2 else (ys[0] + ys[1]) / 2.0
    xs = []
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xs.append(x1 + (x2 - x1) * (y - y1) / (y2 - y1))
    xs.sort()
    if len(xs) < 2:
        return poly[0]
    return ((xs[0] + xs[1]) / 2.0, y)


def sense_of(polys, source_tris, z, sample=None):
    """Is a traced polygon the ARTWORK, or the HOLE around it?

    Asks the source mesh whether there is material at a guaranteed-interior
    point of each polygon. Returns (n_on_material, n_total).

      n_on_material == 0  -> the polygons are cut-outs / negative space.
                             SUBTRACT them from a disc.
      n_on_material == n  -> the polygons are raised artwork.
                             They may be extruded directly.

    Expect near-unanimity. Anything in between means the trace really does
    mix both senses and needs separating before use -- treat it as a stop,
    not as a majority vote."""
    from mesh_query import is_solid_at
    hits = 0
    use = polys if sample is None else polys[:sample]
    for p in use:
        if abs(polygon_area(p)) < 1e-9:
            continue
        x, y = interior_point(p)
        if is_solid_at(source_tris, x, y, z):
            hits += 1
    return hits, len(use)


def orientation_iou(polys, source_tris, z, r_clip, ppm=16.0, scale=1.0,
                    verbose=True):
    """Score the trace against the source mesh's own face, all four flips.

    Returns [((flip_x, flip_y), iou), ...] best first. The winner should be
    far ahead -- on Insert-tree.stl it was 0.94 against 0.28 -- and it
    should be (False, False). If it is not, fix the ORIENTATION IN THE TRACE
    RECIPE, not by flipping signs downstream, so no hidden convention
    survives into the pattern file.

    `r_clip` clips both sides to a radius that contains the polygons you
    traced, so the score is not diluted by parts of the plate you excluded.
    A perfect score is not expected: thin features at finite raster
    resolution cost a few percent."""
    from raster import Grid, mask_from_polygons, mask_from_slice, AND, SUB, disc, iou

    g = Grid(ppm=ppm, half=r_clip * 1.05)
    plate = mask_from_slice(g, source_tris, z, scale=scale)
    ref = AND(SUB(disc(g, r_clip), plate), disc(g, r_clip))
    rows = []
    for fx in (False, True):
        for fy in (False, True):
            flipped = [[((-x if fx else x) * scale, (-y if fy else y) * scale)
                        for x, y in p] for p in polys]
            rows.append(((fx, fy), iou(mask_from_polygons(g, flipped), ref)))
    rows.sort(key=lambda r: -r[1])
    if verbose:
        print("orientation_iou (flip_x, flip_y) -> IoU against the source mesh:")
        for (fx, fy), v in rows:
            mark = "  <- best" if (fx, fy) == rows[0][0] else ""
            print("   (%-5s, %-5s)  %.4f%s" % (fx, fy, v, mark))
        if rows[0][0] != (False, False):
            print("   !! the trace is mirrored. Fix projection_trace_recipe.scad,")
            print("      not the extraction script.")
    return rows


def emit_scad(polys, path, module_name, header="", extra="", fmt="%.4f"):
    """Write the polygons as an OpenSCAD module of `polygon()` calls.

    `header` is prepended verbatim -- use it to say, in the file itself,
    whether these polygons are the artwork or its negative space, and how
    that was verified. Every pattern file in coasters/cad/ does, because
    the one that did not caused the most expensive mistake in this repo."""
    pt = "[" + fmt + "," + fmt + "]"
    body = "".join(
        "        polygon(points = [%s]);\n" % ", ".join(pt % (x, y) for x, y in p)
        for p in polys)
    with open(path, "w") as f:
        f.write(header)
        if extra:
            f.write(extra)
        f.write("module %s() {\n    union() {\n" % module_name)
        f.write(body)
        f.write("    }\n}\n")
    return path
