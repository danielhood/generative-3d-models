"""Ray casting against a mesh: where along a line is there solid material?

    from mesh_rays import axis_spans, ray_spans, overlap, max_overlap, is_inside

    axis_spans(tris, 2, x, y)          # solid z-intervals of the column through (x, y)
    ray_spans(tris, origin, direction) # the same along any line
    overlap(spans_a, spans_b)          # do two parts' columns collide?

This is the general tool behind questions like "does the lid interfere with the
box at this point?" and "how thick is the wall here?".  It answers them against
the real exported mesh, for the same reason `mesh_query.py` does (read its
docstring): not from the CAD source, a render, or your own arithmetic.

How it works.  Every triangle the line crosses is a hit.  Whether the line is
ENTERING or LEAVING solid at a hit is read from the triangle's outward normal
against the line direction, not from counting hits, so it needs a closed mesh
with outward normals (`mesh_check.py`).  Solid intervals run from an entry to
the matching exit.

Things that will bite you:

  * A line through exactly an edge or vertex hits two triangles at the same
    point and can come back with a spurious sliver of "solid".  The hits are
    de-duplicated, but the real defence is not choosing round-number
    coordinates: a column at exactly a corner round's tangent line is the
    classic way to read a 0.05 mm interference that is not there.  Offset your
    sample grid by an untidy amount (0.0731, 0.0417) -- see
    `mtg-deck-boxes/cad/check_ugp100.py`.
  * `overlap` returns the largest OVERLAP IN LENGTH along the line.  It is the
    height of an interference along a vertical ray, not its thickness: a thin
    sliver standing 0.7 mm tall reports 0.7 mm.  Section it (`mesh_section.py`)
    before believing a number.
  * Parts that are meant to touch (mating faces) overlap by ~0 and the ray
    cast's own noise is of the order 1e-6; call anything under a micron clear.
"""
import math

_EPS = 1e-9
_CYCLIC = {(0, 1, 2), (1, 2, 0), (2, 0, 1)}


def _spans_from_hits(hits, tol):
    """Hits are (t, +1 entering / -1 leaving).  -> solid (t0, t1) intervals."""
    hits.sort()
    merged = []
    for t, s in hits:
        if merged and abs(t - merged[-1][0]) < 1e-7 and merged[-1][1] == s:
            continue                     # the same crossing seen through an edge
        merged.append((t, s))
    out, depth, start = [], 0, None
    for t, s in merged:
        prev = depth
        depth += s
        if prev <= 0 and depth > 0:
            start = t
        elif prev > 0 and depth <= 0 and start is not None:
            if t - start > tol:
                out.append((start, t))
            start = None
    return out


def axis_spans(tris, axis, a, b, tol=1e-7):
    """Solid intervals along a line parallel to a coordinate axis.

    `axis` is 0, 1 or 2 (x, y, z).  (a, b) are the line's coordinates on the
    OTHER two axes, in ascending axis order: axis=2 -> (x, y); axis=1 -> (x, z);
    axis=0 -> (y, z).  Returns [(lo, hi), ...] in absolute coordinates along
    `axis`.  Much faster than `ray_spans`: most triangles are rejected by a
    bounding-box test before any arithmetic.
    """
    i, j = [k for k in range(3) if k != axis]
    sign = 1.0 if (i, j, axis) in _CYCLIC else -1.0
    hits = []
    for (p0, p1, p2) in tris:
        if (max(p0[i], p1[i], p2[i]) < a - _EPS or min(p0[i], p1[i], p2[i]) > a + _EPS or
                max(p0[j], p1[j], p2[j]) < b - _EPS or min(p0[j], p1[j], p2[j]) > b + _EPS):
            continue
        e1i, e1j, e1k = p1[i] - p0[i], p1[j] - p0[j], p1[axis] - p0[axis]
        e2i, e2j, e2k = p2[i] - p0[i], p2[j] - p0[j], p2[axis] - p0[axis]
        det = e1i * e2j - e1j * e2i               # the normal's component along the axis
        if abs(det) < 1e-14:                      # edge-on to the line
            continue
        qa, qb = a - p0[i], b - p0[j]
        u = (qa * e2j - qb * e2i) / det
        v = (e1i * qb - e1j * qa) / det
        if u < -_EPS or v < -_EPS or u + v > 1 + _EPS:
            continue
        t = p0[axis] + u * e1k + v * e2k
        hits.append((t, 1 if sign * det < 0 else -1))
    return _spans_from_hits(hits, tol)


