#!/usr/bin/env python3
"""Verify the 3 x 3 deck case against the brief.

    python3 cad/check_case.py

Exports the tray and the lid through SolveSpace and measures the MESHES, not the
parameters, against each requirement in turn:

  0. every sketch group is fully constrained                (slvs_write.dof_report)
  1. each part is one watertight shell                      (mesh_check)
  2. the footprint fits the 250 x 250 mm bed
  3. each slot is the single box's slot, all nine
  4. the outer walls, lip and groove are the single box's
  5. heights: the tray is as tall as the single bottom's tall edge; the lid takes
     the rest; the card space is the single box's
  6. dividers: 3 mm; both ways in the tray; FRONT-TO-BACK ONLY in the lid
  7. snap: 12 domes and 12 dimples, on all four sides, one per slot, as designed
  8. assembly: the pair interferes nowhere, the domes seat in the dimples with the
     single box's clearance, and a lid WITHOUT dimples is caught (the control)
  9. the finger ledge on the front of each half: its outline, its thickness, its
     position flush with the bottom / top, and nothing else out there; a half
     built WITHOUT it is caught (the control)
 10. the committed STL files, the ones that get printed, are the current design:
     watertight, one shell, and the same size and volume as a fresh export of the
     .slvs; the same test refuses the tray's STL as the lid's (the control)

Each check is written so that the error it exists to catch would fail it; the
`utilities/selftest.py` file shows the tools themselves can fail.  Exit status 0
only if everything passed.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PART = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))
sys.path.insert(0, HERE)

import mesh_check
from mesh_features import features_beyond
from mesh_geom import bbox, point_tri_distance
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


def health(tris, name):
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "m.stl")
        # mesh_check works on a file; write the triangles to one
        import struct
        with open(p, "wb") as fh:
            fh.write(b"\0" * 80 + struct.pack("<I", len(tris)))
            for t in tris:
                fh.write(struct.pack("<12fH", 0, 0, 0, *[c for v in t for c in v], 0))
        return mesh_check.check(p, verbose=False)


def runs(spans):
    """Lengths of solid runs, and of the gaps between them."""
    solid = [hi - lo for lo, hi in spans]
    gap = [spans[i + 1][0] - spans[i][1] for i in range(len(spans) - 1)]
    return solid, gap


def ledge_front(x):
    """Where the front face of a half should be at x, off the design: the flat, then a
    flank arc tangent to it, then the bare wall."""
    ax = abs(x)
    if ax <= C.LEDGE_FLAT_HX:
        return -C.EXT_HY - C.LEDGE_OUT
    if ax >= C.LEDGE_HX:
        return -C.EXT_HY
    yc = -C.EXT_HY - C.LEDGE_OUT + C.LEDGE_FLANK_R
    return yc - (C.LEDGE_FLANK_R ** 2 - (ax - C.LEDGE_FLAT_HX) ** 2) ** 0.5


def ledge_problems(tris, z0, z1, label):
    """Everything wrong with the finger ledge on a half whose ledge spans z0..z1
    (z0 < z1).  Measured off the mesh, so an absent ledge reports a problem for each
    thing it should have: that is what the control relies on."""
    bad = []
    zm = (z0 + z1) / 2.0
    lo, hi = bbox(tris)
    if abs(lo[1] - (-C.EXT_HY - C.LEDGE_OUT)) > 0.01:
        bad.append("%s: frontmost point y = %.4f, want %.4f" % (label, lo[1], -C.EXT_HY - C.LEDGE_OUT))
    # the front face along x, mid-thickness: flat, then the flanks, then the wall
    xs = [0.0, 20.0, C.LEDGE_FLAT_HX - 0.4, C.LEDGE_FLAT_HX + 0.4, C.LEDGE_FLAT_HX + 8.0,
          C.LEDGE_FLAT_HX + 16.0, C.LEDGE_HX - 3.0, C.LEDGE_HX + 2.0, C.LEDGE_HX + 20.0]
    for x in xs + [-v for v in xs[1:]]:
        sp = axis_spans(tris, 1, x + 0.0137, zm)       # untidy offset: see mesh_rays
        want = ledge_front(x + 0.0137)
        if not sp or abs(sp[0][0] - want) > 0.03:
            bad.append("%s: front face at x=%+.2f is y=%s, want %.4f"
                       % (label, x, "%.4f" % sp[0][0] if sp else "absent", want))
    # its thickness and its flush face: one solid run over exactly z0..z1, out in front
    for x in (0.0, 30.0, -45.0):
        sp = axis_spans(tris, 2, x + 0.0137, -C.EXT_HY - C.LEDGE_OUT / 2.0)
        if len(sp) != 1 or abs(sp[0][0] - z0) > TOL or abs(sp[0][1] - z1) > TOL:
            bad.append("%s: through the ledge at x=%+.1f, solid z = %s, want %.4f..%.4f"
                       % (label, x, [(round(a, 4), round(b, 4)) for a, b in sp], z0, z1))
    # nothing else stands out in front of the wall, off the ends of the ledge
    for x in (C.LEDGE_HX + 6.0, -C.LEDGE_HX - 6.0, 100.0, -100.0):
        if axis_spans(tris, 2, x, -C.EXT_HY - 0.3):
            bad.append("%s: something stands proud of the wall at x=%+.1f" % (label, x))
    return bad


def near(a, b, tol=TOL):
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


# ---------------------------------------------------------------------------
def main():
    print("=" * 72)
    print("0. sketch constraints")
    print("=" * 72)
    for label, fn in (("tray", builder.build_bottom), ("lid", builder.build_top)):
        S = fn()
        rows = [r for r in dof_report(S, S.group_names) if r["equations"]]
        bad = [r["name"] for r in rows if r["dof"] or r["redundant"] or r["residual"] > 1e-7]
        n_ok = len(rows) - len(bad)
        (ok if not bad else fail)("%s: %d of %d constrained groups are 0 DOF, 0 redundant%s"
                                  % (label, n_ok, len(rows), "" if not bad else "; bad: %s" % bad))

    tray = export(builder.build_bottom(), "tray")
    lid = export(builder.build_top(), "lid")
    if not tray or not lid:
        return 1

    print()
    print("=" * 72)
    print("1. the meshes")
    print("=" * 72)
    for name, t in (("tray", tray), ("lid", lid)):
        h = health(t, name)
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
    print("3. the slots: nine, each the single box's")
    print("=" * 72)
    want_x = [C.SLOT_X] * C.N_COLS
    want_y = [C.SLOT_Y] * C.N_ROWS
    for name, t, z in (("tray", tray, 30.0), ("lid", lid, 90.0)):
        for yc in C.SLOT_CENTRES_Y:               # across x, through each row of slots
            solid, gap = runs(axis_spans(t, 0, yc, z))
            if not near(gap, want_x) or not near(solid, [C.WALL_X, C.INNER_T, C.INNER_T, C.WALL_X]):
                fail("%s along x through row y=%.1f: solid %s gaps %s" % (name, yc, solid, gap))
    ok("tray and lid: the three slots across x are %.4f wide, between walls of %.4f and dividers of %.1f"
       % (C.SLOT_X, C.WALL_X, C.INNER_T))
    for xc in C.SLOT_CENTRES_X:                   # along y, through each column: the TRAY only
        solid, gap = runs(axis_spans(tray, 1, xc, 30.0))
        if not near(gap, want_y) or not near(solid, [C.WALL_Y, C.INNER_T, C.INNER_T, C.WALL_Y]):
            fail("tray along y through column x=%.1f: solid %s gaps %s" % (xc, solid, gap))
    ok("tray: the three slots along y are %.4f deep, between walls of %.4f and dividers of %.1f"
       % (C.SLOT_Y, C.WALL_Y, C.INNER_T))
    (ok if C.SLOT_X == 2 * B.INT_HX and C.SLOT_Y == 2 * B.INT_HY else fail)(
        "a slot is exactly the single box's cavity, %.4f x %.4f" % (2 * B.INT_HX, 2 * B.INT_HY))

    print()
    print("=" * 72)
    print("4. outer walls, lip and groove: the single box's")
    print("=" * 72)
    z = C.Z_S + 5.0                               # above the domes (they top out 4 mm above the seam)
    sx, _ = runs(axis_spans(tray, 0, 0.0, z))     # the tray's lip band at y = 0
    lipx = sx[0] if sx else None
    sy, _ = runs(axis_spans(tray, 1, 0.0, z))
    lipy = sy[0] if sy else None
    (ok if lipx and abs(lipx - B.LIP_T_X) < TOL and lipy and abs(lipy - B.LIP_T_Y) < TOL else fail)(
        "lip thickness x %.4f, y %.4f   (single box %.4f, %.4f)" % (lipx or -1, lipy or -1, B.LIP_T_X, B.LIP_T_Y))
    lid_spans_x = axis_spans(lid, 0, 0.0, z)
    lid_spans_y = axis_spans(lid, 1, 0.0, z)
    tray_spans_x = axis_spans(tray, 0, 0.0, z)
    tray_spans_y = axis_spans(tray, 1, 0.0, z)
    # the lid's wall ends where the groove begins; the tray's lip begins at its outer
    # face, which is INSIDE that by the clearance (both measured off the meshes)
    gx = tray_spans_x[0][0] - lid_spans_x[0][1] if lid_spans_x and tray_spans_x else None
    gy = tray_spans_y[0][0] - lid_spans_y[0][1] if lid_spans_y and tray_spans_y else None
    (ok if gx is not None and abs(gx - B.CLEAR_X) < TOL and abs(gy - B.CLEAR_Y) < TOL else fail)(
        "lip-to-groove clearance x %.5f, y %.5f   (single box %.5f, %.5f)"
        % (gx if gx is not None else -1, gy if gy is not None else -1, B.CLEAR_X, B.CLEAR_Y))
    wall_lid_x = lid_spans_x[0][1] - lid_spans_x[0][0]
    wall_lid_y = lid_spans_y[0][1] - lid_spans_y[0][0]
    (ok if abs(wall_lid_x - (C.EXT_HX - C.GROOVE_HX)) < TOL and abs(wall_lid_y - (C.EXT_HY - C.GROOVE_HY)) < TOL
     else fail)("the lid's wall beside the groove is %.4f (x), %.4f (y) thick" % (wall_lid_x, wall_lid_y))
    wx = axis_spans(tray, 0, 0.0, 30.0)
    wy = axis_spans(tray, 1, 0.0, 30.0)
    (ok if abs((wx[0][1] - wx[0][0]) - B.WALL_X) < TOL and abs((wy[0][1] - wy[0][0]) - B.WALL_Y) < TOL else fail)(
        "the tray's outer walls are %.4f (x), %.4f (y)   (single box %.4f, %.4f)"
        % (wx[0][1] - wx[0][0], wy[0][1] - wy[0][0], B.WALL_X, B.WALL_Y))

    print()
    print("=" * 72)
    print("5. heights")
    print("=" * 72)
    tlo, thi = bbox(tray)
    llo, lhi = bbox(lid)
    single_bottom = os.path.join(PART, "..", "mtg-deck-boxes", "ultra_guard_pro_100_bottom.stl")
    sb = bbox(load_stl(single_bottom))
    single_h = sb[1][2] - sb[0][2]
    (ok if abs((thi[2] - tlo[2]) - single_h) < 0.01 else fail)(
        "tray is %.4f tall; the single bottom's STL is %.4f tall" % (thi[2] - tlo[2], single_h))
    (ok if abs(tlo[2]) < TOL else fail)("tray underside at z = %.4f" % tlo[2])
    (ok if abs(llo[2] - C.Z_S) < TOL and abs(lhi[2] - C.H_TOTAL) < TOL else fail)(
        "lid spans z = %.4f .. %.4f (%.4f tall); seam at %.4f" % (llo[2], lhi[2], lhi[2] - llo[2], C.Z_S))
    fl = axis_spans(tray, 2, 0.0, 0.0)
    cl = axis_spans(lid, 2, 0.0, 0.0)
    card = cl[0][0] - fl[0][1] if fl and cl else None
    (ok if card is not None and abs(card - B.INT_H) < TOL else fail)(
        "card space, tray floor to lid ceiling, %.4f   (single box %.4f)" % (card or -1, B.INT_H))
    z_wall_tray = axis_spans(tray, 2, C.EXT_HX - 1.0, 0.0)
    (ok if z_wall_tray and abs(z_wall_tray[0][1] - C.Z_S) < TOL else fail)(
        "the tray's outer wall stops at the seam, z = %.4f" % z_wall_tray[0][1])
    z_lip_tray = axis_spans(tray, 2, C.IN_HX + 0.9, 0.0)
    (ok if z_lip_tray and abs(z_lip_tray[0][1] - C.Z_LIP) < TOL else fail)(
        "the lip stands to z = %.4f, %.4f above the seam" % (z_lip_tray[0][1], z_lip_tray[0][1] - C.Z_S))

    print()
    print("=" * 72)
    print("6. dividers")
    print("=" * 72)
    # tray: a bar across the whole width at each y divider, across the whole depth at each x divider
    for y in C.DIV_Y:
        s = axis_spans(tray, 0, y, 30.0)
        (ok if len(s) == 1 and abs((s[0][1] - s[0][0]) - 2 * C.EXT_HX) < TOL else fail)(
            "tray: divider along x at y=%+.3f spans wall to wall (%.3f)" % (y, s[0][1] - s[0][0] if s else -1))
    for x in C.DIV_X:
        s = axis_spans(tray, 1, x, 30.0)
        (ok if len(s) == 1 and abs((s[0][1] - s[0][0]) - 2 * C.EXT_HY) < TOL else fail)(
            "tray: divider along y at x=%+.3f spans wall to wall (%.3f)" % (x, s[0][1] - s[0][0] if s else -1))
    zt = axis_spans(tray, 2, C.DIV_X[0], 10.0)
    (ok if zt and abs(zt[0][1] - C.DIV_TRAY_TOP) < TOL else fail)(
        "tray dividers rise to z = %.4f, %.2f under the lip top" % (zt[0][1], C.Z_LIP - zt[0][1]))
    # lid: front-to-back only
    for x in C.DIV_X:
        s = axis_spans(lid, 1, x, 90.0)
        (ok if len(s) == 1 and abs((s[0][1] - s[0][0]) - 2 * C.EXT_HY) < TOL else fail)(
            "lid: divider along y at x=%+.3f spans front to back (%.3f)" % (x, s[0][1] - s[0][0] if s else -1))
    for xc in C.SLOT_CENTRES_X:
        s = axis_spans(lid, 1, xc, 90.0)
        (ok if len(s) == 2 else fail)(
            "lid: through the middle of a slot, x=%+.2f, a line front-to-back meets %d solid runs "
            "(2 = the walls only: no left-right wall)" % (xc, len(s)))
    for y in C.DIV_Y:
        s = axis_spans(lid, 0, y, 90.0)
        (ok if len(s) == 4 else fail)("lid: at y=%+.3f, where the tray has a divider, a line across x meets "
                                      "%d runs (4 = walls and the two y-dividers, no left-right bar)" % (y, len(s)))
    zl = axis_spans(lid, 2, C.DIV_X[0], 10.0)
    (ok if zl and abs(zl[0][0] - C.DIV_LID_BOTTOM) < TOL else fail)(
        "lid dividers hang to z = %.4f, %.2f over the roof" % (zl[0][0], zl[0][0] - C.Z_LIP))
    gap = zl[0][0] - zt[0][1] if zl and zt else None
    (ok if gap is not None and abs(gap - 2 * C.DIV_GAP) < TOL else fail)(
        "where a tray divider meets a lid divider the gap is %.4f" % (gap or -1))

    print()
    print("=" * 72)
    print("7. snap domes and dimples")
    print("=" * 72)
    specs_t = builder.snap_specs(C.LIP_HX, C.LIP_HY)
    specs_l = builder.snap_specs(C.GROOVE_HX, C.GROOVE_HY)

    def measure(tris, face_abs, specs, name, want_h, want_r, above):
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

    nb = measure(tray, C.LIP_HX, specs_t, "dome", C.BUMP_H, B.BUMP_BASE_R, True)
    nd = measure(lid, C.GROOVE_HX, specs_l, "dimple", C.DENT_DEPTH, B.DENT_MOUTH_R, False)
    (ok if nb == 12 else fail)("tray: %d of 12 domes measure to the single box's dome (height %.4f, base radius %.3f)"
                               % (nb, C.BUMP_H, B.BUMP_BASE_R))
    (ok if nd == 12 else fail)("lid: %d of 12 dimples measure to the single box's dimple (depth %.4f, mouth radius %.3f)"
                               % (nd, C.DENT_DEPTH, B.DENT_MOUTH_R))
    # no extra ones: all features above the seam on each lip face, anywhere
    for sg in (-1, 1):
        for axis, face_abs, n in ((0, C.LIP_HX, C.N_ROWS), (1, C.LIP_HY, C.N_COLS)):
            fs = features_beyond(tray, axis, sg * face_abs, sg, max_off=1.2,
                                 keep=lambda t: min(v[2] for v in t) > C.Z_S + 0.5)
            if len(fs) != n:
                fail("the tray's %s%s lip face carries %d domes, expected %d"
                     % ("+" if sg > 0 else "-", "xy"[axis], len(fs), n))
    ok("three domes on each of the four lip faces, one per slot, and no others")

    print()
    print("=" * 72)
    print("8. assembly")
    print("=" * 72)
    print("  Both parts are in one frame (the tray at z = 0, the lid seated on the seam).")
    cols = []
    jx, jy = 0.0731, 0.0417                       # untidy offsets: see mesh_rays
    nx, ny = 28, 30
    for i in range(nx):
        for j in range(ny):
            x = -C.EXT_HX + 2 * C.EXT_HX * (i + 0.5) / nx + jx
            y = -C.EXT_HY + 2 * C.EXT_HY * (j + 0.5) / ny + jy
            cols.append((x, y))
    for i in range(80):                           # the wall bands, densely: lip and groove
        f = (i + 0.5) / 80.0
        for sg in (-1, 1):
            for off in (0.5, 1.2, 1.8):
                cols.append((sg * (C.IN_HX + off) + jx, -C.EXT_HY + 2 * C.EXT_HY * f + jy))
                cols.append((-C.EXT_HX + 2 * C.EXT_HX * f + jx, sg * (C.IN_HY + off) + jy))
    cols = [(x, y) for x, y in cols if abs(x) < C.EXT_HX - 0.2 and abs(y) < C.EXT_HY - 0.2]

    def col_spans(t, cs):
        return [axis_spans(t, 2, x, y) for x, y in cs]

    ts = col_spans(tray, cols)
    ls = col_spans(lid, cols)
    worst = max((overlap(a, b), c) for a, b, c in zip(ts, ls, cols))
    (ok if worst[0] < TOL else fail)(
        "tray + lid over %d vertical columns across the whole footprint: %s"
        % (len(cols), "no overlap" if worst[0] < TOL else
           "OVERLAP %.4f at x=%.2f y=%.2f" % (worst[0], *worst[1])))

    # the domes' footprints, on all four sides
    scols = []
    for tag, face, sg, across, along, _ in specs_t:
        for k in range(-6, 7):
            for t in (0.04, 0.13, 0.27, 0.41, 0.55, 0.69, 0.75):
                off = sg * (abs(face) + t) + 0.0007 * sg
                if along == "x":
                    scols.append((off, across + k * 0.21 + 0.013))
                else:
                    scols.append((across + k * 0.21 + 0.013, off))
    sts = col_spans(tray, scols)
    sls = col_spans(lid, scols)
    w = max(overlap(a, b) for a, b in zip(sts, sls))
    (ok if w < TOL else fail)("the 12 domes seat in the 12 dimples: %d columns across their footprints, %s"
                              % (len(scols), "no overlap" if w < TOL else "OVERLAP %.4f mm" % w))

    # Nearest approach of dome to dimple, every one of the twelve, against what the
    # geometry says it must be.  The apex gap is the lip-to-groove clearance PLUS
    # the dimple's extra depth, and the clearance is NOT the same on both axes (the
    # single box's walls are scaled 1.0294 in x and 1.1953 in y): 0.0118 across x
    # and 0.0781 across y.  So the x-face caps seat with 0.0254 and the y-face caps
    # with 0.0917.  An earlier version of this check used the x figure for all
    # twelve, with a tolerance wide enough to pass the y caps; it is per-axis and
    # tight (0.01, against a measured spread of 0.0002) now.
    extra = C.DENT_DEPTH - C.BUMP_H
    wants, mins = [], []
    for tag, face, sg, across, along, _ in specs_t:
        axis = 0 if along == "x" else 1
        wants.append((C.CLEAR_X if along == "x" else C.CLEAR_Y) + extra)
        fs = features_beyond(tray, axis, face, sg, max_off=1.2,
                             window=(across - 2.2, across + 2.2, C.DOME_Z - 2.2, C.DOME_Z + 2.2),
                             keep=lambda t: min(v[2] for v in t) > C.Z_S + 0.5)
        pts = [v for v in fs[0]["verts"] if abs(abs(v[axis]) - abs(face)) > 0.05]
        near_tris = [t for t in lid
                     if all(abs(v[2] - C.DOME_Z) < 3.5 and abs(abs(v[axis]) - abs(face)) < 2.5 and
                            abs(v[1 - axis] - across) < 3.5 for v in t)]
        mins.append(min(min(point_tri_distance(p, *t) for t in near_tris) for p in pts))
    off = [(specs_t[k][0], round(mins[k], 4), round(wants[k], 4)) for k in range(12)
           if abs(mins[k] - wants[k]) > 0.01]
    (ok if not off else fail)(
        "dome-to-dimple nearest approach: x-face caps %.4f..%.4f (design %.4f), y-face caps %.4f..%.4f (design %.4f)%s"
        % (min(mins[:6]), max(mins[:6]), C.CLEAR_X + extra, min(mins[6:]), max(mins[6:]),
           C.CLEAR_Y + extra, "" if not off else "; off design: %s" % off))

    # the control: the same tray against a lid built WITHOUT dimples must overlap
    blank = export(builder.build_top(dimples=False), "lid-nodimple")
    bls = col_spans(blank, scols)
    wb = max(overlap(a, b) for a, b in zip(sts, bls))
    (ok if wb > 0.5 * C.BUMP_H else fail)(
        "control: the same tray against a lid WITHOUT dimples overlaps by %.4f mm (the test can fail)" % wb)

    print()
    print("=" * 72)
    print("9. the finger ledge")
    print("=" * 72)
    for name, t, z0, z1 in (("tray", tray, 0.0, C.LEDGE_H),
                            ("lid", lid, C.H_TOTAL - C.LEDGE_H, C.H_TOTAL)):
        bad = ledge_problems(t, z0, z1, name)
        for m in bad:
            fail(m)
        if not bad:
            ok("%s: ledge %.1f proud, %.1f thick, flush with the %s (z = %.2f..%.2f); flat %.2f wide, "
               "%.2f at the wall; front face matches the design at 17 stations"
               % (name, C.LEDGE_OUT, C.LEDGE_H, "bottom" if name == "tray" else "top", z0, z1,
                  2 * C.LEDGE_FLAT_HX, 2 * C.LEDGE_HX))
    # nothing else is affected: the ledges clear the other half and the snap
    lo, hi = bbox(lid)
    tlo, thi = bbox(tray)
    (ok if thi[2] < C.H_TOTAL - C.LEDGE_H else fail)(
        "the tray's top (z=%.2f) is below the lid's ledge (z=%.2f): the two never meet"
        % (thi[2], C.H_TOTAL - C.LEDGE_H))
    # the control: halves built WITHOUT the ledge must be caught by the same test
    for name, S, z0, z1 in (("tray", builder.build_bottom(ledge=False), 0.0, C.LEDGE_H),
                            ("lid", builder.build_top(ledge=False), C.H_TOTAL - C.LEDGE_H, C.H_TOTAL)):
        t = export(S, name + "-noledge")
        bad = ledge_problems(t, z0, z1, name)
        (ok if len(bad) >= 5 else fail)(
            "control: the %s built WITHOUT the ledge fails the test %d ways (the test can fail)"
            % (name, len(bad)))

    print()
    print("=" * 72)
    print("10. the committed STL files are the current design")
    print("=" * 72)
    print("  `solvespace-cli export-mesh` is not reproducible, so the files are compared by")
    print("  size and volume to a fresh export, not triangle by triangle.")

    def stl_matches(path, fresh):
        """Problems with a committed STL against a fresh export of the same part."""
        if not os.path.exists(path):
            return ["%s does not exist" % os.path.basename(path)]
        t = load_stl(path)
        h, hf = health(t, "stl"), health(fresh, "fresh")
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

    stl_tray = os.path.join(PART, "deck_case_3x3_bottom.stl")
    stl_lid = os.path.join(PART, "deck_case_3x3_top.stl")
    for name, path, fresh in (("tray", stl_tray, tray), ("lid", stl_lid, lid)):
        bad = stl_matches(path, fresh)
        for m in bad:
            fail("%s STL: %s" % (name, m))
        if not bad:
            lo, hi = bbox(load_stl(path))
            ok("%s STL: %s, %.3f x %.3f x %.3f mm, as a fresh export of the .slvs"
               % (name, os.path.basename(path), hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
    wrong = stl_matches(stl_tray, lid)
    (ok if len(wrong) >= 2 else fail)(
        "control: the tray's STL checked as if it were the lid's fails %d ways (the test can fail)" % len(wrong))

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
