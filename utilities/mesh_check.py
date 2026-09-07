"""Dependency-free STL sanity check: manifoldness, winding, volume, bbox,
connected shells. The generalized, project-agnostic sibling of
pole-foot/check_stl.py (that one also does fit-probe cross-sections specific
to the pole-foot part; this one is just the mesh-health checks, meant to be
reused as-is on any part in this repo).

Usage:
    python3 mesh_check.py part.stl
    from mesh_check import check
    result = check("part.stl")   # dict, see fields below

Why this matters (see coasters/coaster_helm_of_awe_spec.md sections 6-7 for
a worked example): a mesh can be watertight and still be the wrong part --
e.g. N disconnected shells when you meant to print one piece, or a volume
that doesn't match a hand calculation because a feature silently vanished
in a boolean. Always check shells + volume, not just manifoldness.
"""
import sys
from collections import defaultdict

from stl_io import load_stl


def _key(v, q=1e-5):
    return tuple(round(c / q) for c in v)


def check(path, verbose=True):
    tris = load_stl(path)
    idx, verts = {}, []
    faces = []
    for t in tris:
        f = []
        for v in t:
            k = _key(v)
            if k not in idx:
                idx[k] = len(verts)
                verts.append(v)
            f.append(idx[k])
        faces.append(tuple(f))

    # edge manifoldness + consistent winding
    directed = defaultdict(int)
    undirected = defaultdict(int)
    for a, b, c in faces:
        for e in ((a, b), (b, c), (c, a)):
            directed[e] += 1
            undirected[tuple(sorted(e))] += 1
    non_manifold_edges = sum(1 for v in undirected.values() if v != 2)
    flipped = sum(1 for e, c in directed.items() if c > 1)

    # signed volume (mm^3 if the STL is in mm)
    vol = 0.0
    for a, b, c in faces:
        p, q, r = verts[a], verts[b], verts[c]
        vol += (
            p[0] * (q[1] * r[2] - q[2] * r[1])
            - p[1] * (q[0] * r[2] - q[2] * r[0])
            + p[2] * (q[0] * r[1] - q[1] * r[0])
        ) / 6.0

    # connected components over shared vertices -- "shells"
    parent = list(range(len(verts)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for a, b, c in faces:
        union(a, b)
        union(b, c)
    shells = len({find(i) for i in range(len(verts))})

    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    result = {
        "path": path,
        "triangles": len(faces),
        "vertices": len(verts),
        "non_manifold_edges": non_manifold_edges,
        "winding_consistent": flipped == 0,
        "volume": vol,
        "shells": shells,
        "bbox": ((min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))),
        "size": (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)),
    }

    if verbose:
        print(f"file            {path}")
        print(f"triangles       {result['triangles']}   vertices {result['vertices']}")
        print(
            "non-manifold    "
            + (
                "none (every edge shared by exactly 2 faces)"
                if non_manifold_edges == 0
                else f"{non_manifold_edges} edges not shared by exactly 2 faces"
            )
        )
        print(
            "winding         "
            + ("consistent" if result["winding_consistent"] else f"{flipped} mismatched directed edges")
        )
        print(f"volume          {vol:.3f} mm^3  ({'outward normals' if vol > 0 else 'INVERTED'})")
        print(f"shells          {shells}  {'(single piece)' if shells == 1 else '(!) multiple disconnected pieces'}")
        sx, sy, sz = result["size"]
        print(f"size            {sx:.3f} x {sy:.3f} x {sz:.3f} mm")

    return result


if __name__ == "__main__":
    check(sys.argv[1])
