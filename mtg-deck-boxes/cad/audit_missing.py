#!/usr/bin/env python3
"""What does the original have that the rebuild does not?

    python3 cad/audit_missing.py

The face-by-face comparison in check_ugp100.py only ever compares things the
rebuild already HAS, so it cannot see a feature that was left out: the four snap
domes were missing through rev D and every check passed.  This asks the other
question.  It samples the original meshes densely, finds how far each sample is
from the nearest point on the rebuilt mesh, and reports where the distance is
large, grouped into clusters.

Reading the result.  Distance is not the same as "missing": a deliberately
dropped fillet is also far from the rebuild.  The known, intended departures
are the 2 mm perimeter rounds and the elliptical corners (spec D3, D4), the
0.5 mm edge fillets (D5), the groove-roof blend (D6), and the label, which the
original's blank bottom does not have.  What matters is a cluster that is none
of those -- a patch away from any edge, with a distance like a feature's.

The label is left out of the rebuilt bottom for the comparison (label=False),
since the source is the BLANK.  Slow in pure Python (a minute or so).
"""
import math
import os
import subprocess
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))
sys.path.insert(0, HERE)

import check_ugp100 as C
import build_ugp100 as builder
import ugp100_params as P
from stl_io import load_stl

CELL = 2.5
THRESH = 0.25           # mm; below this a sample is "explained"


