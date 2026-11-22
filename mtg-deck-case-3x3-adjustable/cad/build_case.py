#!/usr/bin/env python3
"""Generate the adjustable case's three .slvs files: a tray, a lid and one divider.

    python3 cad/build_case.py          # writes all three, beside cad/
    python3 cad/check_case.py          # verifies them

See case_params.py for what the case is and why.  Built here that the 3 x 3 case
(mtg-deck-case-3x3/cad/build_case.py, which this grew from) did not need:

  * Four 5 mm LANE WALLS (two partitions, two liners) instead of 1.6 mm dividers, in
    the tray and, hanging down to meet them, in the lid.
  * SLOTS in the lane faces: 25 mm deep, 2 mm wide, 3.5 mm into the wall, every 6 mm,
    in two STAGGERED sets (lanes 1 and 3; lane 2, 3 mm along).  Each set is made by
    drawing ONE slot per face and repeating it with SolveSpace's step-and-repeat
    (`Sketch.translate`): two sketches, two extrudes and two repeat groups, and the pitch
    and the count stay editable in the GUI.
  * The DIVIDER: one flat profile (a body and two 25 mm tabs), pinned point by point,
    extruded 1.6 mm.

The group order is the build order, and it matters in the same way as before: every
cut that a solid is meant to keep must come after the solid it cuts.  Scaffolding
groups are hidden and only the last operation is shown.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))
sys.path.insert(0, HERE)

from slvs_write import (Sketch, UNION, DIFFERENCE, TWO_SIDED, PT_PLANE_DISTANCE,
                        POINTS_COINCIDENT, HORIZONTAL, VERTICAL, ARC_LINE_TANGENT,
                        DIAMETER, EQUAL_RADIUS,
                        ENT_XY_WORKPLANE, ENT_YZ_WORKPLANE, ENT_ZX_WORKPLANE)
from slvs_shapes import rect, rounded_rect, rect_at, datums, spherical_cap, corner_wedge
import case_params as C

XY_U, XY_V = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)


def _extrude_from(S, name, g, length, combine, up=True, visible=False):
    """Extrude sketch group g by `length`, up or down from its plane.  An extrude's
    vector is half its length for ONE_SIDED (group.cpp: the far cap is at 2 x vec)."""
    return S.extrude(name, g, (0.0, 0.0, (length if up else -length) / 2.0),
                     combine=combine, visible=visible)


# --------------------------------------------------------------------------
# the snap
# --------------------------------------------------------------------------
def snap_specs(face_x, face_y):
    """The twelve caps: (tag, signed face position, sg, position along the face,
    axis, world point).  Left/right faces carry three each at the same y positions as
    the 3 x 3 case's; front/back faces three each centred on the three lanes."""
    specs = []
    for sg in (-1, 1):
        for k, y in enumerate(C.SNAP_CENTRES_Y):
            specs.append(("%s%d" % ("L" if sg < 0 else "R", k + 1), sg * face_x, sg, y, "x",
                          (sg * face_x, y, C.DOME_Z)))
    for sg in (-1, 1):
        for k, x in enumerate(C.SNAP_CENTRES_X):
            specs.append(("%s%d" % ("F" if sg < 0 else "B", k + 1), sg * face_y, sg, x, "y",
                          (x, sg * face_y, C.DOME_Z)))
    return specs


def snap_caps(S, kind):
    """Twelve domes on the tray's lip (`kind` "bump") or twelve dimples in the lid's
    groove walls ("dimple").  See slvs_shapes.spherical_cap for how one is built; for
    a dimple the apex points INTO the wall, which is outward from the case's axis,
    so `sg` is the same for dome and dimple on a given face."""
    bump = kind == "bump"
    if bump:
        specs = snap_specs(C.LIP_HX, C.LIP_HY)
        h, R, combine = C.BUMP_H, C.BUMP_SPHERE_R, UNION
    else:
        specs = snap_specs(C.GROOVE_HX, C.GROOVE_HY)
        h, R, combine = C.DENT_DEPTH, C.DENT_SPHERE_R, DIFFERENCE
    pts = datums(S, [s[5] for s in specs])
    for i, (spec, pt) in enumerate(zip(specs, pts)):
        tag, face, sg, across, along, _ = spec
        spherical_cap(S, "%s-%s" % (kind, tag), pt, face, sg, across, h, R, combine,
                      visible=(i == len(specs) - 1), along=along)


