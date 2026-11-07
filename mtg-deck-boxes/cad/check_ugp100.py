#!/usr/bin/env python3
"""Verify the Ultra Guard Pro 100+ rebuild against the source STLs.

    python3 cad/check_ugp100.py

Exports both .slvs to meshes, then:
  1. mesh health (watertight, one shell, consistent winding)
  2. the critical interior cavity, measured off the mesh rather than trusted
  3. every significant face plane, rebuild vs original, in a common frame
  4. interference along vertical rays for all four bottom/top pairings --
     rebuilt pair, and each rebuilt half against the original other half,
     which is the test that says a printed replacement part still fits

The originals sit in their own arbitrary frame and, more awkwardly, the two of
them do not quite share it: the original top is offset from the original bottom
by (+0.0038, -0.0016, -0.0271) mm.  That z term is not noise -- it means the
original pair interferes by 0.027 mm at the seam.  The rebuild puts the two
halves in one exact frame instead, so its seam faces just touch.
"""
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PART = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))
sys.path.insert(0, HERE)

from stl_io import load_stl
from slvs_write import print_dof_report
import ugp100_params as P
import build_ugp100 as builder

ORIG = {"bottom": os.path.join(PART, "orig", "Ultra_Guard_Pro_100+_bottom-BLANK.stl"),
        "top": os.path.join(PART, "orig", "Ultra_Guard_Pro_100+_top-tight.stl")}
SLVS = {k: os.path.join(PART, "ultra_guard_pro_100_%s.slvs" % k) for k in ORIG}

# rebuild frame -> original bottom's frame
TO_ORIG = (41.505642, 25.650428, 6.610869)
# original top's frame -> original bottom's frame
TOP_OFF = (-0.003752, 0.001600, 0.027149)

FAIL = []


def fail(msg):
    FAIL.append(msg)
    print("  FAIL  " + msg)


def shift(tris, d):
    return [tuple(tuple(v[i] + d[i] for i in range(3)) for v in t) for t in tris]


def tri_na(t):
    a, b, c = t
    e1 = [b[i] - a[i] for i in range(3)]
    e2 = [c[i] - a[i] for i in range(3)]
    n = [e1[1] * e2[2] - e1[2] * e2[1],
         e1[2] * e2[0] - e1[0] * e2[2],
         e1[0] * e2[1] - e1[1] * e2[0]]
    m = math.sqrt(sum(x * x for x in n))
    if m < 1e-15:
        return None, 0.0
    return [x / m for x in n], m / 2


# ---------------------------------------------------------------- ray casting
def ray_spans(tris, x, y):
    """Solid z intervals of the column through (x, y).  Moller-Trumbore with a
    straight-down... up ray; the outward normal opposes the ray on entry, which
    is how the parity is tracked."""
    hits = []
    ox, oy = x, y
    for (a, b, c) in tris:
        # 2D edge test first -- cheap reject for a vertical ray
        if (max(a[0], b[0], c[0]) < ox or min(a[0], b[0], c[0]) > ox or
                max(a[1], b[1], c[1]) < oy or min(a[1], b[1], c[1]) > oy):
            continue
        e1 = [b[i] - a[i] for i in range(3)]
        e2 = [c[i] - a[i] for i in range(3)]
        # p = d x e2 with d = (0,0,1)
        px, py = -e2[1], e2[0]
        det = e1[0] * px + e1[1] * py
        if abs(det) < 1e-14:
            continue
        inv = 1.0 / det
        tv = (ox - a[0], oy - a[1], -a[2])
        u = (tv[0] * px + tv[1] * py) * inv
        if u < -1e-9 or u > 1 + 1e-9:
            continue
        qx = tv[1] * e1[2] - tv[2] * e1[1]
        qy = tv[2] * e1[0] - tv[0] * e1[2]
        qz = tv[0] * e1[1] - tv[1] * e1[0]
        v = qz * inv
        if v < -1e-9 or u + v > 1 + 1e-9:
            continue
        t = (e2[0] * qx + e2[1] * qy + e2[2] * qz) * inv
        n, _ = tri_na((a, b, c))
        hits.append((t, 1 if n[2] < 0 else -1))      # +1 = entering
    hits.sort()
    out, depth, start = [], 0, None
    for t, s in hits:
        prev = depth
        depth += s
        if prev <= 0 and depth > 0:
            start = t
        elif prev > 0 and depth <= 0 and start is not None:
            if t - start > 1e-7:
                out.append((start, t))
            start = None
    return out


def overlap(sa, sb):
    worst = 0.0
    for a0, a1 in sa:
        for b0, b1 in sb:
            worst = max(worst, min(a1, b1) - max(a0, b0))
    return worst


