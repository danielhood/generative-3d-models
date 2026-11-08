"""Find the flat faces of a mesh and measure them exactly.

    from mesh_planes import group_planes, axis_planes, fit_plane

    python3 mesh_planes.py part.stl                    # every flat face over 8 mm^2
    python3 mesh_planes.py part.stl --axis             # only faces square to x, y or z
    python3 mesh_planes.py part.stl --like 0 -0.435 0.9   # only faces with that normal

An STL has no notion of "face": a flat wall is some number of coplanar triangles.
Grouping them by normal and offset recovers the faces, and the area-weighted
offset of a group is a far better measurement than any single vertex.  This is
how the original Ultra Guard Pro boxes were reverse-engineered: the wall
thicknesses came out as 4.1176 and 4.7812, not round, and dividing the whole
part by 1.0294 in x and 1.1953 in y turned every number into a round one --
because the part had been non-uniformly scaled.  That kind of insight needs
the exact numbers, to four decimals, which this gives.

Conventions.  A face is described by its outward unit normal n and offset d, the
plane n . p = d.  For a wall facing +x at x = 4.65, n = (1,0,0) and d = 4.65; for
a wall facing -x at x = 4.65, n = (-1,0,0) and d = -4.65.  Check the sign of d
before trusting a comparison between two faces.

Things that will bite you:

  * A curved surface is many tiny planes.  `min_area` drops them, which is the
    point -- but it also means a feature built of small facets (a dome, a
    fillet) is INVISIBLE to this tool.  Four snap domes were missed on exactly
    that basis: the planar comparison matched the lip's faces to 0.00001 mm and
    never saw the domes.  Use `mesh_compare.py` to find what this cannot.
  * Faces are grouped by rounding the offset to `decimals` (default 2).  Two
    genuinely different parallel faces closer than that merge; two triangles of
    one face straddling a rounding boundary split.  Both are rare, neither is
    impossible; if a face's area looks half what it should, that is why.
  * A tiny triangle on a face's boundary can pull its fitted offset by far less
    than a micron.  Pass `min_tri` to ignore small triangles when measuring a
    large face -- needed when something nearby adds small facets with almost the
    same offset (engraved text did, to a floor measured as 94.04998 not 94.05).
"""
import math

from mesh_geom import tri_normal_area


def group_planes(tris, ref=None, tol=1e-5, decimals=2, min_area=5.0, min_tri=0.0):
    """Group coplanar triangles into faces.

    ref        optional (nx, ny, nz): only keep faces whose normal matches this
               direction to within `tol` (compared as 1 - n.ref), and tell those
               faces apart by offset alone.  Note `tol` is on 1 - n.ref, so
               1e-5 admits normals up to ~0.0045 rad off: facets of a shallow
               fillet beside a flat face are inside that, and are averaged into
               it.  Tighten `tol` to separate them.
    min_area   drop faces smaller than this in total
    min_tri    ignore individual triangles smaller than this when grouping

    Returns a list of dicts, largest first:
      normal, offset (d, area-weighted), area, tris, extent {x,y,z: (min,max)}
    """
    if ref is not None:
        rm = math.sqrt(sum(c * c for c in ref))
        ref = tuple(c / rm for c in ref)
    groups = {}
    for t in tris:
        n, a = tri_normal_area(t)
        if n is None or a < min_tri:
            continue
        if ref is not None and sum(n[i] * ref[i] for i in range(3)) < 1 - tol:
            continue
        # With a reference direction every offset is measured ALONG IT rather than
        # along the triangle's own normal, so a facet a few milliradians off (still
        # within `tol`) reports where it sits in that direction.  Faces are then
        # told apart by that offset alone.  Measuring each along its own normal
        # moved the seam face of the Ultra Guard Pro by 0.0002 mm.  Without a
        # reference the normal is part of the key, or two faces at the same offset
        # but different angles would merge.
        direction = ref if ref is not None else n
        d = sum(direction[i] * t[0][i] for i in range(3))
        key = (round(d, decimals),) if ref is not None else \
            (round(n[0], 3), round(n[1], 3), round(n[2], 3), round(d, decimals))
        g = groups.setdefault(key, {"normal": n, "wd": 0.0, "area": 0.0, "tris": []})
        g["wd"] += d * a
        g["area"] += a
        g["tris"].append(t)
    out = []
    for g in groups.values():
        if g["area"] < min_area:
            continue
        ext = {c: (min(v[k] for t in g["tris"] for v in t),
                   max(v[k] for t in g["tris"] for v in t))
               for k, c in enumerate("xyz")}
        out.append({"normal": g["normal"], "offset": g["wd"] / g["area"],
                    "area": g["area"], "tris": g["tris"], "extent": ext})
    out.sort(key=lambda f: -f["area"])
    return out


