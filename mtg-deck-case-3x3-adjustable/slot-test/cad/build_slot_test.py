#!/usr/bin/env python3
"""Generate the slot-and-tab test pieces: one divider and a short single-lane base.

    python3 cad/build_slot_test.py     # writes both .slvs, beside cad/
    python3 cad/check_slot_test.py     # verifies them

See slot_params.py for what this is and why.

  * The divider is one flat profile (body plus two 25 mm tabs, no arms), pinned vertex
    by vertex and extruded 1.6 mm.
  * The base is a 1 mm floor and the two 5 mm partition walls of the middle lane, 48 mm
    long, 73.4 mm tall (the divider hangs 44 mm below its tabs, so the walls cannot be
    shorter without a shorter divider), with the slots: set B on the faces towards the
    lane, set A on the outer faces.  Each set is ONE slot drawn per wall and repeated
    with step-and-repeat (`Sketch.translate`).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "utilities"))
sys.path.insert(0, HERE)

from slvs_write import (Sketch, UNION, DIFFERENCE, TWO_SIDED, PT_PLANE_DISTANCE,
                        POINTS_COINCIDENT, ENT_XY_WORKPLANE, ENT_YZ_WORKPLANE)
from slvs_shapes import rect_at, datums
import slot_params as P

XY_U, XY_V = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)


def _extrude_from(S, name, g, length, combine, up=True, visible=False):
    """Extrude sketch group g by `length`, up or down from its plane (an extrude's
    vector is half its length for ONE_SIDED)."""
    return S.extrude(name, g, (0.0, 0.0, (length if up else -length) / 2.0),
                     combine=combine, visible=visible)


# --------------------------------------------------------------------------
# the divider
# --------------------------------------------------------------------------
def divider_outline(tab_reach=None):
    """The divider's profile in (x, z), counter-clockwise from the body's bottom left:
    up the body's left edge to the tab's underside, out along it, up the tab's end to
    the wall top, back in along the tab's top (which is flush with the wall top), up
    the body to its top, and the mirror image.  `tab_reach` (default TAB_REACH) is how
    far the tab goes into the wall from the lane face; a larger value is a tab that
    cannot fit the slot, for a control."""
    reach = P.TAB_REACH if tab_reach is None else tab_reach
    hw, out = P.DIV_BODY_HX, P.LANE_W / 2.0 + reach
    zb, zt, zk, zs = P.DIV_BOTTOM, P.DIV_TOP, P.WALL_TOP, P.DIV_TAB_BOTTOM
    left = [(-hw, zb), (-hw, zs), (-out, zs), (-out, zk), (-hw, zk), (-hw, zt)]
    right = [(hw, zt), (hw, zk), (out, zk), (out, zs), (hw, zs), (hw, zb)]
    return left + right


def build_divider(tab_reach=None):
    """One divider, standing in the case frame at x = y = 0 (the middle lane).  Drawn
    in the x-z plane, extruded DIV_T centred on y = 0.  Every vertex is pinned by two
    plane distances: 12 lines x 4 coordinates = 48 unknowns; 12 joints x 2 = 24
    equations and 24 pins, so 0 DOF and none redundant."""
    S = Sketch()
    (pt_o,) = datums(S, [(0.0, 0.0, 0.0)])
    g, wp = S.workplane_group("divider-profile", pt_o, (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), visible=False)
    pts = divider_outline(tab_reach)
    n = len(pts)
    lines = [S.line(g, wp, pts[i], pts[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        S.constraint(POINTS_COINCIDENT, g, wp, ptA=lines[i][2], ptB=lines[(i + 1) % n][1])
        x, z = pts[i]
        S.constraint(PT_PLANE_DISTANCE, g, wp, valA=x, ptA=lines[i][1], entityA=ENT_YZ_WORKPLANE)
        S.constraint(PT_PLANE_DISTANCE, g, wp, valA=z, ptA=lines[i][1], entityA=ENT_XY_WORKPLANE)
    S.extrude("divider", g, (0.0, P.DIV_T / 2.0, 0.0), combine=UNION, subtype=TWO_SIDED, visible=True)
    return S


# --------------------------------------------------------------------------
# the test base
# --------------------------------------------------------------------------
def build_base(slots=True, stagger=True):
    """slots=False leaves the slots out, stagger=False puts set A at set B's positions
    (a wall cut through at each): the verification's controls."""
    S = Sketch()
    pt_base, pt_top, pt_cut = datums(S, [(0.0, 0.0, 0.0), (0.0, 0.0, P.WALL_TOP),
                                         (0.0, 0.0, P.WALL_TOP + P.OVER)])
    half_w = P.LANE_W / 2.0 + P.WALL_T

    # 1. the floor: a thin plate across both walls and the lane between
    g, wp = S.workplane_group("floor-profile", pt_base, XY_U, XY_V, visible=False)
    rect_at(S, g, wp, 0.0, 0.0, half_w, P.TEST_HY)
    _extrude_from(S, "floor", g, P.TEST_FLOOR_T, UNION, up=True)

    # 2. the two partition walls, from the wall top down into the floor
    g, wp = S.workplane_group("walls-profile", pt_top, XY_U, XY_V, visible=False)
    for sgn in (-1, 1):
        rect_at(S, g, wp, sgn * P.WALL_CX, 0.0, P.WALL_T / 2.0, P.TEST_HY)
    _extrude_from(S, "walls", g, P.WALL_TOP - P.TEST_WALL_BASE, UNION, up=False)

    if slots:
        n_b, n_a = len(P.B_YS), len(P.A_YS)
        ya = P.A_YS[0] if stagger else P.B_YS[0]
        na = n_a if stagger else n_b
        # 3. set B: the slots on the lane faces (lane 2's), cut 3.5 into the wall and 1 mm out
        #    into the lane, in air, so no cutter face lies in the wall's own face
        g, wp = S.workplane_group("slots-b-profile", pt_cut, XY_U, XY_V, visible=False)
        for sgn in (-1, 1):
            face = sgn * P.LANE_W / 2.0                    # the lane face
            lo, hi = (face - P.SLOT_DEPTH, face + 1.0) if sgn < 0 else (face - 1.0, face + P.SLOT_DEPTH)
            rect_at(S, g, wp, (lo + hi) / 2.0, P.B_YS[0], (hi - lo) / 2.0, P.SLOT_W / 2.0)
        eg = _extrude_from(S, "slot-b-cut", g, P.SLOT_H + P.OVER, DIFFERENCE, up=False)
        S.translate("slots-b-repeat", eg, (0.0, P.SLOT_PITCH, 0.0), n_b, DIFFERENCE)
        # 4. set A: the slots on the outer faces (what lanes 1 and 3 would use)
        g, wp = S.workplane_group("slots-a-profile", pt_cut, XY_U, XY_V, visible=False)
        for sgn in (-1, 1):
            face = sgn * (P.LANE_W / 2.0 + P.WALL_T)       # the outer face
            lo, hi = (face - 1.0, face + P.SLOT_DEPTH) if sgn < 0 else (face - P.SLOT_DEPTH, face + 1.0)
            rect_at(S, g, wp, (lo + hi) / 2.0, ya, (hi - lo) / 2.0, P.SLOT_W / 2.0)
        eg = _extrude_from(S, "slot-a-cut", g, P.SLOT_H + P.OVER, DIFFERENCE, up=False)
        S.translate("slots-a-repeat", eg, (0.0, P.SLOT_PITCH, 0.0), na, DIFFERENCE)
    return S


def main():
    out = os.path.normpath(os.path.join(HERE, ".."))
    for name, fn in (("slot_divider.slvs", build_divider), ("slot_test_base.slvs", build_base)):
        path = os.path.join(out, name)
        fn().write(path)
        print("wrote %s" % path)


if __name__ == "__main__":
    main()