# --------------------------------------------------------------------------
# the finger ledge
# --------------------------------------------------------------------------
def finger_ledge(S, name, pt_face, up):
    """The shelf on the front of one half: its plan-view outline sketched on the
    half's end face (`pt_face`, a datum on that plane) and pushed LEDGE_H into the
    part (`up` for the tray, whose end face is its underside; down for the lid).

    The outline, counter-clockwise, front edge at the bottom:  in from the wall along
    the left; an arc tangent to the flat; the flat, LEDGE_OUT proud of the wall; a
    mirror arc; back along the right; and a closing line LEDGE_OVERLAP inside the
    wall so the extrude joins the part by overlap, not by sharing a face.  28
    unknowns, 28 equations (the arcs carry one each):

        6 joints, 2 coordinates each                         12
        flat horizontal, the sides vertical, the top
        horizontal                                            4
        the flat's two ends on x = +-LEDGE_FLAT_HX, its
        height on y; the arcs' wall ends on the wall's y;
        the top's y                                           6
        each arc tangent to the flat                          2
        one arc's radius, the other equal to it               2
        the arcs' own equal-distance equation                 2
    """
    xe, xf = C.LEDGE_HX, C.LEDGE_FLAT_HX
    yw = -C.EXT_HY                                   # the front wall
    yf = yw - C.LEDGE_OUT                            # the flat
    yin = yw + C.LEDGE_OVERLAP                       # inside the wall
    rf = C.LEDGE_FLANK_R
    yc = yf + rf                                     # both flank arcs' centres' y
    g, wp = S.workplane_group(name + "-profile", pt_face, XY_U, XY_V, visible=False)
    left = S.line(g, wp, (-xe, yin), (-xe, yw))
    flat = S.line(g, wp, (-xf, yf), (xf, yf))
    right = S.line(g, wp, (xe, yw), (xe, yin))
    top = S.line(g, wp, (xe, yin), (-xe, yin))
    a1 = S.arc(g, wp, (-xf, yc), (-xe, yw), (-xf, yf))    # counter-clockwise: wall to flat
    a2 = S.arc(g, wp, (xf, yc), (xf, yf), (xe, yw))       # counter-clockwise: flat to wall
    # entities are (ent, A, B) for a line, (ent, centre, start, end) for an arc
    for p, q in ((left[2], a1[2]), (a1[3], flat[1]), (flat[2], a2[2]),
                 (a2[3], right[1]), (right[2], top[1]), (top[2], left[1])):
        S.constraint(POINTS_COINCIDENT, g, wp, ptA=p, ptB=q)
    S.constraint(HORIZONTAL, g, wp, entityA=flat[0])
    S.constraint(VERTICAL, g, wp, entityA=left[0])
    S.constraint(VERTICAL, g, wp, entityA=right[0])
    S.constraint(HORIZONTAL, g, wp, entityA=top[0])
    S.constraint(ARC_LINE_TANGENT, g, wp, entityA=a1[0], entityB=flat[0], other=True)
    S.constraint(ARC_LINE_TANGENT, g, wp, entityA=a2[0], entityB=flat[0], other=False)
    S.constraint(DIAMETER, g, wp, valA=2 * rf, entityA=a1[0], other=True,
                 disp=(-xf, yc, 0.0))
    S.constraint(EQUAL_RADIUS, g, wp, entityA=a1[0], entityB=a2[0])
    # the sketch's origin is the case's axis (the datum is at x = y = 0), so (u, v)
    # are world (x, y) and the pins read as the plain numbers they are
    for pt, val, plane in ((flat[1], -xf, ENT_YZ_WORKPLANE), (flat[2], xf, ENT_YZ_WORKPLANE),
                           (flat[1], yf, ENT_ZX_WORKPLANE), (left[2], yw, ENT_ZX_WORKPLANE),
                           (right[1], yw, ENT_ZX_WORKPLANE), (top[2], yin, ENT_ZX_WORKPLANE)):
        S.constraint(PT_PLANE_DISTANCE, g, wp, valA=val, ptA=pt, entityA=plane)
    _extrude_from(S, name, g, C.LEDGE_H, UNION, up=up)


