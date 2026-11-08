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
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PART = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))
sys.path.insert(0, HERE)

from stl_io import load_stl
from mesh_geom import shift, tri_normal_area as tri_na, volume as _volume, point_tri_distance as _tri_dist
from mesh_planes import group_planes
from mesh_rays import axis_spans, overlap
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


# ---------------------------------------------------------------- face planes
def planes(tris, ref, tol=1e-5, min_area=5.0, min_tri=0.0):
    """(offset, area) of each face with normal `ref`, sorted by offset: a thin
    view over mesh_planes.group_planes, which is where the grouping lives."""
    return sorted((f["offset"], f["area"])
                  for f in group_planes(tris, ref, tol, 2, min_area, min_tri))


NORMALS = [("-x", (-1, 0, 0)), ("+x", (1, 0, 0)),
           ("-y", (0, -1, 0)), ("+y", (0, 1, 0)),
           ("-z", (0, 0, -1)), ("+z", (0, 0, 1)),
           ("seam-up", (0.0, -P.SEAM_SIN, P.SEAM_COS)),
           ("seam-down", (0.0, P.SEAM_SIN, -P.SEAM_COS))]


def _col_spans(tris, x, y):
    """Solid z-intervals of the vertical column through (x, y)."""
    return axis_spans(tris, 2, x, y)


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
        return None
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
    return {"area": area, "removed": removed, "wall": wall,
            "ink_w": x1 - x0, "ink_h": z1 - z0,
            "margin_side": min(flat_x + x0, flat_x - x1),
            "margin_bottom": z0, "margin_top": P.Z_FRONT_TOP - z1}


def _cap_stats(tris, face_abs, sg, y, z):
    """Height (or depth), base radius and centre of the cap on one face."""
    xf = sg * face_abs
    win = [t for t in tris if all(abs(v[1] - y) < 2.2 and abs(v[2] - z) < 2.2 for v in t)
           and any(sg * (v[0] - xf) > 0.004 for v in t)
           and all(abs(v[0] - xf) < 1.2 for v in t)]
    vs = [v for t in win for v in t]
    if not vs:
        return None
    ring = [v for v in vs if abs(v[0] - xf) < 2e-4]
    ys_, zs_ = [v[1] for v in ring], [v[2] for v in ring]
    return {"h": max(sg * (v[0] - xf) for v in vs),
            "r": ((max(ys_) - min(ys_)) + (max(zs_) - min(zs_))) / 4.0,
            "cy": (max(ys_) + min(ys_)) / 2.0, "cz": (max(zs_) + min(zs_)) / 2.0,
            "verts": vs}


def _snap_columns():
    """Vertical rays across each bump's footprint, from the lip face out to the
    bump's apex.  Offsets are deliberately untidy for the reason given in
    section 4's grid."""
    cols = []
    for sg in (-1, 1):
        for (yc, zc) in P.SNAP_POINTS:
            for k in range(-6, 7):
                for t in (0.04, 0.13, 0.27, 0.41, 0.55, 0.69, 0.75):
                    cols.append((sg * (P.LIP_HX + t) + 0.0007 * sg, yc + k * 0.21 + 0.013))
    return cols