# ---------------------------------------------------------------- face planes
def planes(tris, ref, tol=1e-5, min_area=5.0, min_tri=0.0):
    rm = math.sqrt(sum(c * c for c in ref))
    refn = [c / rm for c in ref]
    acc = {}
    for t in tris:
        n, a = tri_na(t)
        if (n is None or a < min_tri or
                sum(n[i] * refn[i] for i in range(3)) < 1 - tol):
            continue
        d = sum(refn[i] * t[0][i] for i in range(3))
        e = acc.setdefault(round(d, 2), [0.0, 0.0])
        e[0] += d * a
        e[1] += a
    return sorted((v[0] / v[1], v[1]) for v in acc.values() if v[1] > min_area)


NORMALS = [("-x", (-1, 0, 0)), ("+x", (1, 0, 0)),
           ("-y", (0, -1, 0)), ("+y", (0, 1, 0)),
           ("-z", (0, 0, -1)), ("+z", (0, 0, 1)),
           ("seam-up", (0.0, -P.SEAM_SIN, P.SEAM_COS)),
           ("seam-down", (0.0, P.SEAM_SIN, -P.SEAM_COS))]


def check_engraving(tris):
    """The label is a pocket cut into the front wall.  What has to be true:
    it is as deep as asked, it does not get near the cavity, it sits inside the
    panel and clear of the face's edges, and it is centred."""
    floor_y = -P.EXT_HY + P.TEXT_DEPTH
    area, vol_expect = 0.0, 0.0
    xs, zs, ys_seen = [], [], set()
    for t in tris:
        n, a = tri_na(t)
        # the pocket floor faces OUT of the part (-y), at the engraving depth
        if n is None or n[1] > -1 + 1e-6 or abs(t[0][1] - floor_y) > 1e-4:
            continue
        area += a
        ys_seen.add(round(t[0][1], 4))
        xs += [v[0] for v in t]
        zs += [v[2] for v in t]
    if not xs:
        fail("no engraving pocket floor found at y=%.4f" % floor_y)
        return
    print("  pocket floor at y = %s   (asked: %.4f, i.e. %.2f deep)"
          % (sorted(ys_seen), floor_y, P.TEXT_DEPTH))
    if len(ys_seen) != 1:
        fail("the pocket floor is not one plane")

    # wall left between the pocket floor and the card cavity
    wall = -P.INT_HY - floor_y
    print("  wall left behind the text: %.4f mm   (need >= %.2f; the wall is "
          "%.4f thick)" % (wall, P.MIN_WALL_BEHIND_TEXT, P.WALL_Y))
    if wall < P.MIN_WALL_BEHIND_TEXT - 1e-6:
        fail("only %.3f mm of wall behind the text" % wall)

    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    print("  ink box   x [%8.3f, %8.3f] = %6.3f wide    z [%7.3f, %7.3f] = %6.3f tall"
          % (x0, x1, x1 - x0, z0, z1, z1 - z0))
    print("  panel     %.1f x %.1f, centred on x = 0, z = %.4f"
          % (P.PANEL_W, P.PANEL_H, P.PANEL_ZC))
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    if x1 - x0 > P.PANEL_W + 1e-6 or z1 - z0 > P.PANEL_H + 1e-6:
        fail("the text overflows its %.0f x %.0f panel" % (P.PANEL_W, P.PANEL_H))
    if abs(cx) > 0.01 or abs(cz - P.PANEL_ZC) > 0.01:
        fail("the text is %.3f, %.3f off the panel centre" % (cx, cz - P.PANEL_ZC))
    print("  ink centre offset from panel centre: dx %+.4f  dz %+.4f" %
          (cx, cz - P.PANEL_ZC))

    # clear of the face's own edges: the flat of the front face runs to the
    # corner tangent in x, and from the floor to the seam in z
    flat_x = P.EXT_HX - P.EXT_CORNER_R
    print("  margin to the face's edges: sides %.2f / %.2f mm, bottom %.2f mm, "
          "top %.2f mm" % (flat_x + x0, flat_x - x1, z0, P.Z_FRONT_TOP - z1))
    if min(flat_x + x0, flat_x - x1, z0, P.Z_FRONT_TOP - z1) < 1.0:
        fail("the text is within 1 mm of the edge of the front face")

    # What the engraving removed must be exactly floor area x depth.  If it is
    # more, the cutter reached something else; if less, it did not go the
    # depth that was asked.  The baseline is the same part built without it.
    plain = _export_plain_bottom()
    removed = _volume(plain) - _volume(tris)
    expect = area * P.TEXT_DEPTH
    print("  volume removed by the label %.2f mm^3   floor area x depth %.2f   "
          "(difference %+.3f, %.3f%%)" % (removed, expect, removed - expect,
                                          100.0 * (removed - expect) / expect))
    if abs(removed - expect) > 0.005 * expect:
        fail("the label removed %.1f mm^3, not the %.1f its floor implies"
             % (removed, expect))
    return area


