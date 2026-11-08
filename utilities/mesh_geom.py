"""Small geometry primitives that the mesh tools in this folder all need.

Every function here used to be defined privately, several times, inside whichever
check script needed it first (`tri_na`, `_volume`, `shift`, `_tri_dist`, a grid
class...).  They live here once so a fix lands everywhere.

    from mesh_geom import bbox, volume, shift, tri_normal_area, SurfaceIndex

A mesh is what `stl_io.load_stl` returns: a list of triangles, each
((x,y,z), (x,y,z), (x,y,z)).  Nothing here needs more than the standard library.

Units are whatever the STL is in (mm here).  Normals follow the right-hand rule
on the vertex order, so on a mesh with outward-facing normals (what `mesh_check`
verifies) they point away from the solid.
"""
import math
from collections import defaultdict


def tri_normal_area(t):
    """-> (unit normal, area) of one triangle, or (None, 0.0) if it is degenerate."""
    a, b, c = t
    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = (e1[1] * e2[2] - e1[2] * e2[1],
         e1[2] * e2[0] - e1[0] * e2[2],
         e1[0] * e2[1] - e1[1] * e2[0])
    m = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
    if m < 1e-15:
        return None, 0.0
    return (n[0] / m, n[1] / m, n[2] / m), m / 2.0


def bbox(tris):
    """-> ((xmin, ymin, zmin), (xmax, ymax, zmax))."""
    lo = [min(v[k] for t in tris for v in t) for k in range(3)]
    hi = [max(v[k] for t in tris for v in t) for k in range(3)]
    return tuple(lo), tuple(hi)


def volume(tris):
    """Signed volume by the divergence theorem.  Positive for a closed mesh with
    outward normals; a negative result means inside-out, and a result that is
    wrong in magnitude means the mesh is not closed (check `mesh_check` first)."""
    v = 0.0
    for a, b, c in tris:
        v += (a[0] * (b[1] * c[2] - b[2] * c[1]) -
              a[1] * (b[0] * c[2] - b[2] * c[0]) +
              a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return v


def shift(tris, d):
    """The mesh translated by d = (dx, dy, dz).  Use this to put two meshes in
    one frame before comparing them -- and be sure which way you are shifting:
    the original STLs of a part rarely share the frame of a rebuild."""
    return [tuple(tuple(v[i] + d[i] for i in range(3)) for v in t) for t in tris]


def point_tri_distance(p, a, b, c):
    """Distance from point p to triangle abc (the closest point may be inside the
    face, on an edge, or a vertex).  Ericson, Real-Time Collision Detection,
    ClosestPtPointTriangle."""
    def sub(u, v):
        return (u[0] - v[0], u[1] - v[1], u[2] - v[2])

    def dot(u, v):
        return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]

    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0:
        q = a
    else:
        bp = sub(p, b)
        d3, d4 = dot(ab, bp), dot(ac, bp)
        if d3 >= 0 and d4 <= d3:
            q = b
        else:
            vc = d1 * d4 - d3 * d2
            if vc <= 0 and d1 >= 0 and d3 <= 0:
                t = d1 / (d1 - d3)
                q = tuple(a[i] + t * ab[i] for i in range(3))
            else:
                cp = sub(p, c)
                d5, d6 = dot(ab, cp), dot(ac, cp)
                if d6 >= 0 and d5 <= d6:
                    q = c
                else:
                    vb = d5 * d2 - d1 * d6
                    if vb <= 0 and d2 >= 0 and d6 <= 0:
                        t = d2 / (d2 - d6)
                        q = tuple(a[i] + t * ac[i] for i in range(3))
                    else:
                        va = d3 * d6 - d5 * d4
                        if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
                            t = (d4 - d3) / ((d4 - d3) + (d5 - d6))
                            q = tuple(b[i] + t * (c[i] - b[i]) for i in range(3))
                        else:
                            den = 1.0 / (va + vb + vc)
                            v, w = vb * den, vc * den
                            q = tuple(a[i] + ab[i] * v + ac[i] * w for i in range(3))
    return math.sqrt(sum((p[i] - q[i]) ** 2 for i in range(3)))


class SurfaceIndex:
    """Nearest-surface queries against a mesh, through a uniform grid.

        idx = SurfaceIndex(tris)
        d = idx.nearest(p)          # distance from p to the surface

    Brute force is O(triangles) per query, which is fine for a handful of points
    and hopeless for the tens of thousands a surface comparison needs; the grid
    makes each query look at a few cells.  Answers are exact, not approximate:
    cells are searched in growing shells until nothing unsearched could be
    closer.

    `nearest` caps at `limit`: a point more than `limit` from everything returns
    `limit`, not its true distance.  Raise it if you need the far tail.
    """

    def __init__(self, tris, cell=2.5):
        self.tris = tris
        self.cell = cell
        self.cells = defaultdict(list)
        for i, t in enumerate(tris):
            lo = [min(v[k] for v in t) for k in range(3)]
            hi = [max(v[k] for v in t) for k in range(3)]
            for ix in range(int(lo[0] // cell), int(hi[0] // cell) + 1):
                for iy in range(int(lo[1] // cell), int(hi[1] // cell) + 1):
                    for iz in range(int(lo[2] // cell), int(hi[2] // cell) + 1):
                        self.cells[(ix, iy, iz)].append(i)

    def nearest(self, p, limit=3.5):
        cell = self.cell
        cx, cy, cz = (int(p[k] // cell) for k in range(3))
        best = limit
        for r in range(0, int(limit // cell) + 2):
            seen = set()
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    for dz in range(-r, r + 1):
                        if max(abs(dx), abs(dy), abs(dz)) != r:
                            continue
                        for i in self.cells.get((cx + dx, cy + dy, cz + dz), ()):
                            if i in seen:
                                continue
                            seen.add(i)
                            d = point_tri_distance(p, *self.tris[i])
                            if d < best:
                                best = d
            # a triangle in a cell outside this shell is at least r*cell away
            if best <= r * cell:
                break
        return best


def surface_samples(tris):
    """Vertices, centroids and edge midpoints of every triangle: dense enough
    that a patch of surface about a millimetre across cannot hide between them
    on a mesh with triangles of that size.  A very coarse mesh (a flat face made
    of two big triangles) is sampled as coarsely as it is built."""
    for a, b, c in tris:
        yield a
        yield tuple((a[i] + b[i] + c[i]) / 3.0 for i in range(3))
        yield tuple((a[i] + b[i]) / 2.0 for i in range(3))
        yield tuple((b[i] + c[i]) / 2.0 for i in range(3))