class Grid:
    """Uniform grid over triangles, for nearest-surface queries."""
    def __init__(self, tris):
        self.tris = tris
        self.cells = defaultdict(list)
        for i, t in enumerate(tris):
            lo = [min(v[k] for v in t) for k in range(3)]
            hi = [max(v[k] for v in t) for k in range(3)]
            for ix in range(int(lo[0] // CELL), int(hi[0] // CELL) + 1):
                for iy in range(int(lo[1] // CELL), int(hi[1] // CELL) + 1):
                    for iz in range(int(lo[2] // CELL), int(hi[2] // CELL) + 1):
                        self.cells[(ix, iy, iz)].append(i)

    def nearest(self, p, limit=3.5):
        """Distance to the nearest triangle, searched in growing shells of
        cells, so a sample far from everything costs more but stays exact."""
        cx, cy, cz = (int(p[k] // CELL) for k in range(3))
        best = limit
        for r in range(0, int(limit // CELL) + 2):
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
                            d = C._tri_dist(p, *self.tris[i])
                            if d < best:
                                best = d
            # anything outside shell r is at least r*CELL away
            if best <= r * CELL:
                break
        return best


def samples(tris):
    """Vertices, centroids and edge midpoints: dense enough that a patch of the
    surface a millimetre across cannot hide between them."""
    for a, b, c in tris:
        yield a
        yield tuple((a[i] + b[i] + c[i]) / 3.0 for i in range(3))
        yield tuple((a[i] + b[i]) / 2.0 for i in range(3))
        yield tuple((b[i] + c[i]) / 2.0 for i in range(3))


def export(src_builder):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "x.slvs"); out = os.path.join(tmp, "x.stl")
        src_builder().write(src)
        subprocess.run(["solvespace-cli", "export-mesh", "--chord-tol", "0.02",
                        "--output", out, src], capture_output=True)
        return load_stl(out)


def _seam_s(p):
    """Perpendicular height above the seam plane (rebuild frame)."""
    return (-P.SEAM_SIN * p[1] + P.SEAM_COS * p[2]) - P.SEAM_COS * P.Z_SEAM


def known_departure(q, part):
    """Is this sample in a region where the rebuild is DELIBERATELY different
    from the original?  Each zone is a decision recorded in the spec; a sample
    in none of them, and far from the rebuild, is something nobody decided."""
    ex = P.EXT_HX - abs(q[0])
    ey = P.EXT_HY - abs(q[1])
    e = min(ex, ey)                                  # distance in from the outside
    s_ = _seam_s(q)
    lip_s = P.LIP_H * P.SEAM_COS
    # D4: the exterior corners are an ellipse in the original, a circle here
    if ex < 2.6 and ey < 2.6:
        return "corner (D4)"
    # the exterior horizontal perimeter rounds, r2.0 in the original (D3)
    if part == "bottom" and q[2] < 2.6 and e < 2.6:
        return "underside round (D3)"
    if part == "top" and q[2] > P.H_TOTAL - 2.6 and e < 2.6:
        return "lid-top round (D3)"
    # the r0.5 fillet on the seam's outer edge (D5)
    if abs(s_) < 1.0 and e < 1.0:
        return "seam outer edge (D5)"
    if part == "bottom":
        # the lip's top edges, inner and outer (D5)
        if abs(s_ - lip_s) < 1.0 and min(abs(P.LIP_HX - abs(q[0])), abs(P.LIP_HY - abs(q[1])),
                                         abs(P.INT_HX - abs(q[0])), abs(P.INT_HY - abs(q[1]))) < 1.0:
            return "lip top edges (D5)"
    else:
        # the blend from the groove roof into its wall, and the relieved groove
        # corners (D6, D7)
        if abs(s_ - lip_s) < 3.2 and min(P.GROOVE_HX - abs(q[0]), P.GROOVE_HY - abs(q[1])) < 3.2:
            return "groove roof blend (D6)"
        # the lead-in at the groove mouth.  The original is a 0.4 chamfer on the
        # wall plus a ~0.6 round into the seam face, reaching 1.46 mm up the
        # back wall, 1.02 up the side walls and 0.5 up the front; the rebuild is
        # one 0.6 chamfer all round (D5, D9).  Measured difference: up to 0.43
        # mm, at the back wall only; within 0.25 mm elsewhere.
        if -0.4 < s_ < 2.0 and (-2.0 < (abs(q[0]) - P.GROOVE_HX) < 1.5 or
                                -2.0 < (abs(q[1]) - P.GROOVE_HY) < 1.5):
            return "groove mouth bevel (D5/D9)"
    return None


def audit(name, orig_tris, rebuilt_tris, shift_back, part, top_n=12):
    g = Grid(rebuilt_tris)
    far, explained = [], defaultdict(int)
    for p in samples(orig_tris):
        q = tuple(p[i] - shift_back[i] for i in range(3))
        d = g.nearest(q)
        if d > THRESH:
            why = known_departure(q, part)
            if why:
                explained[why] += 1
            else:
                far.append((q, d))
    total = sum(explained.values()) + len(far)
    print("%s: %d of the original's samples are more than %.2f mm from the rebuild"
          % (name, total, THRESH))
    for why, n in sorted(explained.items(), key=lambda kv: -kv[1]):
        print("     %5d  explained: %s" % (n, why))
    # cluster what is left by proximity
    clusters = []
    for q, d in sorted(far, key=lambda x: -x[1]):
        for cl in clusters:
            if math.dist(q, cl["c"]) < 3.0:
                cl["pts"].append((q, d))
                break
        else:
            clusters.append({"c": q, "pts": [(q, d)]})
    clusters.sort(key=lambda cl: -max(d for _, d in cl["pts"]))
    print("     %5d  UNEXPLAINED, in %d clusters%s" %
          (len(far), len(clusters), "" if clusters else "  -- nothing left over"))
    for cl in clusters[:top_n]:
        pts = [q for q, _ in cl["pts"]]
        ctr = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
        print("         worst %.2f mm  %4d samples  around x=%7.2f y=%7.2f z=%7.2f  "
              "spread %.1f x %.1f x %.1f"
              % (max(d for _, d in cl["pts"]), len(pts), ctr[0], ctr[1], ctr[2],
                 *(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3))))
    return clusters


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bottom-stl", help="audit this STL (in the rebuild frame) "
                    "instead of building the bottom")
    ap.add_argument("--top-stl")
    ap.add_argument("--prove", action="store_true",
                    help="audit a rebuild WITHOUT the snap domes and dimples and "
                    "confirm all four positions are reported: proof that this "
                    "audit can see a missing feature")
    a = ap.parse_args()
    ob = load_stl(C.ORIG["bottom"])
    ot = load_stl(C.ORIG["top"])

    if a.prove:
        rb = export(lambda: builder.build_bottom(label=False, bumps=False))
        rt = export(lambda: builder.build_top(dimples=False))
        cb = audit("BOTTOM, domes left out", ob, rb, C.TO_ORIG, "bottom")
        print()
        ct = audit("TOP, dimples left out", ot, rt,
                   tuple(C.TO_ORIG[i] + C.TOP_OFF[i] for i in range(3)), "top")
        ok = True
        print()
        for part, clusters in (("domes", cb), ("dimples", ct)):
            for sg in (-1, 1):
                for (y, z) in P.SNAP_POINTS:
                    face = P.LIP_HX if part == "domes" else P.GROOVE_HX
                    here = (sg * (face + 0.4), y, z)
                    hit = any(math.dist(here, q) < 2.0 for c in clusters
                              for q, _ in c["pts"])
                    ok = ok and hit
                    print("  %s at %s face, y=%7.2f z=%6.2f : %s"
                          % (part[:-1], "left " if sg < 0 else "right", y, z,
                             "FOUND by the audit" if hit else "NOT FOUND"))
        print("\n%s" % ("the audit finds all 8 missing caps" if ok else
                        "THE AUDIT MISSED A MISSING CAP"))
        return 0 if ok else 1

    rb = load_stl(a.bottom_stl) if a.bottom_stl else \
        export(lambda: builder.build_bottom(label=False))
    rt = load_stl(a.top_stl) if a.top_stl else export(lambda: builder.build_top())
    cb = audit("BOTTOM", ob, rb, C.TO_ORIG, "bottom")
    print()
    ct = audit("TOP", ot, rt, tuple(C.TO_ORIG[i] + C.TOP_OFF[i] for i in range(3)), "top")
    left = len(cb) + len(ct)
    print("\n%s" % ("nothing unexplained: every region where the original differs from "
                    "the rebuild is a recorded decision" if not left else
                    "%d unexplained clusters -- something is missing, or a decision "
                    "is unrecorded" % left))
    return 0 if not left else 1


if __name__ == "__main__":
    sys.exit(main())