def axis_planes(tris, min_area=5.0, tol=1e-6, decimals=3):
    """Faces square to x, y or z: {"x": [...], "y": [...], "z": [...]}, each a
    list of dicts (sign +1/-1 of the outward normal along that axis, `pos`, area,
    extent), sorted by position.  The workhorse for prismatic parts: it gives
    the wall positions directly."""
    result = {"x": [], "y": [], "z": []}
    for k, name in enumerate("xyz"):
        groups = {}
        for t in tris:
            n, a = tri_normal_area(t)
            if n is None or abs(abs(n[k]) - 1.0) > tol:
                continue
            sgn = 1 if n[k] > 0 else -1
            pos = sum(v[k] for v in t) / 3.0
            g = groups.setdefault((sgn, round(pos, decimals)), {"wp": 0.0, "area": 0.0, "tris": []})
            g["wp"] += pos * a
            g["area"] += a
            g["tris"].append(t)
        for (sgn, _), g in groups.items():
            if g["area"] < min_area:
                continue
            others = [c for c in range(3) if c != k]
            ext = {"xyz"[c]: (min(v[c] for t in g["tris"] for v in t),
                              max(v[c] for t in g["tris"] for v in t)) for c in others}
            result[name].append({"sign": sgn, "pos": g["wp"] / g["area"],
                                 "area": g["area"], "extent": ext, "tris": g["tris"]})
        result[name].sort(key=lambda f: f["pos"])
    return result


def fit_plane(points, iters=500):
    """Least-squares plane through points: (unit normal, offset d), n . p = d.

    The normal is the direction of least variance of the points, found by power
    iteration on the covariance matrix (standard library only).  The sign is
    arbitrary: flip both if you need it to face a particular way.  Needs the
    points to genuinely span a plane; three nearly collinear points give a
    meaningless normal.
    """
    n = len(points)
    c = [sum(p[i] for p in points) / n for i in range(3)]
    m = [[0.0] * 3 for _ in range(3)]
    for p in points:
        d = [p[i] - c[i] for i in range(3)]
        for i in range(3):
            for j in range(3):
                m[i][j] += d[i] * d[j]
    tr = m[0][0] + m[1][1] + m[2][2]
    a = [[(tr if i == j else 0.0) - m[i][j] for j in range(3)] for i in range(3)]
    v = [0.3, 0.5, 0.81]
    for _ in range(iters):
        w = [sum(a[i][j] * v[j] for j in range(3)) for i in range(3)]
        mag = math.sqrt(sum(x * x for x in w))
        v = [x / mag for x in w]
    return tuple(v), sum(v[i] * c[i] for i in range(3))


def fit_plane_to_tris(tris):
    """`fit_plane` through every vertex of a set of triangles, with the normal
    flipped to agree with the first triangle's outward normal."""
    pts = [v for t in tris for v in t]
    n, d = fit_plane(pts)
    n0, _ = tri_normal_area(tris[0])
    if n0 is not None and sum(n[i] * n0[i] for i in range(3)) < 0:
        n, d = tuple(-x for x in n), -d
    return n, d


def slope_degrees(normal, axis):
    """Angle in degrees between a plane and the axis-aligned plane square to
    `axis` (0, 1, 2).  For a seam tilted about x this recovers its angle:
    normal (0, -0.435, 0.900) against axis 2 is 25.78 degrees."""
    return math.degrees(math.acos(min(1.0, abs(normal[axis]))))


if __name__ == "__main__":
    import argparse
    from stl_io import load_stl
    ap = argparse.ArgumentParser(description="List the flat faces of an STL.")
    ap.add_argument("stl")
    ap.add_argument("--min-area", type=float, default=8.0)
    ap.add_argument("--axis", action="store_true", help="only faces square to x, y or z")
    ap.add_argument("--like", nargs=3, type=float, metavar=("NX", "NY", "NZ"),
                    help="only faces with this normal")
    a = ap.parse_args()
    tris = load_stl(a.stl)
    if a.axis:
        for name, faces in axis_planes(tris, a.min_area).items():
            print("--- faces square to %s ---" % name)
            for f in faces:
                ext = "  ".join("%s[%8.3f,%8.3f]" % (c, *f["extent"][c]) for c in f["extent"])
                print("  %s = %12.6f  n%+d  A=%9.2f  %s" % (name, f["pos"], f["sign"], f["area"], ext))
    else:
        print("%-28s %10s  %s" % ("normal", "offset", "area / extent"))
        for f in group_planes(tris, ref=a.like, min_area=a.min_area):
            n = f["normal"]
            ext = "  ".join("%s[%8.3f,%8.3f]" % (c, *f["extent"][c]) for c in "xyz")
            print("(%6.3f %6.3f %6.3f)  d=%10.4f  A=%9.2f  %s" % (*n, f["offset"], f["area"], ext))
