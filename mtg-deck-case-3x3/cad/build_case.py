#!/usr/bin/env python3
"""Generate the 3 x 3 deck case's two .slvs files: a tray and a lid.

    python3 cad/build_case.py          # writes both, beside cad/
    python3 cad/check_case.py          # verifies them

The case is the single deck box (mtg-deck-boxes/) as a grid, and this is its
generator.  Everything dimensional is in case_params.py and almost all of that is
imported from the single box.  What is built here that the single box did not
need:

  * A FLAT seam.  The single box's seam slopes front to back, so every cut there is
    on a tilted plane and some had to be built sideways (an extrude cannot be skewed;
    see that box's spec 6.1).  Here everything is axis-aligned: blocks and cutters
    are plain vertical extrudes, and the only things that are not boxes are the
    snap caps.
  * Dividers: the tray has them in both directions, the lid in one only (case_params
    explains why).
  * Snap domes and dimples on ALL FOUR sides, three per side, each centred on a slot.

The group order is the build order, and it matters in the same way as before: every
cut that the lid's solid is meant to keep must come after the solid it cuts.
Scaffolding groups are hidden and only the last operation is shown, so the file
opens as the part rather than as a thicket of wireframe.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))
sys.path.insert(0, HERE)

from slvs_write import (Sketch, UNION, DIFFERENCE, TWO_SIDED, PT_PLANE_DISTANCE,
                        ENT_XY_WORKPLANE, ENT_YZ_WORKPLANE, ENT_ZX_WORKPLANE)
from slvs_shapes import rect, rounded_rect, rect_at, datums, spherical_cap, corner_wedge
import case_params as C

XY_U, XY_V = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)


def _extrude_from(S, name, g, length, combine, up=True, visible=False):
    """Extrude sketch group g by `length`, up or down from its plane.  An extrude's
    vector is half its length for ONE_SIDED (group.cpp: the far cap is at 2 x vec)."""
    S.extrude(name, g, (0.0, 0.0, (length if up else -length) / 2.0),
              combine=combine, visible=visible)


# --------------------------------------------------------------------------
# the snap
# --------------------------------------------------------------------------
def snap_specs(face_x, face_y):
    """The twelve caps: (tag, signed face position, sg, position along the face,
    axis, world point).  Left/right faces carry three each at the slot rows'
    y positions; front/back faces three each at the slot columns' x positions."""
    specs = []
    for sg in (-1, 1):
        for k, y in enumerate(C.SLOT_CENTRES_Y):
            specs.append(("%s%d" % ("L" if sg < 0 else "R", k + 1), sg * face_x, sg, y, "x",
                          (sg * face_x, y, C.DOME_Z)))
    for sg in (-1, 1):
        for k, x in enumerate(C.SLOT_CENTRES_X):
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
# the tray
# --------------------------------------------------------------------------
def build_bottom(bumps=True):
    """bumps=False leaves out the snap domes, for the verification's controls."""
    S = Sketch()
    pt_seam, pt_lip, pt_floor, pt_div = datums(S, [(0.0, 0.0, C.Z_S), (0.0, 0.0, C.Z_LIP),
                                                   (0.0, 0.0, C.FLOOR_T),
                                                   (0.0, 0.0, C.DIV_TRAY_TOP)])

    # 1. the outer walls, sketched on the seam plane and pushed down to the floor's
    #    underside: so the one plane that mates with the lid is the dimensioned one
    g, wp = S.workplane_group("outer-profile", pt_seam, XY_U, XY_V, visible=False)
    rounded_rect(S, g, wp, C.EXT_HX, C.EXT_HY, C.EXT_CORNER_R)
    _extrude_from(S, "outer-block", g, C.Z_S, UNION, up=False)

    # 2. the lip: the same outline as the single box's, sketched on the lip-top plane
    #    and pushed down into the walls (to 1 mm up, not to the floor's underside, so
    #    its bottom face is not coplanar with the outer block's)
    g, wp = S.workplane_group("lip-profile", pt_lip, XY_U, XY_V, visible=False)
    rounded_rect(S, g, wp, C.LIP_HX, C.LIP_HY, C.LIP_CORNER_R)
    _extrude_from(S, "lip-block", g, C.Z_LIP - C.DIV_BASE_Z, UNION, up=False)

    # 3. one cavity for the whole grid, from the floor up and out through the lip
    g, wp = S.workplane_group("cavity-profile", pt_floor, XY_U, XY_V, visible=False)
    rect(S, g, wp, C.IN_HX, C.IN_HY)
    _extrude_from(S, "cavity-cut", g, C.Z_LIP + C.OVER - C.FLOOR_T, DIFFERENCE, up=True)

    # 4. the dividers, added back into the cavity: two sets, in two groups, because
    #    bars that cross cannot share a sketch.  Each runs INTO the lip or wall at
    #    both ends, so it joins by overlap, not by sharing a face.
    h_bar = C.DIV_TRAY_TOP - C.DIV_BASE_Z
    g, wp = S.workplane_group("dividers-x-profile", pt_div, XY_U, XY_V, visible=False)
    for y in C.DIV_Y:                                    # bars running along x
        rect_at(S, g, wp, 0.0, y, C.IN_HX + C.DIV_OVERLAP, C.INNER_T / 2.0)
    _extrude_from(S, "dividers-x", g, h_bar, UNION, up=False)
    g, wp = S.workplane_group("dividers-y-profile", pt_div, XY_U, XY_V, visible=False)
    for x in C.DIV_X:                                    # bars running along y
        rect_at(S, g, wp, x, 0.0, C.INNER_T / 2.0, C.IN_HY + C.DIV_OVERLAP)
    _extrude_from(S, "dividers-y", g, h_bar, UNION, up=False)

    # 5. the snap domes
    if bumps:
        snap_caps(S, "bump")
    return S