def _export_plain_bottom():
    src = os.path.join(PART, ".check_plain.slvs")
    out = os.path.join(PART, ".check_plain.stl")
    builder.build_bottom(label=False).write(src)
    subprocess.run(["solvespace-cli", "export-mesh", "--chord-tol", "0.02",
                    "--output", out, src], capture_output=True)
    tris = load_stl(out)
    os.remove(src)
    os.remove(out)
    return tris


def _volume(tris):
    v = 0.0
    for a, b, c in tris:
        v += (a[0] * (b[1] * c[2] - b[2] * c[1]) -
              a[1] * (b[0] * c[2] - b[2] * c[0]) +
              a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return v


def main():
    print("=" * 72)
    print("0. sketch constraints: degrees of freedom and redundancy")
    print("=" * 72)
    print("  A group wants 0 dof and 0 redundant.  Neither a clean")
    print("  `solvespace-cli regenerate` nor a correct exported mesh can see a")
    print("  failure here -- the seeded Param values hide it, and only the GUI")
    print("  complains.  See spec 6.7.")
    for label, fn in (("bottom", builder.build_bottom),
                      ("top", builder.build_top)):
        print("  -- %s --" % label)
        sk = fn()
        if not print_dof_report(sk, sk.group_names):
            fail("%s has groups that are not cleanly constrained" % label)

    print()
    print("=" * 72)
    print("1. export and mesh health")
    print("=" * 72)
    import mesh_check
    rebuilt = {}
    for part, src in SLVS.items():
        out = os.path.join(HERE, "..", ".check_%s.stl" % part)
        out = os.path.normpath(out)
        if os.path.exists(out):
            os.remove(out)
        r = subprocess.run(["solvespace-cli", "export-mesh", "--chord-tol", "0.02",
                            "--output", out, src], capture_output=True, text=True)
        if not os.path.exists(out):
            fail("%s: solvespace-cli produced no mesh" % part)
            continue
        if "self-intersecting" in (r.stdout + r.stderr):
            fail("%s: solvespace reports a self-intersecting mesh" % part)
        tris = load_stl(out)
        rebuilt[part] = tris
        print("  %-7s %d triangles" % (part, len(tris)))
        res = mesh_check.check(out)
        os.remove(out)

    print()
    print("=" * 72)
    print("2. critical interior cavity (measured off the rebuilt meshes)")
    print("=" * 72)
    want = [("interior X", 2 * P.INT_HX, 70.0),
            ("interior Y", 2 * P.INT_HY, 76.5),
            ("interior Z", P.INT_H, 94.05)]
    # interior x/y from the bottom's cavity faces, z from floor to ceiling
    bx = planes(rebuilt["bottom"], (1, 0, 0))
    by = planes(rebuilt["bottom"], (0, 1, 0))
    # large triangles only: the engraving adds small upward-facing facets that
    # land within a bin-width of the floor and would otherwise blur it
    floor = max(planes(rebuilt["bottom"], (0, 0, 1), min_tri=20.0),
                key=lambda p: p[1])[0]
    ceil = -planes(rebuilt["top"], (0, 0, -1))[0][0]
    got = [bx[0][0] * -2, by[0][0] * -2, ceil - floor]
    got[0] = -2 * bx[0][0]
    got[1] = -2 * by[0][0]
    for (name, model, intent), g in zip(want, got):
        d = g - intent
        print("  %-11s design intent %8.3f   model %8.4f   measured %10.5f  "
              "delta vs intent %+9.5f" % (name, intent, model, g, d))
        if abs(d) > 0.002:
            fail("%s is %.4f off the design intent" % (name, d))

    print()
    print("=" * 72)
    print("2b. engraved label on the bottom's front face")
    print("=" * 72)
    check_engraving(rebuilt["bottom"])

    print()
    print("=" * 72)
    print("3. face planes: rebuild vs original (common frame, mm)")
    print("=" * 72)
    frames = {"bottom": TO_ORIG,
              "top": tuple(TO_ORIG[i] + TOP_OFF[i] for i in range(3))}
    for part in ("bottom", "top"):
        print("  -- %s --" % part)
        orig = load_stl(ORIG[part])
        if part == "top":
            orig = shift(orig, TOP_OFF)
        rb = shift(rebuilt[part], TO_ORIG)
        for name, ref in NORMALS:
            po, pr = planes(orig, ref), planes(rb, ref)
            if not po and not pr:
                continue
            for d_o, a_o in po:
                near = [(abs(d_r - d_o), d_r, a_r) for d_r, a_r in pr
                        if abs(d_r - d_o) < 0.1]
                if not near:
                    print("     %-9s orig %11.5f (A=%7.1f)   no rebuild face: "
                          "facets of an omitted fillet" % (name, d_o, a_o))
                    continue
                dd, d_r, a_r = min(near)
                expected = (part == "top" and name in ("-z", "+z")
                            and abs(dd - abs(TOP_OFF[2])) < 1e-4)
                if expected:
                    note = "   (expected: the original pair's own %.4f mm seam " \
                           "interference, which the rebuild removes)" % abs(TOP_OFF[2])
                elif dd < 0.002:
                    note = ""
                else:
                    note = "   <-- CHECK"
                print("     %-9s orig %11.5f   rebuild %11.5f   delta %+9.5f%s"
                      % (name, d_o, d_r, d_r - d_o, note))
                if dd > 0.002 and not expected:
                    fail("%s %s face off by %.5f mm" % (part, name, dd))

    print()
    print("=" * 72)
    print("4. assembly: does anything interfere, along vertical rays")
    print("=" * 72)
    print("  Each pair is seated with its seam planes coincident, which is how")
    print("  the halves meet in use.  Note the originals do NOT sit that way in")
    print("  their own files: as exported the original top is %.4f mm low in z,"
          % abs(TOP_OFF[2]))
    print("  so the original pair as shipped interferes by that much at the seam.")
    # everything in the REBUILD frame; the originals come back by -TO_ORIG
    def to_rebuild(tris, part):
        d = [-TO_ORIG[i] for i in range(3)]
        t = shift(tris, [-x for x in TOP_OFF]) if False else tris
        return shift(tris, d)

    ob = shift(load_stl(ORIG["bottom"]), [-c for c in TO_ORIG])
    ot = shift(shift(load_stl(ORIG["top"]), TOP_OFF), [-c for c in TO_ORIG])
    pairs = [("rebuild bottom + rebuild top", rebuilt["bottom"], rebuilt["top"]),
             ("rebuild bottom + ORIGINAL top", rebuilt["bottom"], ot),
             ("ORIGINAL bottom + rebuild top", ob, rebuilt["top"]),
             ("ORIGINAL bottom + ORIGINAL top", ob, ot)]
    # A grid of columns over the wall band, where the lip and groove live.
    # The offsets are deliberately scruffy: a column that lands exactly on a
    # corner round's tangent line hits that silhouette edge dead-on and the
    # parity count comes back with a spurious sub-millimetre sliver, which then
    # reads as interference.  Nothing here is at a round number.
    cols = []
    n = 17
    jx, jy = 0.0731, 0.0417
    for i in range(n):
        f = (i + 0.5) / n
        y = -P.EXT_HY + 2 * P.EXT_HY * f + jy
        for x in (-0.5 * (P.EXT_HX + P.LIP_HX), 0.5 * (P.EXT_HX + P.LIP_HX),
                  -0.5 * (P.LIP_HX + P.INT_HX), 0.5 * (P.LIP_HX + P.INT_HX)):
            cols.append((x + jx, y))
        x = -P.EXT_HX + 2 * P.EXT_HX * f + jx
        for y2 in (-0.5 * (P.EXT_HY + P.LIP_HY), 0.5 * (P.EXT_HY + P.LIP_HY),
                   -0.5 * (P.LIP_HY + P.INT_HY), 0.5 * (P.LIP_HY + P.INT_HY)):
            cols.append((x, y2 + jy))
    # and the four corners, where the lip's rounded corner meets the groove's
    # sharp one -- the walls alone would never sample that
    for sx in (-1, 1):
        for sy in (-1, 1):
            for fx, fy in ((0.5, 0.5), (0.85, 0.3), (0.3, 0.85)):
                cols.append((sx * (P.INT_HX + fx * (P.EXT_HX - P.INT_HX)),
                             sy * (P.INT_HY + fy * (P.EXT_HY - P.INT_HY))))
    cols = [(x, y) for x, y in cols
            if abs(x) < P.EXT_HX - 0.2 and abs(y) < P.EXT_HY - 0.2]
    for label, A, B in pairs:
        worst, where = 0.0, None
        for x, y in cols:
            o = overlap(ray_spans(A, x, y), ray_spans(B, x, y))
            if o > worst:
                worst, where = o, (x, y)
        # the mating faces are designed to touch exactly, so anything under a
        # micron is the ray cast's own noise, not overlap
        verdict = "clear (touching)" if worst < 1e-3 else \
            "interference %.5f mm at x=%.3f y=%.3f" % (worst, where[0], where[1])
        print("  %-32s %s" % (label, verdict))
        if label == "rebuild bottom + rebuild top" and worst >= 1e-3:
            fail("the rebuilt pair interferes by %.5f mm" % worst)

    print()
    print("=" * 72)
    if FAIL:
        print("%d CHECK(S) FAILED" % len(FAIL))
        for m in FAIL:
            print("  - " + m)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
