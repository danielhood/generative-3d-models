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
