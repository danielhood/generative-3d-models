#!/usr/bin/env python3
"""Verify the adjustable case: the tray, the lid and the divider.

    python3 cad/check_case.py

Exports all three through SolveSpace and measures the MESHES, not the parameters.

  0. every sketch group is fully constrained                (slvs_write.dof_report)
  1. each part is one watertight shell
  2. the footprint fits the 250 x 250 mm bed
  3. the lanes: three, each the single box's cavity width, the full depth, no cross walls
  4. the outer walls, lip and groove are the single box's
  5. heights, and the card space
  6. the lane walls: four, 5 mm, in the tray and the lid; the holes and slits in them
  7. the snap: 12 domes and 12 dimples, as in the 3 x 3 case, centred on the lanes
  8. the finger ledge on the front of each half
  9. assembly: tray and lid; the divider in every lane at the ends and middle of the
     holes; its clearances; that it hangs on its bridges; the neighbours rule
 10. the committed STL files, the ones that get printed, are the current design

Every check is written so that the error it exists to catch would fail it, and each
group of checks ends with a CONTROL: the same test run on a part built wrongly on
purpose, which must fail.  Exit status 0 only if everything passed.
"""
import os
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PART = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))
sys.path.insert(0, HERE)

import mesh_check
from mesh_features import features_beyond
from mesh_geom import bbox, point_tri_distance, shift
from mesh_rays import axis_spans, overlap
from slvs_cli import export_mesh
from slvs_write import dof_report
from stl_io import load_stl
import case_params as C
import build_case as builder

B = C.B                                   # the single box's parameters
FAIL = []
TOL = 1e-3


def fail(msg):
    FAIL.append(msg)
    print("  FAIL  " + msg)


def ok(msg):
    print("  ok    " + msg)


def export(S, name):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, name + ".slvs")
        S.write(src)
        r = export_mesh(src, 0.02)
    if r["tris"] is None or r["boolean_failed"] or r["self_intersecting"]:
        fail("%s: no usable mesh from SolveSpace (%s)" % (name, r["messages"][:2]))
    return r["tris"]


def health(tris):
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "m.stl")
        with open(p, "wb") as fh:
            fh.write(b"\0" * 80 + struct.pack("<I", len(tris)))
            for t in tris:
                fh.write(struct.pack("<12fH", 0, 0, 0, *[c for v in t for c in v], 0))
        return mesh_check.check(p, verbose=False)


def runs(spans):
    """Lengths of solid runs, and of the gaps between them."""
    return ([hi - lo for lo, hi in spans],
            [spans[i + 1][0] - spans[i][1] for i in range(len(spans) - 1)])


def near(a, b, tol=TOL):
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def window(tris, x0, x1, y0, y1):
    """The triangles touching an x-y window: a much smaller mesh to ray-cast."""
    return [t for t in tris if max(v[0] for v in t) >= x0 and min(v[0] for v in t) <= x1
            and max(v[1] for v in t) >= y0 and min(v[1] for v in t) <= y1]


def yband(cy):
    """A y window for ray-casting along a hole column.  A ray along y needs air at both
    ends of its window or the in/out parity is wrong; hole centres are air, and 8 mm is
    two pitches, so cy +- 8 is a hole centre.  Near the front and back walls the window
    opens out past the part instead (where the ray starts in air too)."""
    lo, hi = cy - 8.0, cy + 8.0
    if lo < -C.IN_HY + 4.0:
        lo = -130.0
    if hi > C.IN_HY - 4.0:
        hi = 130.0
    return lo, hi


def col_overlap(a, b, columns):
    worst, where = 0.0, None
    for x, y in columns:
        o = overlap(axis_spans(a, 2, x, y), axis_spans(b, 2, x, y))
        if o > worst:
            worst, where = o, (x, y)
    return worst, where


