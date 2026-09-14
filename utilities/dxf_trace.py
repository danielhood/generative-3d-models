"""Extract exact 2D artwork (as ordered polygons) from a relief/engraving on
an STL -- including one that's non-manifold and can't be booleaned directly.

Full worked example: coasters/coaster_helm_of_awe_spec.md sections 3 and 6
(C1, C2). Short version of the problem this solves: you have a source STL
with a decorative relief (raised lines, logos, engraved text -- anything
that's fundamentally 2D artwork extruded a bit) that you want to reuse at a
different scale/depth/crop, but the file has a manifold defect (a self-
touching vertex, a small crack) that makes `intersection()`/`difference()`
against it in OpenSCAD unreliable -- it can silently leak through the
defect instead of stopping at a clean boundary (see C1: a crop radius kept
tracking whatever value was given instead of stopping at the shape's true
edge, only bounded once it reached unrelated geometry far away).

The fix is to never ask a 3D boolean to resolve the defective region at
all. Recipe:

    1. In OpenSCAD, flatten the relief to a 2D outline and export to DXF:

        projection(cut=false)
            rotate([90,0,0])       // reorient so the relief's face plane becomes XY
                import("source.stl");

       then `openscad --render -o out.dxf that.scad`. `projection()` only
       needs a valid *surface*, not a closed volume, so it works straight
       through the kind of defect that breaks `intersection()`/`difference()`.

    2. Parse the DXF's LINE entities (parse_dxf_lines, below).

    3. Group them into connected components by shared endpoints
       (group_into_components) -- in complex artwork this naturally
       separates unrelated sub-shapes (e.g. the coaster project's emblem
       vs. its square frame's corner brackets, which were never meant to
       touch) without needing to know the artwork's structure up front.

    4. Walk each component into an ordered polygon (walk_polygon) that
       OpenSCAD's `polygon()` can consume directly.

    5. Classify components by distance from a center point
       (classify_by_radius) to decide what to keep vs. exclude -- e.g.
       "everything within 45mm of center is the emblem; everything beyond
       is the other project's registration marks."

Known failure mode (C2): a component whose source geometry has a
self-touching vertex (itself a symptom of the same manifold defect) will
not walk into a clean simple loop -- `walk_polygon` will return a
suspiciously short list. Detect this (`len(loop) far less than len(edges)`)
and don't trust that polygon; either drop it, or -- if the design has
rotational/mirror symmetry, as ours did -- substitute a rotated copy of a
different, clean instance of the same feature instead of trying to repair
the broken one directly.
"""
import math
from collections import defaultdict


def parse_dxf_lines(path):
    """Returns a list of ((x1,y1), (x2,y2)) segments from a DXF's LINE entities."""
    lines = open(path).read().split("\n")
    segments = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == "LINE":
            j = i + 1
            vals = {}
            while j < len(lines) - 1:
                code = lines[j].strip()
                if code == "0":
                    break
                vals[code] = float(lines[j + 1].strip())
                j += 2
            if all(k in vals for k in ("10", "20", "11", "21")):
                segments.append(((vals["10"], vals["20"]), (vals["11"], vals["21"])))
            i = j
        else:
            i += 1
    return segments


def group_into_components(segments, tol=1e-3):
    """Union-find over segment endpoints (snapped to `tol`). Returns
    {root: [(p1,p2), ...]} -- each value is the raw edge list of one
    connected sub-shape."""

    def key(pt):
        return (round(pt[0] / tol) * tol, round(pt[1] / tol) * tol)

    parent = {}

    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in segments:
        ka, kb = key(a), key(b)
        parent.setdefault(ka, ka)
        parent.setdefault(kb, kb)
        union(ka, kb)

    components = defaultdict(list)
    for a, b in segments:
        components[find(key(a))].append((a, b))
    return dict(components)


def walk_polygon(edges):
    """Orders one component's edge list into a closed polygon point list
    (last point == first point) by walking the adjacency graph. If the
    component is a simple loop (every vertex has degree 2), this returns
    the full loop. If it's not -- see module docstring, "Known failure
    mode" -- the walk will terminate early and `len(result)` will be much
    smaller than `len(edges)`. Always check for that; don't assume success."""
    adj = defaultdict(list)
    for idx, (a, b) in enumerate(edges):
        adj[a].append((b, idx))
        adj[b].append((a, idx))

    start = edges[0][0]
    used = set()
    loop = [start]
    cur = start
    while True:
        candidates = [(nb, idx) for nb, idx in adj[cur] if idx not in used]
        if not candidates:
            break
        nb, idx = candidates[0]
        used.add(idx)
        loop.append(nb)
        cur = nb
        if cur == start:
            break
    return loop


def is_clean_walk(loop, edges):
    """True if `walk_polygon` fully consumed the component (closed loop,
    used every edge). False means the component has a branch point / self-
    touching vertex and `loop` should not be trusted as a simple polygon."""
    return len(loop) - 1 == len(edges) and loop[0] == loop[-1]


