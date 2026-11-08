"""What does one mesh have that another does not?

    from mesh_compare import far_samples, cluster_points, compare

    res = compare(source_tris, rebuilt_tris, to_dst=(dx, dy, dz), thresh=0.25)
    res["clusters"]                      # regions of the source far from the rebuild

    python3 mesh_compare.py source.stl rebuilt.stl --to-dst -41.5 -25.65 -6.61

The question this answers is the one every other check in this repo cannot.  A
check that compares a rebuild against its source walks what the REBUILD has --
the faces it built, the points it was told about -- so it cannot find what was
left out.  Four snap domes were missing through four revisions with every such
check green.  This samples the SOURCE densely and measures how far each sample
is from the nearest point on the rebuild; a missing feature shows up as a cluster
of samples hovering over empty space.

`compare` is part-agnostic.  What it cannot know is which differences were
DECIDED: a dropped fillet is also far from the rebuild.  So `far_samples` takes
an `explain` callback -- given a sample's position, return a label if it falls in
a region where the rebuild is deliberately different, else None.  Explained
samples are counted and set aside; what remains is, by construction, something
nobody decided.  The callback is where a part's own knowledge goes; see
`mtg-deck-boxes/cad/audit_missing.py` for a complete one.

Proving it works.  A tool that reports "nothing missing" is worthless until it has
been shown to report a missing thing.  Leave a known feature out of the rebuild
and require the tool to find it (`audit_missing.py --prove` does this).

Limits.  It looks one way: source -> rebuild.  It finds what is MISSING.  What is
EXTRA in the rebuild (an engraving the source never had) it finds only by accident:
swapping the arguments reports a sample only where the source's own surface happens
to lie under or inside the extra feature, and a flat face of two triangles has
samples along its diagonal and nowhere else.  Do not rely on the reverse.  It is
blind below `thresh`: a
feature shallower than that is invisible, so choose `thresh` for the smallest
feature you care about, not for comfort.  And it is only as dense as the source
mesh: a flat face made of two huge triangles contributes five samples.

The two meshes must be in one frame.  `to_dst` is ADDED to every source point to
put it in the rebuild's frame; get its sign wrong and everything is "far", which
at least is not subtle.
"""
import math

from mesh_geom import SurfaceIndex, surface_samples


def far_samples(src, dst, to_dst=(0.0, 0.0, 0.0), thresh=0.25, limit=3.5,
                explain=None, index=None):
    """Samples of `src` more than `thresh` from the surface of `dst`.

    Returns a dict:
        far        [(point in dst's frame, distance), ...]   unexplained
        explained  {label: count}
        total      samples over `thresh`, explained or not
        sampled    how many samples were taken
    Distances are capped at `limit` (see `SurfaceIndex.nearest`).
    """
    idx = index or SurfaceIndex(dst)
    far, explained, sampled = [], {}, 0
    for p in surface_samples(src):
        sampled += 1
        q = (p[0] + to_dst[0], p[1] + to_dst[1], p[2] + to_dst[2])
        d = idx.nearest(q, limit)
        if d > thresh:
            why = explain(q) if explain else None
            if why:
                explained[why] = explained.get(why, 0) + 1
            else:
                far.append((q, d))
    return {"far": far, "explained": explained,
            "total": len(far) + sum(explained.values()), "sampled": sampled}


def cluster_points(far, radius=3.0):
    """Group (point, distance) pairs into clusters of points within `radius`.
    Returns dicts sorted by worst distance, largest first:
        centre, n, worst, spread (extent in x, y, z), pts"""
    clusters = []
    for q, d in sorted(far, key=lambda x: -x[1]):
        for cl in clusters:
            if math.dist(q, cl["seed"]) < radius:
                cl["pts"].append((q, d))
                break
        else:
            clusters.append({"seed": q, "pts": [(q, d)]})
    out = []
    for cl in clusters:
        pts = [q for q, _ in cl["pts"]]
        n = len(pts)
        out.append({"centre": tuple(sum(p[i] for p in pts) / n for i in range(3)),
                    "n": n, "worst": max(d for _, d in cl["pts"]),
                    "spread": tuple(max(p[i] for p in pts) - min(p[i] for p in pts)
                                    for i in range(3)),
                    "pts": cl["pts"]})
    out.sort(key=lambda c: -c["worst"])
    return out


def compare(src, dst, to_dst=(0.0, 0.0, 0.0), thresh=0.25, explain=None, radius=3.0):
    """`far_samples` then `cluster_points`: returns the far_samples dict plus
    "clusters"."""
    res = far_samples(src, dst, to_dst, thresh, explain=explain)
    res["clusters"] = cluster_points(res["far"], radius)
    return res


def print_report(res, name="", thresh=0.25, top_n=12):
    print("%s: %d of %d source samples are more than %.2f mm from the rebuild"
          % (name or "comparison", res["total"], res["sampled"], thresh))
    for why, n in sorted(res["explained"].items(), key=lambda kv: -kv[1]):
        print("     %5d  explained: %s" % (n, why))
    cl = res["clusters"]
    print("     %5d  UNEXPLAINED, in %d clusters%s"
          % (len(res["far"]), len(cl), "" if cl else "  -- nothing left over"))
    for c in cl[:top_n]:
        print("         worst %.2f mm  %4d samples  around x=%7.2f y=%7.2f z=%7.2f  "
              "spread %.1f x %.1f x %.1f" % (c["worst"], c["n"], *c["centre"], *c["spread"]))


if __name__ == "__main__":
    import argparse
    import sys
    from stl_io import load_stl
    ap = argparse.ArgumentParser(description="Where does the source differ from the rebuild?")
    ap.add_argument("source")
    ap.add_argument("rebuilt")
    ap.add_argument("--to-dst", nargs=3, type=float, default=(0.0, 0.0, 0.0),
                    metavar=("DX", "DY", "DZ"),
                    help="added to source points to put them in the rebuild's frame")
    ap.add_argument("--thresh", type=float, default=0.25)
    a = ap.parse_args()
    res = compare(load_stl(a.source), load_stl(a.rebuilt), a.to_dst, a.thresh)
    print_report(res, "%s vs %s" % (a.source, a.rebuilt), a.thresh)
    sys.exit(0 if not res["clusters"] else 1)
