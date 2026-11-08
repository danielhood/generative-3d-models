"""Find and measure small bumps and dimples standing on, or cut into, a flat face.

    from mesh_features import features_beyond, radial_profile, fit_sphere_cap

    for f in features_beyond(tris, axis=0, face=4.653, outward=-1):
        print(f["centre"], f["height"], f["half_extents"])
        print(fit_sphere_cap(f))

    python3 mesh_features.py part.stl --axis x --face 4.653 --outward -1

A "feature" here is geometry on the far side of a plane from the solid's
surface: a snap dome standing off a wall, or a dimple cut into one.  Planar
checks (`mesh_planes.py`) are blind to these -- a dome is hundreds of tiny
non-planar facets, below any sensible area floor -- so the wall it stands on
matches to 0.00001 mm and the dome goes unnoticed.  That is how four of them
were missed through four revisions.  This finds them.

Direction.  `outward` is +1 or -1: the sign, along `axis`, that points away from
the face's solid.  For a bump that is the direction it protrudes.  For a dimple
cut into the wall it is the direction the dimple goes into the material, so a
dimple in a wall at x = 4.645 whose material lies at smaller x has outward = -1.
In both cases "height" is how far the feature reaches along that direction.

What it returns, per feature, in the face's two in-plane axes (u, v), taken in
ascending axis order (axis x -> (y, z); axis y -> (x, z); axis z -> (x, y)):

    centre        the middle of the feature's outline on the face
    half_extents  half its width in u and in v
    height        how far it reaches off the face
    tris, ring    its triangles; the outline vertices lying on the face

Things that will bite you:

  * `centre` is the middle of the OUTLINE'S BOUNDING BOX, never the mean of its
    vertices.  A search window clips a ring unevenly and a vertex mean follows
    the clipping: using the mean put dimples 0.13 mm from where they were, a
    wrong figure that was reported before it was caught.  The bounding box does
    not care.
  * `fit_sphere_cap` fits the VERTICES of the mesh.  A coarse mesh is a polygon
    inscribed in the true surface (for a bump) or circumscribed about it (for a
    dimple's void), so a 100-triangle dimple's cross-sections come out a few
    hundredths smaller than the sphere through its vertices.  Judge the fit by
    its `rms`, not by how round the numbers look.
  * The fit assumes the feature is round.  A feature scaled non-uniformly (these
    domes were stretched 1.1953 in y) fits badly unless you pass `scale`.  A fit
    that is bad in one direction and fine in the other is an ellipse.
  * Pick the window and `max_off` so a neighbouring fillet or relief does not
    count as part of the feature: the top's groove has its own blends that sit
    "beyond the wall" and swamp a naive search.
"""
import math