def classify_by_radius(components, center, keep_max_rmin):
    """Splits components into (kept, excluded) by their closest point to
    `center` (an (x,y) tuple): a component is kept if its *nearest* point
    to center is within `keep_max_rmin`, on the theory that only pieces
    which are part of a connected, center-reaching design should read as
    "the artwork" -- isolated decoration/registration marks that never
    approach the center will have a much larger minimum radius. Look at
    the actual radius histogram for your file first (there is usually a
    clean gap to threshold on, e.g. 42mm vs 46mm) rather than guessing."""
    kept, excluded = {}, {}
    cx, cy = center
    for root, edges in components.items():
        pts = set()
        for a, b in edges:
            pts.add(a)
            pts.add(b)
        rmin = min(math.hypot(x - cx, y - cy) for x, y in pts)
        (kept if rmin <= keep_max_rmin else excluded)[root] = edges
    return kept, excluded


# ---------------------------------------------------------------------------
# Repair for the "Known failure mode" (C2) described at the top of this file.
#
# walk_polygon() gives up on a component whose curve touches itself: it
# returns a stub, is_clean_walk() says False, and the original advice here
# was to drop that component or substitute a rotated copy of a symmetric
# twin. Both are lossy, and neither works if the shape has no twin.
#
# trace_faces() just solves it. Treat the component as a planar graph and
# walk its faces: on arriving at a vertex, leave by the edge that is next
# CLOCKWISE from the reversed incoming edge. That traversal visits every
# face exactly once; interior faces come back counter-clockwise (positive
# area) and the single outer face clockwise (negative). Keep the positive
# ones over some small area floor and you have the component's real
# polygons, self-touch and all.
#
# On coasters/Insert-tree.stl this recovered all 3 of the tree's 62
# components that walk_polygon could not close. Each turned out to be a
# simple loop carrying a zero-area spur -- a duplicated edge traversed in
# both directions -- rather than a genuine figure-eight, which is why the
# areas came back as a clean +/- pair plus a 0.0.
#
#     from dxf_trace import trace_faces, polygon_area
#     if not is_clean_walk(loop, edges):
#         for f in trace_faces(edges):
#             if polygon_area(f) > 0.02:
#                 use(f)
# ---------------------------------------------------------------------------

def polygon_area(poly):
    """Signed area of a point list (positive = counter-clockwise)."""
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def drop_spurs(poly, max_area=1e-3, tol=1e-4):
    """Remove zero-area excursions from a closed polygon.

    A traced loop can visit the same point twice and enclose nothing
    between the two visits -- an edge walked out and back, or a two- or
    three-step wander along a curve that returns where it started. The
    Tree of Life build found these and dismissed them as harmless because
    they carry no area (its spec, section 6, D3). They are not harmless.

    A polygon that touches itself at a point is still a valid `polygon()`
    to OpenSCAD and still renders the correct shape, but `linear_extrude()`
    turns that point into a vertical edge shared by FOUR side faces instead
    of two. The result is a mesh that is the right size, the right volume,
    a single shell, visually perfect -- and not watertight. Two arcs on the
    triskele coaster did exactly this, for spurs of 2.3e-6 mm^2 (see
    coasters/coaster_triskele_spec.md section 6, E2).

    So this is a mesh-validity repair, not a cosmetic one, and it is worth
    doing to every traced polygon rather than only to the ones that needed
    `trace_faces()`: one of the three spurs found on that coaster came out
    of a component that `walk_polygon` had walked perfectly cleanly.

    A repeated vertex enclosing REAL area is left alone -- that is a
    genuine figure-eight, which is `trace_faces`'s job to split, not this
    one's. `max_area` is deliberately far below any feature worth keeping
    (1e-3 mm^2 is a 30 micron square) and far above float noise.
    """
    def k(p):
        return (round(p[0] / tol) * tol, round(p[1] / tol) * tol)

    poly = list(poly)
    again = True
    while again:
        again = False
        seen = {}
        for i, p in enumerate(poly):
            key = k(p)
            if key in seen and abs(polygon_area(poly[seen[key]:i])) <= max_area:
                poly = poly[:seen[key]] + poly[i:]
                again = True
                break
            seen[key] = i
    return poly


def trace_faces(edges, tol=1e-6):
    """Decompose one component's edge list into its simple closed faces.

    Returns a list of point lists. Interior faces have positive area, the
    outer boundary negative, and degenerate spurs come back at 0.0 -- so
    filter on `polygon_area(f) > <small>` to get the usable polygons."""
    def k(p):
        return (round(p[0] / tol) * tol, round(p[1] / tol) * tol)

    pos = {}
    adj = defaultdict(list)
    for a, b in edges:
        ka, kb = k(a), k(b)
        if ka == kb:
            continue
        pos[ka] = a
        pos[kb] = b
        adj[ka].append(kb)
        adj[kb].append(ka)

    order = {}
    for v, nbrs in adj.items():
        uniq = []
        for n in nbrs:
            if n not in uniq:
                uniq.append(n)
        uniq.sort(key=lambda n: math.atan2(n[1] - v[1], n[0] - v[0]))
        order[v] = uniq
    idx = {v: {n: i for i, n in enumerate(ns)} for v, ns in order.items()}

    visited = set()
    faces = []
    for v in order:
        for w in order[v]:
            if (v, w) in visited:
                continue
            face = []
            cv, cw = v, w
            while True:
                visited.add((cv, cw))
                face.append(cv)
                ns = order[cw]
                nxt = ns[(idx[cw][cv] - 1) % len(ns)]
                cv, cw = cw, nxt
                if (cv, cw) == (v, w):
                    break
                if len(face) > len(edges) + 5:
                    break
            faces.append([pos[p] for p in face])
    return faces