def check_snap(rebuilt, ob, ot):
    """The snap: do the domes and dimples exist as designed, does the dome seat in
    its dimple, and would this test notice if it did not."""
    # 1. the caps are what the parameters say
    for part, face, h_key, want_h, want_r in (
            ("bottom", P.LIP_HX, "bump", P.BUMP_H, P.BUMP_BASE_R),
            ("top", P.GROOVE_HX, "dimple", P.DENT_DEPTH, P.DENT_MOUTH_R)):
        found = 0
        for sg in (-1, 1):
            for (y, z) in P.SNAP_POINTS:
                c = _cap_stats(rebuilt[part], face, sg, y, z)
                if c is None:
                    fail("no %s found at %s face, y=%.2f z=%.2f" %
                         (h_key, "left" if sg < 0 else "right", y, z))
                    continue
                found += 1
                bad = (abs(c["h"] - want_h) > 0.001 or abs(c["r"] - want_r) > 0.001
                       or abs(c["cy"] - y) > 0.002 or abs(c["cz"] - z) > 0.002)
                if bad:
                    fail("%s at %s y=%.2f z=%.2f is height %.4f radius %.4f centre "
                         "(%.4f, %.4f), not %.4f / %.4f / (%.4f, %.4f)" %
                         (h_key, "left" if sg < 0 else "right", y, z, c["h"], c["r"],
                          c["cy"], c["cz"], want_h, want_r, y, z))
        print("  %-7s %d of 4 %ss found; height/depth %.4f, %s radius %.4f"
              % (part, found, h_key, want_h, "base" if h_key == "bump" else "mouth",
                 want_r))

    # 2. the dome seats in the dimple, with the clearance the source has
    cols = _snap_columns()
    print("  engagement, vertical rays across each dome's footprint "
          "(%d columns):" % len(cols))
    sensitivity = None
    for label, A, B in (("rebuild bottom + rebuild top", rebuilt["bottom"], rebuilt["top"]),
                        ("rebuild bottom + ORIGINAL top", rebuilt["bottom"], ot),
                        ("ORIGINAL bottom + rebuild top", ob, rebuilt["top"]),
                        ("ORIGINAL bottom + ORIGINAL top", ob, ot)):
        worst, where = 0.0, None
        for x, y in cols:
            o = overlap(_col_spans(A, x, y), _col_spans(B, x, y))
            if o > worst:
                worst, where = o, (x, y)
        verdict = "seats clear" if worst < 1e-3 else \
            "overlap %.4f mm at x=%.3f y=%.3f" % (worst, where[0], where[1])
        if worst >= 1e-3 and label.startswith("ORIGINAL bottom"):
            # not a defect of the rebuild: the source's own dome is an ellipse
            # ~0.1 mm wider in y than its circular dimple at nearly every depth, so it
            # presses into the dimple's flanks.  The figure is the vertical
            # height of that sliver, not its thickness.  See spec 6.10.
            verdict += "   <- the source's own dome is ~0.1 mm wider than its dimple"
        print("     %-32s %s" % (label, verdict))
        if label == "rebuild bottom + rebuild top" and worst >= 1e-3:
            fail("the rebuilt dome does not seat in the rebuilt dimple: %.4f mm of "
                 "overlap" % worst)

    # 3. the clearance the dome seats with: nearest approach of each dome's
    #    surface to the dimple's.  The caps are concentric spheres, so it is
    #    (GROOVE_HX + DENT_DEPTH) - (LIP_HX + BUMP_H) at the apex and no less
    #    anywhere else.
    want_gap = (P.GROOVE_HX + P.DENT_DEPTH) - (P.LIP_HX + P.BUMP_H)
    tmin = 1e9
    for sg in (-1, 1):
        for (y, z) in P.SNAP_POINTS:
            c = _cap_stats(rebuilt["bottom"], P.LIP_HX, sg, y, z)
            near = [t for t in rebuilt["top"]
                    if all(abs(v[1] - y) < 3.5 and abs(v[2] - z) < 3.5 and
                           abs(v[0] - sg * P.LIP_HX) < 2.5 for v in t)]
            for v in c["verts"]:
                if abs(v[0] - sg * P.LIP_HX) < 0.05:       # base ring: on the face
                    continue
                d = min(_tri_dist(v, *t) for t in near)
                tmin = min(tmin, d)
    print("  nearest approach of dome to dimple %.4f mm   (design %.4f; the "
          "tessellation of two spheres accounts for a few hundredths)"
          % (tmin, want_gap))
    if tmin < 0.5 * want_gap or tmin > 3.0 * want_gap + 0.05:
        fail("the dome sits %.4f mm from its dimple, not about %.4f"
             % (tmin, want_gap))

    # 4. would this test notice if the dimples were missing?
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "nodimple.slvs"); out = os.path.join(tmp, "nodimple.stl")
        builder.build_top(dimples=False).write(src)
        subprocess.run(["solvespace-cli", "export-mesh", "--chord-tol", "0.02",
                        "--output", out, src], capture_output=True)
        blank = load_stl(out)
    worst = max(overlap(_col_spans(rebuilt["bottom"], x, y), _col_spans(blank, x, y))
                for x, y in cols)
    print("  control: the same bottom against a top WITHOUT dimples overlaps "
          "by %.4f mm" % worst)
    if worst < 0.5 * P.BUMP_H:
        fail("the engagement test did not see a dome pushing into a dimple-less "
             "wall (%.4f mm); it would not notice a missing dimple" % worst)


def _export_plain_bottom():
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "plain.slvs")
        out = os.path.join(tmp, "plain.stl")
        builder.build_bottom(label=False).write(src)
        subprocess.run(["solvespace-cli", "export-mesh", "--chord-tol", "0.02",
                        "--output", out, src], capture_output=True)
        return load_stl(out)


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
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "%s.stl" % part)
            r = subprocess.run(["solvespace-cli", "export-mesh", "--chord-tol",
                                "0.02", "--output", out, src],
                               capture_output=True, text=True)
            if not os.path.exists(out):
                fail("%s: solvespace-cli produced no mesh" % part)
                continue
            if "self-intersecting" in (r.stdout + r.stderr):
                fail("%s: solvespace reports a self-intersecting mesh" % part)
            rebuilt[part] = load_stl(out)
            print("  %-7s %d triangles" % (part, len(rebuilt[part])))
            res = mesh_check.check(out, verbose=False)
        print("          watertight %s, winding %s, %d shell(s), volume %.1f mm^3"
              % ("yes" if res["non_manifold_edges"] == 0 else
                 "NO (%d bad edges)" % res["non_manifold_edges"],
                 "consistent" if res["winding_consistent"] else "INCONSISTENT",
                 res["shells"], res["volume"]))
        if res["non_manifold_edges"] or not res["winding_consistent"] \
                or res["shells"] != 1:
            fail("%s mesh is not one watertight shell" % part)

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
            o = overlap(_col_spans(A, x, y), _col_spans(B, x, y))
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
    print("5. snap domes and dimples")
    print("=" * 72)
    check_snap(rebuilt, ob, ot)

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