def ray_spans(tris, origin, direction, tol=1e-7):
    """Solid intervals along an arbitrary line: points origin + t * direction.

    `direction` is normalised here, so t is a distance.  The WHOLE line is
    searched, not just t > 0.  Moller-Trumbore for each triangle; use
    `axis_spans` instead when the line is axis-aligned, which it usually is.
    """
    ox, oy, oz = origin
    m = math.sqrt(sum(c * c for c in direction))
    dx, dy, dz = (c / m for c in direction)
    hits = []
    for (a, b, c) in tris:
        e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        px, py, pz = dy * e2[2] - dz * e2[1], dz * e2[0] - dx * e2[2], dx * e2[1] - dy * e2[0]
        det = e1[0] * px + e1[1] * py + e1[2] * pz
        if abs(det) < 1e-12:
            continue
        inv = 1.0 / det
        tv = (ox - a[0], oy - a[1], oz - a[2])
        u = (tv[0] * px + tv[1] * py + tv[2] * pz) * inv
        if u < -_EPS or u > 1 + _EPS:
            continue
        qx, qy, qz = (tv[1] * e1[2] - tv[2] * e1[1],
                      tv[2] * e1[0] - tv[0] * e1[2],
                      tv[0] * e1[1] - tv[1] * e1[0])
        v = (dx * qx + dy * qy + dz * qz) * inv
        if v < -_EPS or u + v > 1 + _EPS:
            continue
        t = (e2[0] * qx + e2[1] * qy + e2[2] * qz) * inv
        nx = e1[1] * e2[2] - e1[2] * e2[1]
        ny = e1[2] * e2[0] - e1[0] * e2[2]
        nz = e1[0] * e2[1] - e1[1] * e2[0]
        hits.append((t, 1 if nx * dx + ny * dy + nz * dz < 0 else -1))
    return _spans_from_hits(hits, tol)


def is_inside(tris, p, axis=2):
    """Is point p inside the solid?  Answered by the column through p along
    `axis`.  A point exactly ON the surface is a coin toss; do not ask."""
    others = [p[k] for k in range(3) if k != axis]
    return any(lo <= p[axis] <= hi for lo, hi in axis_spans(tris, axis, *others))


def overlap(spans_a, spans_b):
    """The longest overlap between any span of one part's column and any span of
    another's (0.0 if they never overlap).  See the module note: this is a
    LENGTH ALONG THE LINE, not a penetration depth."""
    worst = 0.0
    for a0, a1 in spans_a:
        for b0, b1 in spans_b:
            worst = max(worst, min(a1, b1) - max(a0, b0))
    return worst


def max_overlap(tris_a, tris_b, columns, axis=2):
    """Worst `overlap` of two meshes over a list of columns.

    `columns` is a list of (a, b) coordinate pairs as for `axis_spans`.  Returns
    (worst, column) -- the column is where it happened, or None if never.  Both
    meshes must already be in one frame (`mesh_geom.shift`).
    """
    worst, where = 0.0, None
    for a, b in columns:
        o = overlap(axis_spans(tris_a, axis, a, b), axis_spans(tris_b, axis, a, b))
        if o > worst:
            worst, where = o, (a, b)
    return worst, where


if __name__ == "__main__":
    import sys
    from stl_io import load_stl
    usage = ("usage:  mesh_rays.py part.stl --axis z X Y        solid z-intervals at (x, y)\n"
             "        mesh_rays.py part.stl --ray OX OY OZ DX DY DZ")
    if len(sys.argv) < 4:
        sys.exit(usage)
    tris = load_stl(sys.argv[1])
    if sys.argv[2] == "--axis" and len(sys.argv) == 6:
        ax = "xyz".index(sys.argv[3])
        spans = axis_spans(tris, ax, float(sys.argv[4]), float(sys.argv[5]))
    elif sys.argv[2] == "--ray" and len(sys.argv) == 9:
        v = [float(x) for x in sys.argv[3:9]]
        spans = ray_spans(tris, v[:3], v[3:])
    else:
        sys.exit(usage)
    if not spans:
        print("no material along that line")
    for lo, hi in spans:
        print("solid from %.4f to %.4f   (length %.4f)" % (lo, hi, hi - lo))
