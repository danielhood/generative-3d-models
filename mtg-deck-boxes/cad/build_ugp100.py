#!/usr/bin/env python3
"""Generate the two Ultra Guard Pro 100+ .slvs files.

    python3 cad/build_ugp100.py      # writes both .slvs beside orig/
    python3 cad/check_ugp100.py      # verifies them against the source STLs

Why a generator rather than a hand-built sketch: every number in here was
measured off the source STLs, and several are only meaningful as
`base_value * scale` (see ugp100_params).  Writing them once, in one place,
is the only way the bottom's lip and the top's groove stay in step.  Running
this reproduces both .slvs byte for byte.

What SolveSpace 3.3 will and will not do, which is what shaped the build
order below (the long version is spec section 6):

  * No 3D fillet and no sweep.  So the horizontal perimeter rounds are
    dropped -- a round that runs around a rounded-rectangle perimeter needs
    one of them.
  * An extrude's end caps are always parallel to its sketch plane, so
    anything bounded by the slanted seam has to be sketched on a plane
    parallel to it.
  * But the extrude must then go along that plane's OWN NORMAL.  The obvious
    alternative -- sketch on the slanted plane, push straight down, get
    vertical walls under a slanted cap -- builds exactly the right solid and
    then fails the NURBS boolean outright.  Where a cut needs both vertical
    walls and a slanted cap, the slant goes in the PROFILE instead: see
    groove_cutter().
  * A cutter whose cap is seam-parallel but whose depth is a vertical
    distance has a cap that climbs 0.483 mm per mm of +y, so "12 mm clear of
    the part" at one end is well inside it at the other.  Both parts open
    along the seam early, so every later cutter is bounded by a surface it
    is parallel to.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))
sys.path.insert(0, HERE)

from slvs_write import (Sketch, ENT_ORIGIN, UNION, DIFFERENCE,
                        POINTS_COINCIDENT, HORIZONTAL, VERTICAL,
                        PT_PT_DISTANCE, SYMMETRIC_HORIZ, SYMMETRIC_VERT,
                        EQUAL_RADIUS, DIAMETER, ARC_LINE_TANGENT,
                        AT_MIDPOINT, ANGLE, TWO_SIDED)
import ugp100_params as P


# --------------------------------------------------------------------------
# sketch helpers
# --------------------------------------------------------------------------
def rect(S, g, wp, hx, hy, dim=True):
    """Closed sharp-cornered rectangle, |u| <= hx, |v| <= hy, counter-clockwise."""
    c = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    L = [S.line(g, wp, c[i], c[(i + 1) % 4]) for i in range(4)]
    for i in range(4):
        S.constraint(POINTS_COINCIDENT, g, wp, ptA=L[i][2], ptB=L[(i + 1) % 4][1])
    S.constraint(HORIZONTAL, g, wp, entityA=L[2][0])
    S.constraint(VERTICAL, g, wp, entityA=L[3][0])
    if not dim:
        S.constraint(HORIZONTAL, g, wp, entityA=L[0][0])
        S.constraint(VERTICAL, g, wp, entityA=L[1][0])
    if dim:
        # symmetric-h holds a horizontal edge's two ends at +-u, which makes it
        # horizontal as well -- so it replaces HORIZONTAL on that edge rather
        # than joining it (the GUI deletes the redundant one for you).
        S.constraint(SYMMETRIC_HORIZ, g, wp, ptA=L[0][1], ptB=L[0][2])
        S.constraint(SYMMETRIC_VERT, g, wp, ptA=L[1][1], ptB=L[1][2])
        S.constraint(PT_PT_DISTANCE, g, wp, valA=2 * hx, ptA=L[0][1], ptB=L[0][2],
                     disp=(0.0, -hy - 6.0, 0.0))
        S.constraint(PT_PT_DISTANCE, g, wp, valA=2 * hy, ptA=L[1][1], ptB=L[1][2],
                     disp=(hx + 6.0, 0.0, 0.0))
    return L


def rounded_rect(S, g, wp, hx, hy, r, dim=True):
    """Closed rounded rectangle: 4 lines + 4 counter-clockwise corner arcs."""
    L = [S.line(g, wp, a, b) for a, b in
         [((-hx + r, -hy), (hx - r, -hy)),
          ((hx, -hy + r), (hx, hy - r)),
          ((hx - r, hy), (-hx + r, hy)),
          ((-hx, hy - r), (-hx, -hy + r))]]
    A = [S.arc(g, wp, c, s, e) for c, s, e in
         [((hx - r, -hy + r), (hx - r, -hy), (hx, -hy + r)),
          ((hx - r, hy - r), (hx, hy - r), (hx - r, hy)),
          ((-hx + r, hy - r), (-hx + r, hy), (-hx, hy - r)),
          ((-hx + r, -hy + r), (-hx, -hy + r), (-hx + r, -hy))]]
    for i in range(4):
        S.constraint(POINTS_COINCIDENT, g, wp, ptA=L[i][2], ptB=A[i][2])
        S.constraint(POINTS_COINCIDENT, g, wp, ptA=A[i][3], ptB=L[(i + 1) % 4][1])
    S.constraint(HORIZONTAL, g, wp, entityA=L[2][0])
    S.constraint(VERTICAL, g, wp, entityA=L[3][0])
    if not dim:
        S.constraint(HORIZONTAL, g, wp, entityA=L[0][0])
        S.constraint(VERTICAL, g, wp, entityA=L[1][0])
    for i in range(4):
        S.constraint(ARC_LINE_TANGENT, g, wp, entityA=A[i][0], entityB=L[i][0],
                     other=False)
        S.constraint(ARC_LINE_TANGENT, g, wp, entityA=A[i][0],
                     entityB=L[(i + 1) % 4][0], other=True)
    for i in range(1, 4):
        S.constraint(EQUAL_RADIUS, g, wp, entityA=A[0][0], entityB=A[i][0])
    if dim:
        S.constraint(DIAMETER, g, wp, valA=2 * r, entityA=A[0][0], other=True,
                     disp=(hx + 3.0, -hy - 3.0, 0.0))
        S.constraint(SYMMETRIC_HORIZ, g, wp, ptA=L[0][1], ptB=L[0][2])
        S.constraint(SYMMETRIC_VERT, g, wp, ptA=L[1][1], ptB=L[1][2])
        S.constraint(PT_PT_DISTANCE, g, wp, valA=2 * (hx - r), ptA=L[0][1], ptB=L[0][2],
                     disp=(0.0, -hy - 6.0, 0.0))
        S.constraint(PT_PT_DISTANCE, g, wp, valA=2 * (hy - r), ptA=L[1][1], ptB=L[1][2],
                     disp=(hx + 6.0, 0.0, 0.0))
    return L, A


XY_U, XY_V = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
# a plane whose sketch u,v read straight off as world y,z (normal = +x)
YZ_U, YZ_V = (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
# in-plane axes of a seam-parallel plane: u along +x, v tilted up toward +y
SEAM_U = (1.0, 0.0, 0.0)
SEAM_V = (0.0, P.SEAM_COS, P.SEAM_SIN)


def seam_cover(S, name, origin_pt, z0, z_from, z_to, up, visible=False):
    """Cut everything on one side of a seam-parallel plane through `origin_pt`
    (which sits on the box axis at height `z0`).  `up` says which side goes.

    Sized, not guessed.  A point of the part maps into this sketch at
    u = x and v = cos.y + sin.(z - z0), and the second term is worth more than
    the footprint is -- sizing v by EXT_HY alone leaves the cutter too small at
    the corners.  The reach along the normal is bounded the same way.  Keeping
    both tight matters for more than tidiness: this group's wireframe is what
    you see when the file opens.
    """
    zs = [z_from - z0, z_to - z0]
    hu = P.EXT_HX + P.OVER
    hv = P.SEAM_COS * P.EXT_HY + P.SEAM_SIN * max(abs(z) for z in zs) + P.OVER
    reach = P.SEAM_SIN * P.EXT_HY + P.SEAM_COS * max(abs(z) for z in zs) + P.OVER
    direction = P.SEAM_N if up else tuple(-c for c in P.SEAM_N)
    g, wp = S.workplane_group(name + "-plane", origin_pt, SEAM_U, SEAM_V,
                              visible=False)
    rect(S, g, wp, hu, hv)
    S.extrude(name, g, tuple(c * reach / 2.0 for c in direction),
              combine=DIFFERENCE, visible=visible)


# Everything except the datums and the final operation of each part is marked
# not-visible: the scaffolding sketches include cutters sized to swallow the
# whole box, and with them all shown the file opens as an unreadable thicket of
# wireframe instead of as the part.  Unhide them in the GUI when editing.
def datums(S, points):
    """One DRAWING_3D group holding the model's datum points, each pinned by
    three dimensions.  Everything that has to sit at a particular height hangs
    off one of these rather than off a bare extrude length."""
    g = S.group_3d("datums")
    out = []
    for xyz in points:
        _, pt = S.datum_point(g, xyz)
        S.lock_point(g, pt, xyz)
        out.append(pt)
    return out


def groove_cutter(S, origin_pt, hy, depth, visible=False):
    """The cut that forms the top's groove: a prism bounded by four vertical
    planes (x = +-GROOVE_HX from the extrude, y = +-hy from the profile), a
    slanted roof ON the lip-top plane, and a floor well below the part.

    It has to be built this way round because a SKEWED extrude -- a sketch on
    the slanted plane pushed along some other direction -- is what you reach
    for first and it does not work: SolveSpace generates the geometry but its
    NURBS boolean then fails outright ("trim was empty", self-intersecting
    mesh).  Sketching the slant as a LINE on an x-normal plane and extruding
    along that plane's own normal keeps every extrude square and works.

    The workplane origin sits at (-GROOVE_HX, 0, Z_LIP), so sketch (u, v)
    reads as (y, z - Z_LIP) and the roof line runs through the origin.
    """
    g, wp = S.workplane_group("groove-profile", origin_pt, YZ_U, YZ_V,
                              visible=False)
    # origin_pt is on the box axis, so this is the plane x = 0 and the extrude
    # below is TWO_SIDED -- the groove's two x walls come out symmetric from the
    # one half-width param instead of from a start plane plus a length.
    vb = -(hy * P.SEAM_TAN + depth)                     # floor, below everything
    c = [(-hy, vb), (hy, vb), (hy, hy * P.SEAM_TAN), (-hy, -hy * P.SEAM_TAN)]
    L = [S.line(g, wp, c[i], c[(i + 1) % 4]) for i in range(4)]
    for i in range(4):
        S.constraint(POINTS_COINCIDENT, g, wp, ptA=L[i][2], ptB=L[(i + 1) % 4][1])
    S.constraint(HORIZONTAL, g, wp, entityA=L[0][0])
    S.constraint(VERTICAL, g, wp, entityA=L[1][0])
    S.constraint(VERTICAL, g, wp, entityA=L[3][0])
    S.constraint(PT_PT_DISTANCE, g, wp, valA=2 * hy, ptA=L[0][1], ptB=L[0][2],
                 disp=(0.0, vb - 6.0, 0.0))
    S.constraint(PT_PT_DISTANCE, g, wp, valA=depth, ptA=L[3][1], ptB=L[3][2],
                 disp=(-hy - 6.0, 0.0, 0.0))
    # The roof: through the lip-top datum, at the seam angle.  AT_MIDPOINT is
    # what centres this profile in u -- so the bottom edge gets a plain
    # HORIZONTAL above and NOT a SYMMETRIC_HORIZ, which would centre it a
    # second time and leave the group one redundant and one short.
    S.constraint(AT_MIDPOINT, g, wp, ptA=S.workplane_origin(g), entityA=L[2][0])
    # other=True negates the roof's direction vector before the dot product:
    # L[2] runs right-to-left and L[0] left-to-right, so without it the
    # constraint asks for 180 - theta and the group never reaches a solution.
    S.constraint(ANGLE, g, wp, valA=P.SEAM_ANGLE, entityA=L[2][0], entityB=L[0][0],
                 other=True, disp=(0.0, 6.0, 0.0))
    S.extrude("groove-cut", g, (P.GROOVE_HX, 0.0, 0.0), combine=DIFFERENCE,
              subtype=TWO_SIDED, visible=visible)


# --------------------------------------------------------------------------
# the bottom part
# --------------------------------------------------------------------------
def build_bottom():
    S = Sketch()
    pt_floor, pt_seam, pt_lip = datums(S, [(0.0, 0.0, P.FLOOR_T),
                                           (0.0, 0.0, P.Z_SEAM),
                                           (0.0, 0.0, P.Z_LIP)])

    tall = P.Z_LIP + P.EXT_HY * P.SEAM_TAN + P.OVER     # clears the highest seam point

    # 1. the exterior block
    g, wp = S.workplane_group("outer-profile", ENT_ORIGIN, XY_U, XY_V,
                              visible=False)
    rounded_rect(S, g, wp, P.EXT_HX, P.EXT_HY, P.EXT_CORNER_R)
    S.extrude("outer-block", g, (0.0, 0.0, tall / 2.0), combine=UNION,
              visible=False)

    # 2. slice the whole block off along the seam
    seam_cover(S, "seam-cut", pt_seam, P.Z_SEAM, 0.0, tall, up=True)

    # 3. put the lip's footprint back as a solid block; step 5's cavity cut is
    #    what turns it into a ring
    g, wp = S.workplane_group("lip-profile", ENT_ORIGIN, XY_U, XY_V,
                              visible=False)
    rounded_rect(S, g, wp, P.LIP_HX, P.LIP_HY, P.LIP_CORNER_R)
    S.extrude("lip-block", g, (0.0, 0.0, tall / 2.0), combine=UNION,
              visible=False)

    # 4. trim the lip to height
    seam_cover(S, "lip-top-cut", pt_lip, P.Z_LIP, 0.0, tall, up=True)

    # 5. and the card cavity last -- the dimension that has to be right, and
    #    what turns step 3's block into a ring.  It goes last because the group
    #    the file opens on is the one whose geometry you see, and the cavity
    #    profile is the size of the part rather than the size of a cutter.
    g, wp = S.workplane_group("cavity-profile", pt_floor, XY_U, XY_V,
                              visible=False)
    rect(S, g, wp, P.INT_HX, P.INT_HY)
    S.extrude("cavity-cut", g, (0.0, 0.0, (tall - P.FLOOR_T + P.OVER) / 2.0),
              combine=DIFFERENCE, visible=True)
    return S


# --------------------------------------------------------------------------
# the top part
# --------------------------------------------------------------------------
def build_top():
    S = Sketch()
    pt_seam, pt_lip, pt_ceil, pt_top = datums(S, [(0.0, 0.0, P.Z_SEAM),
                                                  (0.0, 0.0, P.Z_LIP),
                                                  (0.0, 0.0, P.Z_CEIL),
                                                  (0.0, 0.0, P.H_TOTAL)])

    # 1. the exterior block, sketched on the exterior top face and pushed DOWN
    #    past the seam.  That way the one plane of this block that survives to
    #    be a finished surface is the datum-dimensioned one, and the length of
    #    the extrude is just "far enough".
    g, wp = S.workplane_group("outer-profile", pt_top, XY_U, XY_V,
                              visible=False)
    rounded_rect(S, g, wp, P.EXT_HX, P.EXT_HY, P.EXT_CORNER_R)
    S.extrude("outer-block", g, (0.0, 0.0, -(P.H_TOTAL + P.OVER) / 2.0),
              combine=UNION, visible=False)

    # 2. open the bottom along the seam
    seam_cover(S, "seam-cut", pt_seam, P.Z_SEAM, -P.OVER, P.H_TOTAL, up=False)

    # 3. the card cavity, down from the ceiling and out through the open bottom
    g, wp = S.workplane_group("cavity-profile", pt_ceil, XY_U, XY_V,
                              visible=False)
    rect(S, g, wp, P.INT_HX, P.INT_HY)
    S.extrude("cavity-cut", g, (0.0, 0.0, -(P.Z_CEIL + P.OVER) / 2.0),
              combine=DIFFERENCE, visible=False)

    # 4. the groove the bottom's lip slides into
    groove_cutter(S, pt_lip, P.GROOVE_HY, P.LIP_H + P.OVER, visible=True)
    return S


# --------------------------------------------------------------------------
def main():
    out = os.path.normpath(os.path.join(HERE, ".."))
    jobs = [("ultra_guard_pro_100_bottom.slvs", build_bottom),
            ("ultra_guard_pro_100_top.slvs", build_top)]
    for name, fn in jobs:
        path = os.path.join(out, name)
        fn().write(path)
        print("wrote %s" % path)


if __name__ == "__main__":
    main()
