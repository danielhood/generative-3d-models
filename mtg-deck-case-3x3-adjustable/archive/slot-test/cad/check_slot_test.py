#!/usr/bin/env python3
"""Verify the slot-and-tab test pieces: the divider and the short single-lane base.

    python3 cad/check_slot_test.py

Exports both through SolveSpace and measures the MESHES, not the parameters:

  0. every sketch group is fully constrained
  1. each part is one watertight shell
  2. the base: size, floor, the lane's width, smooth below the slots
  3. the slots: positions, width, pitch, depth, floor; the two faces STAGGERED, and the
     wall never thinner than 1.5 mm
  4. the divider: size, body width, tabs
  5. the two together: the divider in every one of lane 2's six slots and in the outer
     slots too; clearances; it hangs and stands vertical; neighbours 3 mm apart coexist
  6. the committed STL files are the current design

Each group ends with a CONTROL, the same test on a part built wrongly on purpose, which
must fail.  Exit status 0 only if everything passed.
"""
import os
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PART = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "utilities"))
sys.path.insert(0, HERE)

import mesh_check
from mesh_geom import bbox, shift
from mesh_rays import axis_spans, overlap
from slvs_cli import export_mesh
from slvs_write import dof_report
from stl_io import load_stl
import slot_params as P
import build_slot_test as builder

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
    return ([hi - lo for lo, hi in spans], [spans[i + 1][0] - spans[i][1] for i in range(len(spans) - 1)])


def centres(spans):
    """Centres of the GAPS between solid runs (the slots, seen along a line)."""
    return [(spans[i][1] + spans[i + 1][0]) / 2.0 for i in range(len(spans) - 1)]


def col_overlap(a, b, columns):
    worst, where = 0.0, None
    for x, y in columns:
        o = overlap(axis_spans(a, 2, x, y), axis_spans(b, 2, x, y))
        if o > worst:
            worst, where = o, (x, y)
    return worst, where


FACE = P.LANE_W / 2.0                      # a partition's lane face, at x = +-FACE
OUTER = P.LANE_W / 2.0 + P.WALL_T          # its outer face
ZS = P.WALL_TOP - 12.0                     # a height inside the slots (and inside the tabs)


# ---------------------------------------------------------------------------
def slot_problems(base, label):
    """Everything wrong with the base's slots, measured off the mesh."""
    bad = []
    for sgn in (-1, 1):
        s = "+" if sgn > 0 else "-"
        # set B: along y just inside the lane face (x = FACE + 1.0 into the wall)
        sp = axis_spans(base, 1, sgn * (FACE + 1.0), ZS)
        got = centres(sp)
        gaps = runs(sp)[1]
        if len(got) != len(P.B_YS) or any(abs(a - b) > TOL for a, b in zip(got, P.B_YS)) or \
                any(abs(g - P.SLOT_W) > TOL for g in gaps):
            bad.append("%s %sx wall, lane side: slots at %s (want %s, %.1f wide)"
                       % (label, s, [round(c, 3) for c in got], P.B_YS, P.SLOT_W))
        # set A: along y just inside the outer face (x = OUTER - 1.0)
        sp = axis_spans(base, 1, sgn * (OUTER - 1.0), ZS)
        got = centres(sp)
        gaps = runs(sp)[1]
        if len(got) != len(P.A_YS) or any(abs(a - b) > TOL for a, b in zip(got, P.A_YS)) or \
                any(abs(g - P.SLOT_W) > TOL for g in gaps):
            bad.append("%s %sx wall, outer side: slots at %s (want %s)" % (label, s, [round(c, 3) for c in got], P.A_YS))
        # depth: the wall's thickness at a B slot and at an A slot, and between
        for y, want, what in ((P.B_YS[2], P.SKIN, "a lane-side slot"), (P.A_YS[3], P.SKIN, "an outer slot"),
                              (P.B_YS[2] + 1.5 + 0.0137, P.WALL_T, "a web between slots")):
            sx = axis_spans(base, 0, y + 0.0, ZS)
            wall = [r for r in sx if sgn * ((r[0] + r[1]) / 2.0) > FACE - 0.1]
            thick = (wall[0][1] - wall[0][0]) if wall else None
            if len(wall) != 1 or abs(thick - want) > TOL:
                bad.append("%s %sx wall at %s (y=%.2f): solid %s thick, want %.2f"
                           % (label, s, what, y, "%.3f" % thick if thick is not None else "absent/split", want))
        # slot floor and wall top
        for x, y, want, what in ((sgn * (FACE + 1.0), P.B_YS[1], P.SLOT_FLOOR, "a lane-side slot floor"),
                                 (sgn * (OUTER - 1.0), P.A_YS[2], P.SLOT_FLOOR, "an outer slot floor"),
                                 (sgn * (FACE + 1.0), P.B_YS[1] + 3.0, P.WALL_TOP, "the wall top between slots")):
            sz = axis_spans(base, 2, x, y)
            if not sz or abs(sz[0][1] - want) > TOL:
                bad.append("%s %sx wall: %s is z=%s, want %.4f" % (label, s, what, "%.4f" % sz[0][1] if sz else "absent", want))
    return bad