# ---------------------------------------------------------------------------
# the lane walls and holes, as one function so the control can run it too
# ---------------------------------------------------------------------------
def wall_problems(tray, label):
    """Everything wrong with the tray's holes and slits, measured off the mesh."""
    bad = []
    web = C.HOLE_YS[0] + C.HOLE_PITCH / 2.0 + 0.0137          # between the first two holes
    for cx, kind in zip(C.WALL_CENTRES_X, C.WALL_KINDS):
        # the column of holes: along y through the wall's middle
        sp = axis_spans(tray, 1, cx, 40.0)
        gaps = [sp[i + 1][0] - sp[i][1] for i in range(len(sp) - 1)]
        cen = [(sp[i + 1][0] + sp[i][1]) / 2.0 for i in range(len(sp) - 1)]
        if len(gaps) != C.HOLE_N or any(abs(g - C.HOLE) > TOL for g in gaps) or \
                any(abs(a - b) > TOL for a, b in zip(cen, C.HOLE_YS)):
            bad.append("%s %s wall: %d holes along y (want %d of %.1f at pitch %.1f)"
                       % (label, kind, len(gaps), C.HOLE_N, C.HOLE, C.HOLE_PITCH))
        # a hole's width across the wall, and its depth
        y = C.HOLE_YS[7]
        sx = axis_spans(tray, 0, y, 40.0)
        want_lo, want_hi = cx - C.HOLE / 2.0, cx + C.HOLE / 2.0
        if not any(abs(sx[i][1] - want_lo) < TOL and abs(sx[i + 1][0] - want_hi) < TOL for i in range(len(sx) - 1)):
            bad.append("%s %s wall: the hole at y=%.1f is not x = %.3f .. %.3f" % (label, kind, y, want_lo, want_hi))
        sz = axis_spans(tray, 2, cx, y)
        if not sz or abs(sz[0][1] - C.HOLE_BOTTOM) > TOL:
            bad.append("%s %s wall: the hole's bottom is z=%s, want %.4f (%.1f deep)"
                       % (label, kind, "%.4f" % sz[0][1] if sz else "absent", C.HOLE_BOTTOM, C.HOLE_DEPTH))
        # the wall's top between holes
        sw = axis_spans(tray, 2, cx, web)
        if not sw or abs(sw[0][1] - C.WALL_TOP) > TOL:
            bad.append("%s %s wall: top between holes is z=%s, want %.4f" % (label, kind, "%.4f" % sw[0][1] if sw else "absent", C.WALL_TOP))
        # the slits: skins either side of the hole, at a hole and between holes
        for side, off in (("left", -(C.HOLE / 2.0 + C.SKIN / 2.0)), ("right", C.HOLE / 2.0 + C.SKIN / 2.0)):
            slit = (kind == "part") or (kind == "liner-l" and side == "right") or (kind == "liner-r" and side == "left")
            want = C.WALL_TOP - C.SLIT_H if slit else C.WALL_TOP
            s = axis_spans(tray, 2, cx + off, y)
            top = s[0][1] if s else None
            if top is None or abs(top - want) > TOL:
                bad.append("%s %s wall, %s skin at a hole: top z=%s, want %.4f (%s)"
                           % (label, kind, side, "%.4f" % top if top else "absent", want, "slit" if slit else "no slit"))
    return bad


# ---------------------------------------------------------------------------
# the finger ledge (the 3 x 3 case's test, unchanged)
# ---------------------------------------------------------------------------
def ledge_front(x):
    ax = abs(x)
    if ax <= C.LEDGE_FLAT_HX:
        return -C.EXT_HY - C.LEDGE_OUT
    if ax >= C.LEDGE_HX:
        return -C.EXT_HY
    yc = -C.EXT_HY - C.LEDGE_OUT + C.LEDGE_FLANK_R
    return yc - (C.LEDGE_FLANK_R ** 2 - (ax - C.LEDGE_FLAT_HX) ** 2) ** 0.5


def ledge_problems(tris, z0, z1, label):
    bad = []
    zm = (z0 + z1) / 2.0
    lo, hi = bbox(tris)
    if abs(lo[1] - (-C.EXT_HY - C.LEDGE_OUT)) > 0.01:
        bad.append("%s: frontmost point y = %.4f, want %.4f" % (label, lo[1], -C.EXT_HY - C.LEDGE_OUT))
    xs = [0.0, 20.0, C.LEDGE_FLAT_HX - 0.4, C.LEDGE_FLAT_HX + 0.4, C.LEDGE_FLAT_HX + 8.0,
          C.LEDGE_FLAT_HX + 16.0, C.LEDGE_HX - 3.0, C.LEDGE_HX + 2.0, C.LEDGE_HX + 20.0]
    for x in xs + [-v for v in xs[1:]]:
        sp = axis_spans(tris, 1, x + 0.0137, zm)
        want = ledge_front(x + 0.0137)
        if not sp or abs(sp[0][0] - want) > 0.03:
            bad.append("%s: front face at x=%+.2f is y=%s, want %.4f" % (label, x, "%.4f" % sp[0][0] if sp else "absent", want))
    for x in (0.0, 30.0, -45.0):
        sp = axis_spans(tris, 2, x + 0.0137, -C.EXT_HY - C.LEDGE_OUT / 2.0)
        if len(sp) != 1 or abs(sp[0][0] - z0) > TOL or abs(sp[0][1] - z1) > TOL:
            bad.append("%s: through the ledge at x=%+.1f, solid z = %s, want %.4f..%.4f"
                       % (label, x, [(round(a, 4), round(b, 4)) for a, b in sp], z0, z1))
    for x in (C.LEDGE_HX + 6.0, -C.LEDGE_HX - 6.0, 100.0, -100.0):
        if axis_spans(tris, 2, x, -C.EXT_HY - 0.3):
            bad.append("%s: something stands proud of the wall at x=%+.1f" % (label, x))
    return bad