def _cluster(items, link):
    """Single-linkage clusters of (index, (u, v)) points closer than `link`."""
    cells = {}
    for k, (_, p) in enumerate(items):
        cells.setdefault((int(p[0] // link), int(p[1] // link)), []).append(k)
    parent = list(range(len(items)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (cu, cv), members in cells.items():
        for du in (-1, 0, 1):
            for dv in (-1, 0, 1):
                for k2 in cells.get((cu + du, cv + dv), ()):
                    for k in members:
                        if k < k2 and math.dist(items[k][1], items[k2][1]) < link:
                            ra, rb = find(k), find(k2)
                            if ra != rb:
                                parent[ra] = rb
    groups = {}
    for k in range(len(items)):
        groups.setdefault(find(k), []).append(items[k][0])
    return list(groups.values())


def features_beyond(tris, axis, face, outward, *, min_off=0.004, max_off=2.0,
                    window=None, keep=None, link=1.5, ring_tol=2e-4):
    """Bumps/dimples beyond the plane `axis = face`, on the `outward` side.

    min_off    a triangle counts only if some vertex is at least this far off the
               plane (keeps the face's own triangles out)
    max_off    ...and all its vertices are within this of the plane (keeps far
               geometry out)
    window     (u0, u1, v0, v1): all of a triangle's vertices must lie inside
    keep       optional predicate on a triangle, for anything the above cannot
               say (e.g. "above the seam plane")
    link       triangles whose centroids are within this are one feature

    Returns a list of feature dicts (see the module docstring), largest first.
    """
    i, j = [k for k in range(3) if k != axis]
    chosen = []
    for t in tris:
        offs = [outward * (v[axis] - face) for v in t]
        if max(offs) <= min_off or any(abs(v[axis] - face) >= max_off for v in t):
            continue
        if window is not None:
            u0, u1, v0, v1 = window
            if any(not (u0 <= v[i] <= u1 and v0 <= v[j] <= v1) for v in t):
                continue
        if keep is not None and not keep(t):
            continue
        chosen.append(t)
    items = [(k, (sum(v[i] for v in t) / 3.0, sum(v[j] for v in t) / 3.0))
             for k, t in enumerate(chosen)]
    features = []
    for idxs in _cluster(items, link):
        ft = [chosen[k] for k in idxs]
        vs = [v for t in ft for v in t]
        ring = [v for v in vs if abs(v[axis] - face) < ring_tol] or vs
        us, vv = [v[i] for v in ring], [v[j] for v in ring]
        apex = max(vs, key=lambda v: outward * (v[axis] - face))
        features.append({
            "tris": ft, "n": len(ft), "ring": ring, "verts": vs,
            "centre": ((max(us) + min(us)) / 2.0, (max(vv) + min(vv)) / 2.0),
            "half_extents": ((max(us) - min(us)) / 2.0, (max(vv) - min(vv)) / 2.0),
            "height": outward * (apex[axis] - face),
            "apex": (apex[i], apex[j]),
            "axis": axis, "face": face, "outward": outward})
    features.sort(key=lambda f: -f["n"])
    return features


def radial_profile(feature, scale=(1.0, 1.0), min_off=0.0):
    """Height against radius from the feature's centre: [(r, height), ...] sorted
    by r.  `scale` divides the two in-plane offsets first, to undo a known
    non-uniform stretch (pass (1.1953, 1.0) for something stretched in u)."""
    cu, cv = feature["centre"]
    ax, face, out = feature["axis"], feature["face"], feature["outward"]
    i, j = [k for k in range(3) if k != ax]
    prof = []
    for v in feature["verts"]:
        h = out * (v[ax] - face)
        if h >= min_off:
            prof.append((math.hypot((v[i] - cu) / scale[0], (v[j] - cv) / scale[1]), h))
    prof.sort()
    return prof


def fit_sphere_cap(feature, scale=(1.0, 1.0), min_off=0.01):
    """Least-squares sphere through the feature's vertices.

    The sphere's centre lies on the feature's axis at offset `centre` along
    `outward` (NEGATIVE when it sits behind the face, as it does for any cap
    shallower than a hemisphere).  Returns
        radius        sphere radius
        centre        signed offset of the sphere's centre from the face
        height        centre + radius: how far the cap reaches off the face
        mouth         sqrt(radius^2 - centre^2): the cap's radius at the face
        rms           misfit, in mm^2 of (r^2 + (d - c)^2 - R^2): ~0.001 is a
                      clean fit, ~0.03 is a coarse mesh, 0.1+ is not a sphere
    Linear in (c, R^2 - c^2), so it needs no starting guess.
    """
    pairs = [(r, d) for r, d in radial_profile(feature, scale, min_off)]
    n = len(pairs)
    if n < 3:
        raise ValueError("too few vertices off the face to fit a sphere (%d)" % n)
    rows = [(2.0 * d, 1.0, r * r + d * d) for r, d in pairs]
    s11 = sum(a * a for a, b, c in rows)
    s12 = sum(a * b for a, b, c in rows)
    s22 = sum(b * b for a, b, c in rows)
    t1 = sum(a * c for a, b, c in rows)
    t2 = sum(b * c for a, b, c in rows)
    det = s11 * s22 - s12 * s12
    c = (t1 * s22 - t2 * s12) / det
    k = (s11 * t2 - s12 * t1) / det
    radius = math.sqrt(k + c * c)
    rms = math.sqrt(sum((r * r + (d - c) ** 2 - radius * radius) ** 2 for r, d in pairs) / n)
    return {"radius": radius, "centre": c, "height": c + radius,
            "mouth": math.sqrt(max(radius * radius - c * c, 0.0)), "rms": rms, "n": n}


if __name__ == "__main__":
    import argparse
    from stl_io import load_stl
    ap = argparse.ArgumentParser(description="Find bumps/dimples beyond a plane.")
    ap.add_argument("stl")
    ap.add_argument("--axis", required=True, choices="xyz")
    ap.add_argument("--face", required=True, type=float, help="the plane's coordinate")
    ap.add_argument("--outward", required=True, type=int, choices=(-1, 1))
    ap.add_argument("--window", nargs=4, type=float, metavar=("U0", "U1", "V0", "V1"))
    ap.add_argument("--max-off", type=float, default=2.0)
    ap.add_argument("--stretch", type=float, default=1.0,
                    help="divide the u offset by this before fitting (undo a known scale)")
    a = ap.parse_args()
    ax = "xyz".index(a.axis)
    names = [c for c in "xyz" if c != a.axis]
    feats = features_beyond(load_stl(a.stl), ax, a.face, a.outward,
                            window=a.window, max_off=a.max_off)
    print("%d feature(s) beyond %s = %.4f on the %s side" %
          (len(feats), a.axis, a.face, "+" if a.outward > 0 else "-"))
    for f in feats:
        print("  centre (%s=%.4f, %s=%.4f)  half-extents %.4f x %.4f  height %.4f  (%d triangles)"
              % (names[0], f["centre"][0], names[1], f["centre"][1], *f["half_extents"],
                 f["height"], f["n"]))
        try:
            s = fit_sphere_cap(f, scale=(a.stretch, 1.0))
            print("      sphere R=%.4f centre %+.4f from the face -> height %.4f, mouth radius %.4f"
                  "   rms %.4f" % (s["radius"], s["centre"], s["height"], s["mouth"], s["rms"]))
        except ValueError as e:
            print("      (no sphere fit: %s)" % e)