# --------------------------------------------------------------------------
# the lid's mouth bevel
# --------------------------------------------------------------------------
def mouth_chamfer(S, pt_seam):
    """The lead-in round the groove's mouth, so the lid drops on without being lined
    up first.  The single box's bevel (spec D5, D9), on a flat seam: four 45 degree
    wedges, two per axis, each sketched in the plane square to the edge it cuts and
    extruded along it.  Each overshoots the corner by the chamfer size in the other
    axis, so the bevels mitre instead of meeting at coincident faces."""
    ch, over, zs = C.MOUTH_CHAMFER, C.CHAMFER_OVER, C.Z_S

    # the walls at y = +-GROOVE_HY: a profile in the plane x = 0 (u = y, v = z)
    g, wp = S.workplane_group("mouth-chamfer-y", pt_seam, (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
                              visible=False)

    def pin_y(gg, ww, pt, uv):
        S.constraint(PT_PLANE_DISTANCE, gg, valA=uv[0], ptA=pt, entityA=ENT_ZX_WORKPLANE)
        S.constraint(PT_PLANE_DISTANCE, gg, valA=zs + uv[1], ptA=pt, entityA=ENT_XY_WORKPLANE)

    for sg in (1, -1):
        corner_wedge(S, g, wp, corner=(sg * C.GROOVE_HY, 0.0), along_wall=(0.0, 1.0),
                     along_face=(float(sg), 0.0), ch=ch, over=over, pin=pin_y)
    S.extrude("mouth-chamfer-y-cut", g, (C.GROOVE_HX + ch, 0.0, 0.0),
              combine=DIFFERENCE, subtype=TWO_SIDED, visible=False)

    # the walls at x = +-GROOVE_HX: a profile in the plane y = 0 (u = x, v = z)
    g, wp = S.workplane_group("mouth-chamfer-x", pt_seam, (1.0, 0.0, 0.0), (0.0, 0.0, 1.0),
                              visible=False)

    def pin_x(gg, ww, pt, uv):
        S.constraint(PT_PLANE_DISTANCE, gg, valA=uv[0], ptA=pt, entityA=ENT_YZ_WORKPLANE)
        S.constraint(PT_PLANE_DISTANCE, gg, valA=zs + uv[1], ptA=pt, entityA=ENT_XY_WORKPLANE)

    for sg in (1, -1):
        corner_wedge(S, g, wp, corner=(sg * C.GROOVE_HX, 0.0), along_wall=(0.0, 1.0),
                     along_face=(float(sg), 0.0), ch=ch, over=over, pin=pin_x)
    S.extrude("mouth-chamfer-x-cut", g, (0.0, C.GROOVE_HY + ch, 0.0),
              combine=DIFFERENCE, subtype=TWO_SIDED, visible=False)


# --------------------------------------------------------------------------
# the lane walls
# --------------------------------------------------------------------------
def lane_wall_rects(S, g, wp, pad_to_x):
    """The four lane walls as rectangles in sketch group g, each running the whole
    depth and INTO the front and back walls (WALL_OVERLAP) so it joins by overlap.
    A liner also runs `pad_to_x` into the outer wall beside it, for the same reason:
    its outer face would otherwise lie exactly in the cavity wall's plane."""
    for cx, kind in zip(C.WALL_CENTRES_X, C.WALL_KINDS):
        hx, mid = C.WALL_T / 2.0, cx
        if kind == "liner-l":
            hx, mid = (C.WALL_T + pad_to_x) / 2.0, cx - pad_to_x / 2.0
        elif kind == "liner-r":
            hx, mid = (C.WALL_T + pad_to_x) / 2.0, cx + pad_to_x / 2.0
        rect_at(S, g, wp, mid, 0.0, hx, C.IN_HY + C.WALL_OVERLAP)


def slots(S, pt_cut, stagger=True):
    """The slots in the lane faces: one drawn per face at the set's first y, then repeated
    at the pitch, once for set A (lanes 1 and 3) and once for set B (lane 2).  `pt_cut` is
    a datum OVER above the wall top, so each cutter starts in air.  Each slot cuts SLOT_DEPTH
    into the wall and 1 mm out into the lane, in air, so no cutter face lies in the wall's
    own face.  stagger=False puts set B at set A's positions, for the verification's
    control: the partitions are then cut through."""
    for name, ys in (("a", C.A_YS), ("b", C.B_YS if stagger else C.A_YS)):
        g, wp = S.workplane_group("slots-%s-profile" % name, pt_cut, XY_U, XY_V, visible=False)
        for face, into, which in C.SLOT_FACES:
            if which.lower() != name:
                continue
            lo, hi = (face - 1.0, face + C.SLOT_DEPTH) if into > 0 else (face - C.SLOT_DEPTH, face + 1.0)
            rect_at(S, g, wp, (lo + hi) / 2.0, ys[0], (hi - lo) / 2.0, C.SLOT_W / 2.0)
        eg = _extrude_from(S, "slot-%s-cut" % name, g, C.SLOT_H + C.OVER, DIFFERENCE, up=False)
        S.translate("slots-%s-repeat" % name, eg, (0.0, C.SLOT_PITCH, 0.0), len(ys), DIFFERENCE)


# --------------------------------------------------------------------------
# the tray
# --------------------------------------------------------------------------
def build_bottom(bumps=True, ledge=True, slots_on=True, stagger=True):
    """bumps=False leaves out the snap domes, ledge=False the finger ledge, slots_on=False
    the slots, stagger=False puts lane 2's slots at lanes 1 and 3's positions: for the
    verification's controls."""
    S = Sketch()
    pt_seam, pt_lip, pt_floor, pt_wall, pt_base, pt_cut = datums(
        S, [(0.0, 0.0, C.Z_S), (0.0, 0.0, C.Z_LIP), (0.0, 0.0, C.FLOOR_T),
            (0.0, 0.0, C.WALL_TOP), (0.0, 0.0, 0.0), (0.0, 0.0, C.WALL_TOP + C.OVER)])

    # 1. the outer walls, sketched on the seam plane and pushed down to the floor's underside
    g, wp = S.workplane_group("outer-profile", pt_seam, XY_U, XY_V, visible=False)
    rounded_rect(S, g, wp, C.EXT_HX, C.EXT_HY, C.EXT_CORNER_R)
    _extrude_from(S, "outer-block", g, C.Z_S, UNION, up=False)

    # 1b. the finger ledge, flush with the underside, so the tray stands on it
    if ledge:
        finger_ledge(S, "ledge", pt_base, up=True)

    # 2. the lip, on the lip-top plane, pushed down into the walls (to 1 mm up)
    g, wp = S.workplane_group("lip-profile", pt_lip, XY_U, XY_V, visible=False)
    rounded_rect(S, g, wp, C.LIP_HX, C.LIP_HY, C.LIP_CORNER_R)
    _extrude_from(S, "lip-block", g, C.Z_LIP - C.WALL_BASE_Z, UNION, up=False)

    # 3. one cavity for the whole case, from the floor up and out through the lip
    g, wp = S.workplane_group("cavity-profile", pt_floor, XY_U, XY_V, visible=False)
    rect(S, g, wp, C.IN_HX, C.IN_HY)
    _extrude_from(S, "cavity-cut", g, C.Z_LIP + C.OVER - C.FLOOR_T, DIFFERENCE, up=True)

    # 4. the four lane walls, added back into the cavity, from just under the lip top down
    #    into the floor.  They are disjoint, so one sketch.
    g, wp = S.workplane_group("walls-profile", pt_wall, XY_U, XY_V, visible=False)
    lane_wall_rects(S, g, wp, pad_to_x=1.0)
    _extrude_from(S, "lane-walls", g, C.WALL_TOP - C.WALL_BASE_Z, UNION, up=False)

    # 5. the slots
    if slots_on:
        slots(S, pt_cut, stagger)

    # 6. the snap domes
    if bumps:
        snap_caps(S, "bump")
    return S


# --------------------------------------------------------------------------
# the lid
# --------------------------------------------------------------------------
def build_top(dimples=True, ledge=True):
    """dimples=False builds a lid without the snap dimples, ledge=False one without
    the finger ledge: the verification uses both to prove its tests can fail."""
    S = Sketch()
    pt_seam, pt_lip, pt_ceil, pt_hang, pt_top = datums(
        S, [(0.0, 0.0, C.Z_S), (0.0, 0.0, C.Z_LIP), (0.0, 0.0, C.Z_CEIL),
            (0.0, 0.0, C.LID_WALL_BOTTOM), (0.0, 0.0, C.H_TOTAL)])

    # 1. the outer block, sketched on the seam and pushed UP to the roof of the lid
    g, wp = S.workplane_group("outer-profile", pt_seam, XY_U, XY_V, visible=False)
    rounded_rect(S, g, wp, C.EXT_HX, C.EXT_HY, C.EXT_CORNER_R)
    _extrude_from(S, "outer-block", g, C.LID_H, UNION, up=True)

    # 1b. the finger ledge, flush with the top
    if ledge:
        finger_ledge(S, "ledge", pt_top, up=False)

    # 2. the cavity, down from the ceiling and out through the open bottom
    g, wp = S.workplane_group("cavity-profile", pt_ceil, XY_U, XY_V, visible=False)
    rect(S, g, wp, C.IN_HX, C.IN_HY)
    _extrude_from(S, "cavity-cut", g, C.Z_CEIL - C.Z_S + C.OVER, DIFFERENCE, up=False)

    # 3. the groove the tray's lip slides into
    g, wp = S.workplane_group("groove-profile", pt_lip, XY_U, XY_V, visible=False)
    rect(S, g, wp, C.GROOVE_HX, C.GROOVE_HY)
    _extrude_from(S, "groove-cut", g, C.Z_LIP - C.Z_S + C.OVER, DIFFERENCE, up=False)

    # 4. the lead-in bevel round the groove's mouth
    mouth_chamfer(S, pt_seam)

    # 5. the lid's walls, hung from the ceiling to meet the tray's lane walls: the same
    #    four, 5 mm, with the same overlaps (into the ceiling, the front and back, and
    #    for a liner into the rim beside it)
    g, wp = S.workplane_group("hangers-profile", pt_hang, XY_U, XY_V, visible=False)
    lane_wall_rects(S, g, wp, pad_to_x=1.0)
    _extrude_from(S, "lane-walls", g, C.Z_CEIL + C.WALL_OVERLAP - C.LID_WALL_BOTTOM, UNION, up=True)

    # 6. the snap dimples
    if dimples:
        snap_caps(S, "dimple")
    return S


# --------------------------------------------------------------------------
# the divider
# --------------------------------------------------------------------------
def divider_outline(tab_reach=None):
    """The divider's profile in (x, z), counter-clockwise from the body's bottom left:
    up the body's left edge to the tab's underside, out along it, up the tab's end to the
    wall top, back in along the tab's top (flush with the wall top), up the body to its
    top, and the mirror image.  `tab_reach` (default TAB_REACH) is how far a tab goes into
    the wall from the lane face; a larger value is a tab that cannot fit the slot, for a
    control."""
    reach = C.TAB_REACH if tab_reach is None else tab_reach
    hw, out = C.DIV_BODY_HX, C.LANE_W / 2.0 + reach
    zb, zt, zk, zs = C.DIV_BOTTOM, C.DIV_TOP, C.WALL_TOP, C.DIV_TAB_BOTTOM
    left = [(-hw, zb), (-hw, zs), (-out, zs), (-out, zk), (-hw, zk), (-hw, zt)]
    right = [(hw, zt), (hw, zk), (out, zk), (out, zs), (hw, zs), (hw, zb)]
    return left + right


def build_divider(tab_reach=None):
    """One divider, standing in the case frame at x = y = 0 (so it sits in the middle
    lane).  The profile is drawn in the x-z plane and extruded DIV_T, centred on y = 0.
    Every vertex is pinned by two plane distances: 12 lines x 4 coordinates = 48 unknowns,
    12 joints x 2 = 24 equations and 24 pins, so 0 DOF and none redundant."""
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
    S.extrude("divider", g, (0.0, C.DIV_T / 2.0, 0.0), combine=UNION, subtype=TWO_SIDED, visible=True)
    return S


def main():
    out = os.path.normpath(os.path.join(HERE, ".."))
    for name, fn in (("deck_case_adjustable_bottom.slvs", build_bottom),
                     ("deck_case_adjustable_top.slvs", build_top),
                     ("deck_case_adjustable_divider.slvs", build_divider)):
        path = os.path.join(out, name)
        fn().write(path)
        print("wrote %s" % path)


if __name__ == "__main__":
    main()