# ---------------------------------------------------------------------------
def main():
    print("=" * 72)
    print("0. sketch constraints")
    print("=" * 72)
    for label, fn in (("tray", builder.build_bottom), ("lid", builder.build_top), ("divider", builder.build_divider)):
        S = fn()
        rows = [r for r in dof_report(S, S.group_names) if r["equations"]]
        bad = [r["name"] for r in rows if r["dof"] or r["redundant"] or r["residual"] > 1e-7]
        (ok if not bad else fail)("%s: %d of %d constrained groups are 0 DOF, 0 redundant%s"
                                  % (label, len(rows) - len(bad), len(rows), "" if not bad else "; bad: %s" % bad))

    tray = export(builder.build_bottom(), "tray")
    lid = export(builder.build_top(), "lid")
    div = export(builder.build_divider(), "divider")
    if not tray or not lid or not div:
        return 1

    print()
    print("=" * 72)
    print("1. the meshes")
    print("=" * 72)
    for name, t in (("tray", tray), ("lid", lid), ("divider", div)):
        h = health(t)
        good = not h["non_manifold_edges"] and h["winding_consistent"] and h["shells"] == 1
        (ok if good else fail)("%s: %d triangles, %s, %d shell(s), volume %.1f mm^3"
                               % (name, h["triangles"], "watertight" if not h["non_manifold_edges"] else "NOT WATERTIGHT",
                                  h["shells"], h["volume"]))

    print()
    print("=" * 72)
    print("2. print bed (250 x 250 mm)")
    print("=" * 72)
    for name, t in (("tray", tray), ("lid", lid)):
        lo, hi = bbox(t)
        w, d = hi[0] - lo[0], hi[1] - lo[1]
        (ok if w < C.BED and d < C.BED else fail)("%s footprint %.3f x %.3f mm  (margin %.2f x %.2f)"
                                                  % (name, w, d, C.BED - w, C.BED - d))

    print()
    print("=" * 72)
    print("3. the lanes")
    print("=" * 72)
    web_y = C.HOLE_YS[0] + C.HOLE_PITCH / 2.0 + 0.0137          # between two holes, so no slit
    for name, t, z in (("tray", tray, 30.0), ("lid", lid, 90.0)):
        solid, gap = runs(axis_spans(t, 0, web_y, z))
        want_solid = [C.WALL_X + C.WALL_T, C.WALL_T, C.WALL_T, C.WALL_X + C.WALL_T]
        (ok if near(gap, [C.LANE_W] * 3) and near(solid, want_solid) else fail)(
            "%s across x at y=%.2f: lanes %s, walls %s  (want %.4f x3 between %s)"
            % (name, web_y, [round(g, 4) for g in gap], [round(s, 4) for s in solid], C.LANE_W,
               [round(s, 4) for s in want_solid]))
    for lx in C.LANE_CENTRES_X:                    # along y through each lane's middle: no cross walls
        solid, gap = runs(axis_spans(tray, 1, lx, 30.0))
        (ok if near(solid, [C.WALL_Y, C.WALL_Y]) and near(gap, [2 * C.IN_HY]) else fail)(
            "tray along y through lane x=%+.2f: the lane is %.4f long, walls %s, nothing across it"
            % (lx, gap[0] if gap else -1, [round(s, 4) for s in solid]))
    (ok if abs(C.LANE_W - 2 * B.INT_HX) < 1e-9 else fail)("a lane is exactly the single box's cavity width, %.4f" % C.LANE_W)
    (ok if abs(2 * C.IN_HY - (3 * 2 * B.INT_HY + 2 * 1.6)) < 1e-9 else fail)(
        "the interior depth is the 3 x 3 case's, %.4f" % (2 * C.IN_HY))
    # the lane faces are smooth below the slits: the lane's width at a hole is the same as between holes
    smooth = True
    for y, want in ((C.HOLE_YS[3], [C.HOLE, C.LANE_W, C.HOLE, C.LANE_W, C.HOLE, C.LANE_W, C.HOLE]),
                    (web_y, [C.LANE_W] * 3), (C.HOLE_YS[40], [C.HOLE, C.LANE_W, C.HOLE, C.LANE_W, C.HOLE, C.LANE_W, C.HOLE])):
        for z in (6.0, 20.0, 45.0, 70.0):
            _, gap = runs(axis_spans(tray, 0, y, z))
            w_ = [C.LANE_W] * 3 if z < C.HOLE_BOTTOM else want      # below the holes' bottom the walls are solid
            if not near(gap, w_):            # at a hole: the hole's 2.0 in each wall, the lane's width between
                smooth = False
                fail("across x at y=%.2f z=%.1f the gaps are %s, want %s (a lane face is not smooth)"
                     % (y, z, [round(g, 4) for g in gap], [round(g, 4) for g in w_]))
    if smooth:
        ok("the lane faces are smooth: %.4f wide at holes and between them, z = 6 to 70, below the slits" % C.LANE_W)

    print()
    print("=" * 72)
    print("4. outer walls, lip and groove: the single box's")
    print("=" * 72)
    zt, zl = C.Z_LIP - 0.07, C.Z_S + 5.0                       # the lip alone; the lid's groove wall alone
    y2 = 2.0
    sx = axis_spans(tray, 0, y2, zt)
    sy = axis_spans(tray, 1, 0.0 + 0.0137, zt)
    lipx, lipy = (sx[0][1] - sx[0][0]) if sx else -1, (sy[0][1] - sy[0][0]) if sy else -1
    (ok if abs(lipx - B.LIP_T_X) < TOL and abs(lipy - B.LIP_T_Y) < TOL else fail)(
        "lip thickness x %.4f, y %.4f   (single box %.4f, %.4f)" % (lipx, lipy, B.LIP_T_X, B.LIP_T_Y))
    lx_ = axis_spans(lid, 0, y2, zl)
    ly_ = axis_spans(lid, 1, 0.0 + 0.0137, zl)
    gx = sx[0][0] - lx_[0][1] if sx and lx_ else None
    gy = sy[0][0] - ly_[0][1] if sy and ly_ else None
    (ok if gx is not None and abs(gx - B.CLEAR_X) < TOL and abs(gy - B.CLEAR_Y) < TOL else fail)(
        "lip-to-groove clearance x %.5f, y %.5f   (single box %.5f, %.5f)"
        % (gx if gx is not None else -1, gy if gy is not None else -1, B.CLEAR_X, B.CLEAR_Y))
    wlx, wly = lx_[0][1] - lx_[0][0], ly_[0][1] - ly_[0][0]
    (ok if abs(wlx - (C.EXT_HX - C.GROOVE_HX)) < TOL and abs(wly - (C.EXT_HY - C.GROOVE_HY)) < TOL else fail)(
        "the lid's wall beside the groove is %.4f (x), %.4f (y) thick" % (wlx, wly))
    wx = axis_spans(tray, 0, web_y, 30.0)
    wy = axis_spans(tray, 1, 0.0 + 0.0137, 30.0)
    (ok if abs((wx[0][1] - wx[0][0]) - (B.WALL_X + C.WALL_T)) < TOL and abs((wy[0][1] - wy[0][0]) - B.WALL_Y) < TOL else fail)(
        "the tray's outer walls are %.4f (x, beside the %.1f liner), %.4f (y)   (single box %.4f, %.4f)"
        % (wx[0][1] - wx[0][0] - C.WALL_T, C.WALL_T, wy[0][1] - wy[0][0], B.WALL_X, B.WALL_Y))

    print()
    print("=" * 72)
    print("5. heights")
    print("=" * 72)
    tlo, thi = bbox(tray)
    llo, lhi = bbox(lid)
    sb = bbox(load_stl(os.path.join(PART, "..", "mtg-deck-boxes", "ultra_guard_pro_100_bottom.stl")))
    single_h = sb[1][2] - sb[0][2]
    (ok if abs((thi[2] - tlo[2]) - single_h) < 0.01 else fail)(
        "tray is %.4f tall; the single bottom's STL is %.4f tall" % (thi[2] - tlo[2], single_h))
    (ok if abs(tlo[2]) < TOL else fail)("tray underside at z = %.4f" % tlo[2])
    (ok if abs(llo[2] - C.Z_S) < TOL and abs(lhi[2] - C.H_TOTAL) < TOL else fail)(
        "lid spans z = %.4f .. %.4f (%.4f tall); seam at %.4f" % (llo[2], lhi[2], lhi[2] - llo[2], C.Z_S))
    fl, cl = axis_spans(tray, 2, 0.0, y2), axis_spans(lid, 2, 0.0, y2)
    card = cl[0][0] - fl[0][1] if fl and cl else None
    (ok if card is not None and abs(card - B.INT_H) < TOL else fail)(
        "card space, tray floor to lid ceiling, %.4f   (single box %.4f)" % (card or -1, B.INT_H))
    zw = axis_spans(tray, 2, C.EXT_HX - 1.0, y2)
    (ok if zw and abs(zw[0][1] - C.Z_S) < TOL else fail)("the tray's outer wall stops at the seam, z = %.4f" % zw[0][1])
    zp = axis_spans(tray, 2, C.IN_HX + 0.9, y2)
    (ok if zp and abs(zp[0][1] - C.Z_LIP) < TOL else fail)("the lip stands to z = %.4f, %.4f above the seam" % (zp[0][1], zp[0][1] - C.Z_S))

    print()
    print("=" * 72)
    print("6. the lane walls, holes and slits")
    print("=" * 72)
    bad = wall_problems(tray, "tray")
    for m in bad:
        fail(m)
    if not bad:
        ok("tray: four 5 mm walls, each with %d holes %.1f square at pitch %.1f (first %.1f, last %+.1f), "
           "%.1f deep (bottom z=%.2f); every wall's top between holes z=%.4f"
           % (C.HOLE_N, C.HOLE, C.HOLE_PITCH, C.HOLE_YS[0], C.HOLE_YS[-1], C.HOLE_DEPTH, C.HOLE_BOTTOM, C.WALL_TOP))
        ok("slits: the top %.1f mm of the lane-side skin at every hole; partitions slit on both sides, liners on the lane "
           "side only (the outer skin keeps its full height)" % C.SLIT_H)
    sw = [axis_spans(tray, 2, cx, web_y) for cx in C.WALL_CENTRES_X]
    lw = [axis_spans(lid, 2, cx, web_y) for cx in C.WALL_CENTRES_X]
    gapw = [lw[i][-1][0] - sw[i][0][1] if lw[i] and sw[i] else None for i in range(4)]
    # the lid's wall is the topmost solid in its column; its bottom is the last span's start
    lbot = [lw[i][0][0] if lw[i] else None for i in range(4)]
    (ok if all(b is not None and abs(b - C.LID_WALL_BOTTOM) < TOL for b in lbot) else fail)(
        "lid: all four walls hang to z = %s, %.2f over the lip's top plane" % ([round(b, 4) for b in lbot], C.DIV_GAP))
    (ok if all(abs(lbot[i] - sw[i][0][1] - 2 * C.DIV_GAP) < TOL for i in range(4)) else fail)(
        "where a tray wall meets a lid wall the gap is %.4f" % (lbot[0] - sw[0][0][1]))
    for cx in C.WALL_CENTRES_X:                    # the lid's walls run front to back, unbroken, no holes
        s = axis_spans(lid, 1, cx, 90.0)
        if len(s) != 1 or abs((s[0][1] - s[0][0]) - 2 * C.EXT_HY) > TOL:
            fail("lid wall at x=%+.2f: %d solid runs along y at z=90, want one front to back" % (cx, len(s)))
    ok("lid: each wall is one unbroken run front to back (no holes in the lid)")
    sol = [axis_spans(lid, 0, y, 90.0) for y in (C.HOLE_YS[0], C.HOLE_YS[20], C.HOLE_YS[50])]
    (ok if all(len(s) == 4 for s in sol) else fail)("lid across x at three depths: always 4 runs (the same four walls everywhere)")
    nohole = export(builder.build_bottom(holes=False), "tray-noholes")
    wb = wall_problems(nohole, "tray")
    (ok if len(wb) >= 12 else fail)("control: the tray built WITHOUT holes fails the hole test %d ways (the test can fail)" % len(wb))

    print()
    print("=" * 72)
    print("7. snap domes and dimples")
    print("=" * 72)
    specs_t = builder.snap_specs(C.LIP_HX, C.LIP_HY)
    specs_l = builder.snap_specs(C.GROOVE_HX, C.GROOVE_HY)

    def measure(tris, specs, name, want_h, want_r, above):
        found = 0
        for tag, face, sg, across, along, _ in specs:
            axis = 0 if along == "x" else 1
            win = (across - 2.2, across + 2.2, C.DOME_Z - 2.2, C.DOME_Z + 2.2)
            fs = features_beyond(tris, axis, face, sg, window=win, max_off=1.2,
                                 keep=(lambda t: min(v[2] for v in t) > C.Z_S + 0.5) if above else None)
            if len(fs) != 1:
                fail("%s %s: %d features found, expected 1" % (name, tag, len(fs)))
                continue
            f = fs[0]
            r = (f["half_extents"][0] + f["half_extents"][1]) / 2.0
            if (abs(f["height"] - want_h) > 0.002 or abs(r - want_r) > 0.003 or
                    abs(f["centre"][0] - across) > 0.005 or abs(f["centre"][1] - C.DOME_Z) > 0.005):
                fail("%s %s: height %.4f radius %.4f centre (%.4f, %.4f); want %.4f / %.4f / (%.4f, %.4f)"
                     % (name, tag, f["height"], r, f["centre"][0], f["centre"][1], want_h, want_r, across, C.DOME_Z))
            else:
                found += 1
        return found

    nb = measure(tray, specs_t, "dome", C.BUMP_H, B.BUMP_BASE_R, True)
    nd = measure(lid, specs_l, "dimple", C.DENT_DEPTH, B.DENT_MOUTH_R, False)
    (ok if nb == 12 else fail)("tray: %d of 12 domes measure to the single box's dome (height %.4f, base radius %.3f)" % (nb, C.BUMP_H, B.BUMP_BASE_R))
    (ok if nd == 12 else fail)("lid: %d of 12 dimples measure to the single box's dimple (depth %.4f, mouth radius %.3f)" % (nd, C.DENT_DEPTH, B.DENT_MOUTH_R))
    for sg in (-1, 1):
        for axis, face_abs in ((0, C.LIP_HX), (1, C.LIP_HY)):
            fs = features_beyond(tray, axis, sg * face_abs, sg, max_off=1.2, keep=lambda t: min(v[2] for v in t) > C.Z_S + 0.5)
            if len(fs) != 3:
                fail("the tray's %s%s lip face carries %d domes, expected 3" % ("+" if sg > 0 else "-", "xy"[axis], len(fs)))
    ok("three domes on each of the four lip faces and no others: front and back centred on the lanes (x = %s), sides at y = %s"
       % ([round(x, 2) for x in C.SNAP_CENTRES_X], [round(y, 2) for y in C.SNAP_CENTRES_Y]))

    print()
    print("=" * 72)
    print("8. the finger ledge")
    print("=" * 72)
    for name, t, z0, z1 in (("tray", tray, 0.0, C.LEDGE_H), ("lid", lid, C.H_TOTAL - C.LEDGE_H, C.H_TOTAL)):
        bad = ledge_problems(t, z0, z1, name)
        for m in bad:
            fail(m)
        if not bad:
            ok("%s: ledge %.1f proud, %.1f thick, flush with the %s (z = %.2f..%.2f); flat %.2f wide, %.2f at the wall; "
               "front face matches the design at 17 stations"
               % (name, C.LEDGE_OUT, C.LEDGE_H, "bottom" if name == "tray" else "top", z0, z1, 2 * C.LEDGE_FLAT_HX, 2 * C.LEDGE_HX))
    for name, S, z0, z1 in (("tray", builder.build_bottom(ledge=False), 0.0, C.LEDGE_H),
                            ("lid", builder.build_top(ledge=False), C.H_TOTAL - C.LEDGE_H, C.H_TOTAL)):
        bad = ledge_problems(export(S, name + "-noledge"), z0, z1, name)
        (ok if len(bad) >= 5 else fail)("control: the %s built WITHOUT the ledge fails the test %d ways (the test can fail)" % (name, len(bad)))

    print()
    print("=" * 72)
    print("9. assembly")
    print("=" * 72)
    print("  Both parts are in one frame (the tray at z = 0, the lid seated on the seam).")
    cols, jx, jy = [], 0.0731, 0.0417
    nx, ny = 36, 30
    for i in range(nx):
        for j in range(ny):
            cols.append((-C.EXT_HX + 2 * C.EXT_HX * (i + 0.5) / nx + jx, -C.EXT_HY + 2 * C.EXT_HY * (j + 0.5) / ny + jy))
    for i in range(80):                           # the wall bands, densely: lip and groove
        f = (i + 0.5) / 80.0
        for sg in (-1, 1):
            for off in (0.5, 1.2, 1.8):
                cols.append((sg * (C.IN_HX + off) + jx, -C.EXT_HY + 2 * C.EXT_HY * f + jy))
                cols.append((-C.EXT_HX + 2 * C.EXT_HX * f + jx, sg * (C.IN_HY + off) + jy))
    for cx in C.WALL_CENTRES_X:                   # the lane walls, where tray and lid meet
        for i in range(60):
            cols.append((cx + (i % 5 - 2) * 0.9 + jx, -C.IN_HY + 2 * C.IN_HY * (i + 0.5) / 60 + jy))
    cols = [(x, y) for x, y in cols if abs(x) < C.EXT_HX - 0.2 and abs(y) < C.EXT_HY - 0.2]
    worst = col_overlap(tray, lid, cols)
    (ok if worst[0] < TOL else fail)("tray + lid over %d vertical columns across the whole footprint: %s"
                                      % (len(cols), "no overlap" if worst[0] < TOL else "OVERLAP %.4f at x=%.2f y=%.2f" % (worst[0], *worst[1])))

    scols = []
    for tag, face, sg, across, along, _ in specs_t:
        for k in range(-6, 7):
            for t in (0.04, 0.13, 0.27, 0.41, 0.55, 0.69, 0.75):
                off = sg * (abs(face) + t) + 0.0007 * sg
                scols.append((off, across + k * 0.21 + 0.013) if along == "x" else (across + k * 0.21 + 0.013, off))
    w = col_overlap(tray, lid, scols)[0]
    (ok if w < TOL else fail)("the 12 domes seat in the 12 dimples: %d columns across their footprints, %s" % (len(scols), "no overlap" if w < TOL else "OVERLAP %.4f mm" % w))
    extra = C.DENT_DEPTH - C.BUMP_H
    wants, mins = [], []
    for tag, face, sg, across, along, _ in specs_t:
        axis = 0 if along == "x" else 1
        wants.append((C.CLEAR_X if along == "x" else C.CLEAR_Y) + extra)
        fs = features_beyond(tray, axis, face, sg, max_off=1.2, window=(across - 2.2, across + 2.2, C.DOME_Z - 2.2, C.DOME_Z + 2.2),
                             keep=lambda t: min(v[2] for v in t) > C.Z_S + 0.5)
        pts = [v for v in fs[0]["verts"] if abs(abs(v[axis]) - abs(face)) > 0.05]
        near_tris = [t for t in lid if all(abs(v[2] - C.DOME_Z) < 3.5 and abs(abs(v[axis]) - abs(face)) < 2.5 and abs(v[1 - axis] - across) < 3.5 for v in t)]
        mins.append(min(min(point_tri_distance(p, *t) for t in near_tris) for p in pts))
    off = [(specs_t[k][0], round(mins[k], 4), round(wants[k], 4)) for k in range(12) if abs(mins[k] - wants[k]) > 0.01]
    xs_, ys_ = [m for m, s in zip(mins, specs_t) if s[4] == "x"], [m for m, s in zip(mins, specs_t) if s[4] == "y"]
    (ok if not off else fail)("dome-to-dimple nearest approach: x-face caps %.4f..%.4f (design %.4f), y-face caps %.4f..%.4f (design %.4f)%s"
                              % (min(xs_), max(xs_), C.CLEAR_X + extra, min(ys_), max(ys_), C.CLEAR_Y + extra, "" if not off else "; off design: %s" % off))
    blank = export(builder.build_top(dimples=False), "lid-nodimple")
    wb = col_overlap(tray, blank, scols)[0]
    (ok if wb > 0.5 * C.BUMP_H else fail)("control: the same tray against a lid WITHOUT dimples overlaps by %.4f mm (the test can fail)" % wb)

    # ---- the divider, in the tray -------------------------------------------------
    print()
    print("  the divider, standing in the tray (lane, hole): the arms in the holes, hung on the bridges")
    hole_idx = {"first": 0, "middle": C.HOLE_N // 2, "last": C.HOLE_N - 1}
    placements = [(0, "first"), (1, "middle"), (2, "last"), (0, "last"), (2, "first")]

    def place(dmesh, lane, hole):
        return shift(dmesh, (C.LANE_CENTRES_X[lane], C.HOLE_YS[hole_idx[hole]], 0.0))

    def divider_problems(dmesh, label, lane, hole):
        """Clearances and the seat, measured between the tray and a placed divider.  The
        tray is windowed to the divider's neighbourhood so the ray casts stay quick."""
        bad = []
        d = place(dmesh, lane, hole)
        cx, cy = C.LANE_CENTRES_X[lane], C.HOLE_YS[hole_idx[hole]]
        tw = window(tray, cx - 46.0, cx + 46.0, *yband(cy))
        lw = window(lid, cx - 46.0, cx + 46.0, *yband(cy))
        # (a) nothing overlaps, in a fine grid over the whole divider footprint, tray and lid
        grid = [(cx + (-1.0 + 2.0 * i / 150.0) * 38.9, cy + (-1.0 + 2.0 * j / 30.0) * 1.15 + 0.0097)
                for i in range(151) for j in range(31)]
        ot, at = col_overlap(tw, d, grid)
        ol, al = col_overlap(lw, d, grid)
        if ot > TOL:
            bad.append("%s: the divider overlaps the tray by %.3f mm at x=%.2f y=%.2f" % (label, ot, at[0], at[1]))
        if ol > TOL:
            bad.append("%s: the divider overlaps the lid by %.3f mm" % (label, ol))
        # (b) lateral clearances at mid-arm height, along x through the middle of the divider
        z = 40.0
        sd = axis_spans(d, 0, cy, z)             # the divider's runs: left arm, body, right arm
        st = axis_spans(tw, 0, cy, z)            # the tray's runs around it
        if len(sd) != 3:
            bad.append("%s: expected arm, body, arm along x at z=%.0f, found %d runs" % (label, z, len(sd)))
        else:
            arm_l, body, arm_r = sd
            for name, a, b in (("left arm", arm_l[0], arm_l[1]), ("right arm", arm_r[0], arm_r[1])):
                lo_wall = max((s[1] for s in st if s[1] <= a + TOL), default=None)
                hi_wall = min((s[0] for s in st if s[0] >= b - TOL), default=None)
                if lo_wall is None or hi_wall is None:
                    bad.append("%s %s: no wall found either side" % (label, name))
                    continue
                gap_out, gap_in = a - lo_wall, hi_wall - b
                lane_side = gap_in if name == "left arm" else gap_out
                far_side = gap_out if name == "left arm" else gap_in
                # the arm's lane-side face is 0.1 from the hole wall (the skin is 1.5, the gap
                # 1.6) and its outer face 0.3 from the far wall (the hole is 2.0, the arm 1.6)
                if abs(lane_side - 0.1) > 0.011 or abs(far_side - 0.3) > 0.011:
                    bad.append("%s %s: %.4f clear on the lane side (want 0.1) and %.4f on the far side (want 0.3)"
                               % (label, name, lane_side, far_side))
            bw = body[1] - body[0]
            if abs(bw - 2 * C.DIV_BODY_HX) > TOL:
                bad.append("%s: body is %.4f wide, want %.4f" % (label, bw, 2 * C.DIV_BODY_HX))
            for side, edge, face in (("left", body[0], cx - C.LANE_W / 2.0), ("right", body[1], cx + C.LANE_W / 2.0)):
                if abs(abs(edge - face) - C.BODY_CLEAR) > TOL:
                    bad.append("%s: body %s edge is %.4f from the lane face, want %.2f" % (label, side, abs(edge - face), C.BODY_CLEAR))
        # (c) the arm in its hole, across y
        for sgn in (-1, 1):
            ax_ = cx + sgn * (C.DIV_ARM_IN + C.ARM_W / 2.0)
            sa = axis_spans(d, 1, ax_, z)
            sh = axis_spans(tw, 1, ax_, z)
            if len(sa) != 1:
                bad.append("%s: arm at x=%+.2f: %d runs along y" % (label, ax_, len(sa)))
            else:
                before = max((s[1] for s in sh if s[1] <= sa[0][0] + TOL), default=None)
                after = min((s[0] for s in sh if s[0] >= sa[0][1] - TOL), default=None)
                if before is None or after is None or abs((sa[0][0] - before) - 0.2) > 0.011 or abs((after - sa[0][1]) - 0.2) > 0.011:
                    bad.append("%s: arm at x=%+.2f has %.4f / %.4f clear in y (want 0.2 each)" % (label, ax_, sa[0][0] - before if before is not None else -1, after - sa[0][1] if after is not None else -1))
        # (d) it hangs: the bridge's underside rests on the slit's floor, and the top is flush
        for sgn in (-1, 1):
            xb = cx + sgn * (C.LANE_W / 2.0 + C.SKIN / 2.0)       # over the lane-side skin
            sdz = axis_spans(d, 2, xb, cy)
            stz = axis_spans(tw, 2, xb, cy)
            if not sdz or not stz:
                bad.append("%s: no bridge/skin found at x=%+.2f" % (label, xb))
                continue
            seat = sdz[-1][0] - stz[-1][1]
            top = sdz[-1][1]
            if abs(seat) > TOL:
                bad.append("%s: the bridge's underside is %.4f from the slit's floor (want it resting on it)" % (label, seat))
            if abs(top - C.WALL_TOP) > TOL:
                bad.append("%s: the bridge's top is z=%.4f, want flush with the wall top %.4f" % (label, top, C.WALL_TOP))
        lo_, hi_ = bbox(d)
        if abs(hi_[2] - C.WALL_TOP - C.DIV_ABOVE) > TOL:
            bad.append("%s: the divider stands %.4f above the wall top, want %.1f" % (label, hi_[2] - C.WALL_TOP, C.DIV_ABOVE))
        if abs(lo_[2] - (C.FLOOR_T + C.DIV_FLOOR_CLEAR)) > TOL:
            bad.append("%s: the divider's bottom is z=%.4f, want %.4f (0.5 above the floor)" % (label, lo_[2], C.FLOOR_T + C.DIV_FLOOR_CLEAR))
        return bad

    for lane, hole in placements:
        bad = divider_problems(div, "lane %d hole %s" % (lane + 1, hole), lane, hole)
        for m in bad:
            fail(m)
        if not bad:
            ok("divider in lane %d at the %s hole (y=%+.1f): no overlap with tray or lid; arms 0.2 clear in y and 0.1/0.3 in x; "
               "body 0.2 off each lane face; bridge rests on the slit floor, top flush; stands 12.0 above the wall; 12.65 under the ceiling"
               % (lane + 1, hole, C.HOLE_YS[hole_idx[hole]]))
    # controls: a divider whose slot cannot take the skin, and a tray without holes, must both be caught
    tight = export(builder.build_divider(skin_gap=1.3), "divider-tight")
    bt = divider_problems(tight, "tight", 1, "middle")
    (ok if bt else fail)("control: a divider with a 1.3 slot (the skin is 1.5) is caught: %s" % (bt[0] if bt else "NOT CAUGHT"))
    d = place(div, 1, "middle")
    tw0 = window(nohole, -46.0, 46.0, *yband(0.0))
    grid0 = [(-1.0 + 2.0 * i / 150.0) * 38.9 for i in range(151)]
    ow = col_overlap(tw0, d, [(x, 0.0097) for x in grid0])[0]
    (ok if ow > 5.0 else fail)("control: a tray WITHOUT holes against the divider overlaps by %.1f mm (the test can fail)" % ow)

    # neighbours: lanes 1 and 2 at the SAME hole share the partition's hole and collide; one hole apart they do not
    cx0 = C.LANE_CENTRES_X
    a = shift(div, (cx0[0], C.HOLE_YS[20], 0.0))
    b_same = shift(div, (cx0[1], C.HOLE_YS[20], 0.0))
    b_next = shift(div, (cx0[1], C.HOLE_YS[21], 0.0))
    cols_n = [(-38.2 + 1.6 * i / 40.0 + 0.0043, C.HOLE_YS[20] + (j - 20) * 0.1 + 0.0071) for i in range(41) for j in range(41)]
    cols_n2 = [(x, y + 2.0) for x, y in cols_n] + [(x, y + 4.0) for x, y in cols_n]
    o_same = col_overlap(a, b_same, cols_n)[0]
    o_next = max(col_overlap(a, b_next, cols_n + cols_n2)[0], 0.0)
    (ok if o_same > 0.5 else fail)("neighbouring lanes at the SAME hole collide in the shared hole by %.2f mm (the limit you expected)" % o_same)
    (ok if o_next < TOL else fail)("...and one hole (4 mm) apart they do not: overlap %.4f" % o_next)

    print()
    print("=" * 72)
    print("10. the committed STL files are the current design")
    print("=" * 72)
    print("  `solvespace-cli export-mesh` is not reproducible, so the files are compared by size and volume to a fresh export.")

    def stl_matches(path, fresh):
        if not os.path.exists(path):
            return ["%s does not exist" % os.path.basename(path)]
        t = load_stl(path)
        h, hf = health(t), health(fresh)
        bad = []
        if h["non_manifold_edges"] or not h["winding_consistent"] or h["shells"] != 1:
            bad.append("not one watertight shell")
        (a0, a1), (b0, b1) = bbox(t), bbox(fresh)
        for k, ax in enumerate("xyz"):
            if abs((a1[k] - a0[k]) - (b1[k] - b0[k])) > 0.02 or abs(a0[k] - b0[k]) > 0.02:
                bad.append("%s extent %.3f..%.3f, fresh export %.3f..%.3f" % (ax, a0[k], a1[k], b0[k], b1[k]))
        if abs(h["volume"] - hf["volume"]) > 5e-4 * hf["volume"]:
            bad.append("volume %.0f, fresh export %.0f mm^3" % (h["volume"], hf["volume"]))
        return bad

    stls = {"tray": (os.path.join(PART, "deck_case_adjustable_bottom.stl"), tray),
            "lid": (os.path.join(PART, "deck_case_adjustable_top.stl"), lid),
            "divider": (os.path.join(PART, "deck_case_adjustable_divider.stl"), div)}
    for name, (path, fresh) in stls.items():
        bad = stl_matches(path, fresh)
        for m in bad:
            fail("%s STL: %s" % (name, m))
        if not bad:
            lo, hi = bbox(load_stl(path))
            ok("%s STL: %s, %.3f x %.3f x %.3f mm, as a fresh export of the .slvs" % (name, os.path.basename(path), hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
    wrong = stl_matches(stls["tray"][0], lid)
    (ok if len(wrong) >= 2 else fail)("control: the tray's STL checked as if it were the lid's fails %d ways (the test can fail)" % len(wrong))

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