# --------------------------------------------------------------------------
# the lid
# --------------------------------------------------------------------------
def build_top(dimples=True):
    """dimples=False builds a lid without the snap dimples, which the verification
    uses to prove its engagement test can fail."""
    S = Sketch()
    pt_seam, pt_lip, pt_ceil, pt_div = datums(S, [(0.0, 0.0, C.Z_S), (0.0, 0.0, C.Z_LIP),
                                                  (0.0, 0.0, C.Z_CEIL),
                                                  (0.0, 0.0, C.DIV_LID_BOTTOM)])

    # 1. the outer block, sketched on the seam and pushed UP to the roof of the lid
    g, wp = S.workplane_group("outer-profile", pt_seam, XY_U, XY_V, visible=False)
    rounded_rect(S, g, wp, C.EXT_HX, C.EXT_HY, C.EXT_CORNER_R)
    _extrude_from(S, "outer-block", g, C.LID_H, UNION, up=True)

    # 2. the cavity, down from the ceiling and out through the open bottom
    g, wp = S.workplane_group("cavity-profile", pt_ceil, XY_U, XY_V, visible=False)
    rect(S, g, wp, C.IN_HX, C.IN_HY)
    _extrude_from(S, "cavity-cut", g, C.Z_CEIL - C.Z_S + C.OVER, DIFFERENCE, up=False)

    # 3. the groove the tray's lip slides into: sketched on the roof plane and cut
    #    down through the seam.  Sharp corners, so it clears the lip's rounded ones.
    g, wp = S.workplane_group("groove-profile", pt_lip, XY_U, XY_V, visible=False)
    rect(S, g, wp, C.GROOVE_HX, C.GROOVE_HY)
    _extrude_from(S, "groove-cut", g, C.Z_LIP - C.Z_S + C.OVER, DIFFERENCE, up=False)

    # 4. the lead-in bevel round the groove's mouth
    mouth_chamfer(S, pt_seam)

    # 5. the lid's dividers, front to back only, hung from the ceiling.  They run INTO
    #    the ceiling and into the front and back walls above the groove roof.
    g, wp = S.workplane_group("dividers-y-profile", pt_div, XY_U, XY_V, visible=False)
    for x in C.DIV_X:
        rect_at(S, g, wp, x, 0.0, C.INNER_T / 2.0, C.IN_HY + C.DIV_OVERLAP)
    _extrude_from(S, "dividers-y", g, C.Z_CEIL + C.DIV_OVERLAP - C.DIV_LID_BOTTOM, UNION, up=True)

    # 6. the snap dimples
    if dimples:
        snap_caps(S, "dimple")
    return S


def main():
    out = os.path.normpath(os.path.join(HERE, ".."))
    for name, fn in (("deck_case_3x3_bottom.slvs", build_bottom),
                     ("deck_case_3x3_top.slvs", build_top)):
        path = os.path.join(out, name)
        fn().write(path)
        print("wrote %s" % path)


if __name__ == "__main__":
    main()