def thinnest_wall(base):
    """The thinnest the walls ever get, scanning y finely at slot height: a wall cut right
    through at some y shows as no run at all (0.0)."""
    worst = P.WALL_T
    y = -P.TEST_HY + 0.35
    while y < P.TEST_HY - 0.3:
        for sgn in (-1, 1):
            sx = axis_spans(base, 0, y, ZS)
            wall = [r for r in sx if sgn * ((r[0] + r[1]) / 2.0) > FACE - 0.1]
            t = (wall[0][1] - wall[0][0]) if len(wall) == 1 else 0.0
            worst = min(worst, t)
        y += 0.25
    return worst


# ---------------------------------------------------------------------------
def main():
    print("=" * 72)
    print("0. sketch constraints")
    print("=" * 72)
    for label, fn in (("base", builder.build_base), ("divider", builder.build_divider)):
        S = fn()
        rows = [r for r in dof_report(S, S.group_names) if r["equations"]]
        bad = [r["name"] for r in rows if r["dof"] or r["redundant"] or r["residual"] > 1e-7]
        (ok if not bad else fail)("%s: %d of %d constrained groups are 0 DOF, 0 redundant%s"
                                  % (label, len(rows) - len(bad), len(rows), "" if not bad else "; bad: %s" % bad))
    base = export(builder.build_base(), "base")
    div = export(builder.build_divider(), "divider")
    if not base or not div:
        return 1

    print()
    print("=" * 72)
    print("1. the meshes")
    print("=" * 72)
    for name, t in (("base", base), ("divider", div)):
        h = health(t)
        good = not h["non_manifold_edges"] and h["winding_consistent"] and h["shells"] == 1
        (ok if good else fail)("%s: %d triangles, %s, %d shell(s), volume %.1f mm^3"
                               % (name, h["triangles"], "watertight" if not h["non_manifold_edges"] else "NOT WATERTIGHT", h["shells"], h["volume"]))

    print()
    print("=" * 72)
    print("2. the base")
    print("=" * 72)
    lo, hi = bbox(base)
    want = (2 * OUTER, 2 * P.TEST_HY, P.WALL_TOP)
    got = tuple(h - l for l, h in zip(lo, hi))
    (ok if all(abs(g - w) < TOL for g, w in zip(got, want)) and abs(lo[2]) < TOL else fail)(
        "base is %.4f x %.4f x %.4f mm (want %.4f x %.4f x %.4f), standing on z = 0" % (*got, *want))
    fz = axis_spans(base, 2, 0.0, 0.0)
    (ok if len(fz) == 1 and abs(fz[0][1] - P.TEST_FLOOR_T) < TOL else fail)("the floor between the walls is %.3f thick" % (fz[0][1] - fz[0][0]))
    smooth = True
    for y in (P.B_YS[1], P.A_YS[2], 0.0137):
        for z in (3.0, 20.0, 45.0):                      # below the slots' floor (48.4)
            sol, gap = runs(axis_spans(base, 0, y, z))
            if len(gap) != 1 or abs(gap[0] - P.LANE_W) > TOL or any(abs(s - P.WALL_T) > TOL for s in sol):
                smooth = False
                fail("across x at y=%.2f z=%.0f: walls %s, lane %s (want 5.0, %.4f, 5.0)" % (y, z, [round(s, 4) for s in sol], [round(g, 4) for g in gap], P.LANE_W))
    if smooth:
        ok("the lane is %.4f wide and the walls 5.000 thick at every height below the slots (z = 3 to 45), at slots and between" % P.LANE_W)

    print()
    print("=" * 72)
    print("3. the slots")
    print("=" * 72)
    bad = slot_problems(base, "base")
    for m in bad:
        fail(m)
    if not bad:
        ok("both walls: %d lane-side slots (y = %s) and %d outer slots (y = %s), each %.1f wide at pitch %.1f; "
           "%.1f deep leaving %.1f; floors at z = %.2f (%.1f below the wall top %.2f)"
           % (len(P.B_YS), [round(y, 1) for y in P.B_YS], len(P.A_YS), [round(y, 1) for y in P.A_YS],
              P.SLOT_W, P.SLOT_PITCH, P.SLOT_DEPTH, P.SKIN, P.SLOT_FLOOR, P.SLOT_H, P.WALL_TOP))
    tw = thinnest_wall(base)
    (ok if tw >= P.SKIN - TOL else fail)("staggered: the thinnest the walls ever get, scanning every 0.25 mm of y, is %.3f (want %.1f)" % (tw, P.SKIN))
    nos = export(builder.build_base(slots=False), "base-noslots")
    bad0 = slot_problems(nos, "no-slots")
    (ok if len(bad0) >= 6 else fail)("control: a base WITHOUT slots fails the slot test %d ways (the test can fail)" % len(bad0))
    unst = export(builder.build_base(stagger=False), "base-unstaggered")
    tu = thinnest_wall(unst)
    (ok if tu < 0.1 else fail)("control: slots on both faces at the SAME positions cut the wall through (thinnest %.3f): the stagger is needed" % tu)

    print()
    print("=" * 72)
    print("4. the divider")
    print("=" * 72)
    lo, hi = bbox(div)
    want = (2 * P.DIV_TAB_OUT, P.DIV_T, P.DIV_TOP - P.DIV_BOTTOM)
    got = tuple(h - l for l, h in zip(lo, hi))
    (ok if all(abs(g - w) < TOL for g, w in zip(got, want)) and abs(lo[2] - P.DIV_BOTTOM) < TOL else fail)(
        "divider is %.4f x %.4f x %.4f (want %.4f x %.4f x %.4f), from z = %.2f" % (*got, *want, lo[2]))
    body = axis_spans(div, 0, 0.0, 30.0)
    (ok if len(body) == 1 and abs((body[0][1] - body[0][0]) - 2 * P.DIV_BODY_HX) < TOL else fail)(
        "the body is %.4f wide, %.2f off each lane face" % (body[0][1] - body[0][0], P.BODY_CLEAR))
    tab = axis_spans(div, 0, 0.0, ZS)
    (ok if len(tab) == 1 and abs((tab[0][1] - tab[0][0]) - 2 * P.DIV_TAB_OUT) < TOL else fail)(
        "across the tabs it is %.4f wide: each tab reaches %.1f past the lane face" % (tab[0][1] - tab[0][0], P.TAB_REACH))
    tz = axis_spans(div, 2, P.LANE_W / 2.0 + 1.0, 0.0)
    (ok if len(tz) == 1 and abs(tz[0][0] - P.DIV_TAB_BOTTOM) < TOL and abs(tz[0][1] - P.WALL_TOP) < TOL else fail)(
        "each tab is z = %.4f .. %.4f (%.1f tall), its top flush with the wall top" % (tz[0][0], tz[0][1], tz[0][1] - tz[0][0]))
    ty = axis_spans(div, 1, 0.0, 30.0)
    (ok if len(ty) == 1 and abs((ty[0][1] - ty[0][0]) - P.DIV_T) < TOL else fail)("the plate and tabs are %.4f thick" % (ty[0][1] - ty[0][0]))
    (ok if abs(hi[2] - P.WALL_TOP - P.DIV_ABOVE) < TOL else fail)("the body stands %.4f above the wall top" % (hi[2] - P.WALL_TOP))

    print()
    print("=" * 72)
    print("5. the divider in the base")
    print("=" * 72)

    def fit_problems(dmesh, bmesh, label, cx, cy, side):
        """Clearances and the hang, measured between the base and a divider placed at
        (cx, cy).  `side` names which tabs are in a slot: 'both' for lane 2, or -1/+1
        for a lane-1 / lane-3 divider whose far tab is in air."""
        bad = []
        d = shift(dmesh, (cx, cy, 0.0))
        # (a) no overlap, fine grid over every tab and the body's footprint near the wall
        cols = []
        for sgn in (-1, 1):
            if side != "both" and sgn != side:
                continue
            face = cx + sgn * P.LANE_W / 2.0
            for i in range(0, 91):
                for j in range(0, 25):
                    cols.append((face - sgn * 1.0 + sgn * i * 0.05 + 0.0073, cy - 1.15 + j * 0.0958 + 0.0031))
        o, at = col_overlap(bmesh, d, cols)
        if o > TOL:
            bad.append("%s: the divider overlaps the base by %.3f mm at x=%.3f y=%.3f" % (label, o, at[0], at[1]))
        # tabs: look through the wall slot in y and x at mid tab height
        for sgn in (-1, 1):
            if side != "both" and sgn != side:
                continue
            face = cx + sgn * P.LANE_W / 2.0
            xm = face + sgn * 1.6                                   # mid-reach of the tab, inside the wall
            sd = axis_spans(d, 1, xm, ZS)
            sb = axis_spans(bmesh, 1, xm, ZS)
            if len(sd) != 1:
                bad.append("%s: tab at x=%+.2f: %d runs along y" % (label, xm, len(sd)))
                continue
            before = max((s[1] for s in sb if s[1] <= sd[0][0] + TOL), default=None)
            after = min((s[0] for s in sb if s[0] >= sd[0][1] - TOL), default=None)
            if before is None or after is None or abs((sd[0][0] - before) - 0.2) > 0.011 or abs((after - sd[0][1]) - 0.2) > 0.011:
                bad.append("%s: the tab at x=%+.2f is %s / %s clear of the slot in y (want 0.2 each)"
                           % (label, xm, "%.4f" % (sd[0][0] - before) if before is not None else "?", "%.4f" % (after - sd[0][1]) if after is not None else "?"))
            # (c) along x through the tab: the body is 0.4 off the lane face, the tab stops 0.3 short of the slot's bottom
            sx_d = axis_spans(d, 0, cy, ZS)
            sx_b = axis_spans(bmesh, 0, cy, ZS)
            tip = (max(r[1] for r in sx_d) if sgn > 0 else min(r[0] for r in sx_d))
            bottom = min((r[0] for r in sx_b if r[0] >= tip - TOL), default=None) if sgn > 0 else max((r[1] for r in sx_b if r[1] <= tip + TOL), default=None)
            if bottom is None or abs(abs(bottom - tip) - P.TAB_GAP) > 0.011:
                bad.append("%s: the tab tip is %s from the slot's bottom (want %.1f)" % (label, "%.4f" % abs(bottom - tip) if bottom is not None else "?", P.TAB_GAP))
            # (d) it hangs: the tab's underside rests on the slot floor, its top is flush
            xz = face + sgn * 1.0
            sdz, sbz = axis_spans(d, 2, xz, cy), axis_spans(bmesh, 2, xz, cy)
            if not sdz or not sbz:
                bad.append("%s: nothing found at x=%+.2f for the hang" % (label, xz))
            else:
                seat = sdz[0][0] - sbz[0][1]
                if abs(seat) > TOL:
                    bad.append("%s: the tab's underside is %.4f from the slot floor (want it resting on it)" % (label, seat))
                if abs(sdz[0][1] - P.WALL_TOP) > TOL:
                    bad.append("%s: the tab's top is z=%.4f, want flush with the wall top %.4f" % (label, sdz[0][1], P.WALL_TOP))
        # (e) the body is 0.4 off the lane face(s) and clear of the floor
        if side == "both":
            sd, sb = axis_spans(d, 0, cy, 30.0), axis_spans(base, 0, cy, 30.0)
            gl = sd[0][0] - max(r[1] for r in sb if r[1] < 0)
            gr = min(r[0] for r in sb if r[0] > 0) - sd[0][1]
            if abs(gl - P.BODY_CLEAR) > TOL or abs(gr - P.BODY_CLEAR) > TOL:
                bad.append("%s: the body is %.4f / %.4f off the lane faces (want %.1f)" % (label, gl, gr, P.BODY_CLEAR))
            zb = axis_spans(d, 2, cx, cy)[0][0] - axis_spans(bmesh, 2, cx, cy)[0][1]
            if zb < 3.0:
                bad.append("%s: the body's bottom is only %.3f above the floor" % (label, zb))
        return bad

    placements = [("lane 2 slot %d" % (i + 1), 0.0, y, "both") for i, y in enumerate(P.B_YS)]
    for label, cx, cy, side in placements:
        bad = fit_problems(div, base, label, cx, cy, side)
        for m in bad:
            fail(m)
        if not bad:
            ok("%s (y=%+.0f): no overlap; tabs 0.2 clear in y, tips 0.3 short of the slot bottom; body 0.4 off both lane faces; "
               "hangs on the slot floors, tops flush; body %.1f above the floor" % (label, cy, axis_spans(shift(div, (cx, cy, 0.0)), 2, 0.0, cy)[0][0] - P.TEST_FLOOR_T))
    outer = []
    for sgn, name in ((-1, "left"), (1, "right")):
        for k in (0, 3, 6):
            outer.append(("%s outer slot %d" % (name, k + 1), sgn * (P.LANE_W + P.WALL_T), P.A_YS[k], -sgn))
    for label, cx, cy, side in outer:
        bad = fit_problems(div, base, label, cx, cy, side)
        for m in bad:
            fail(m)
        if not bad:
            ok("%s (y=%+.0f): one tab in the wall's outer slot, as a lane 1 / lane 3 divider would be: the same fit" % (label, cy))
    # neighbours, one lane apart, 3 mm along: both in the left partition, on opposite faces
    d1 = shift(div, (-(P.LANE_W + P.WALL_T), P.A_YS[3], 0.0))          # lane 1 at y=0
    d2 = shift(div, (0.0, P.B_YS[3], 0.0))                             # lane 2 at y=+3
    cols = [(-FACE - P.WALL_T + 0.0073 + i * 0.05, -1.0 + j * 0.1) for i in range(0, 110) for j in range(0, 60)]
    o12 = col_overlap(d1, d2, cols)[0]
    ob1, ob2 = col_overlap(base, d1, cols)[0], col_overlap(base, d2, cols)[0]
    (ok if o12 < TOL and ob1 < TOL and ob2 < TOL else fail)(
        "a lane 1 divider at y=0 and a lane 2 divider at y=+3 share the left partition: no overlap between them (%.4f) or with the wall (%.4f, %.4f), and the wall keeps %.1f"
        % (o12, ob1, ob2, P.SKIN))
    # controls
    tall = export(builder.build_divider(tab_reach=P.SLOT_DEPTH + 0.1), "divider-long-tab")
    bt = fit_problems(tall, base, "long-tab", 0.0, P.B_YS[2], "both")
    (ok if bt else fail)("control: a divider whose tabs reach 3.6 (the slot is 3.5 deep) is caught: %s" % (bt[0] if bt else "NOT CAUGHT"))
    bn = fit_problems(div, nos, "no-slots", 0.0, P.B_YS[2], "both")
    (ok if bn else fail)("control: the same divider against a base WITHOUT slots is caught: %s" % (bn[0] if bn else "NOT CAUGHT"))

    print()
    print("=" * 72)
    print("6. the committed STL files are the current design")
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

    stls = {"base": (os.path.join(PART, "slot_test_base.stl"), base), "divider": (os.path.join(PART, "slot_divider.stl"), div)}
    for name, (path, fresh) in stls.items():
        bad = stl_matches(path, fresh)
        for m in bad:
            fail("%s STL: %s" % (name, m))
        if not bad:
            lo, hi = bbox(load_stl(path))
            ok("%s STL: %s, %.3f x %.3f x %.3f mm, as a fresh export of the .slvs" % (name, os.path.basename(path), hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
    wrong = stl_matches(stls["base"][0], div)
    (ok if len(wrong) >= 2 else fail)("control: the base's STL checked as if it were the divider's fails %d ways (the test can fail)" % len(wrong))

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
