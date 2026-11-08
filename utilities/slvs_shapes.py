"""Sketch shapes that are fully constrained, ready to extrude or lathe.

    from slvs_write import Sketch
    from slvs_shapes import rect, rounded_rect, datums, spherical_cap

Every shape here is built to the standard that cost a failed file to learn:
**0 degrees of freedom and 0 redundant equations**, checked by
`slvs_write.dof_report` and by SolveSpace's GUI.  A sketch that merely LOOKS right
passes every mesh check and still opens with "unsolvable constraints", because
the seeded coordinates hide a rank-deficient system.  So these are not sketches
with a few dimensions added; each constraint is there for a reason, and the
reasons are the useful part:

  * `rect(dim=True)` centres the rectangle on its workplane origin with the two
    SYMMETRIC constraints and therefore must NOT also say HORIZONTAL/VERTICAL on
    the edges they govern: symmetry implies it, and saying it twice is a
    redundant equation (the GUI deletes the redundant one for you; a generated
    file has to not add it).  It is 16 unknowns, 16 equations, 0 DOF.
    `dim=False` says HORIZONTAL/VERTICAL on all four edges and gives no
    dimensions: 16 unknowns, 12 equations, 4 DOF (position and size free), for a
    caller that places and sizes it some other way.  A cutter "whose size does not
    matter" is NOT an excuse for dim=False: those groups reported 4 DOF each
    from `dof_report`.  Prefer dim=True and an oversize dimension.
  * SYMMETRIC_HORIZ is symmetry about the VERTICAL axis (same v, opposite u),
    the constraint for a HORIZONTAL edge's two ends.  It reads backwards.
  * ANGLE constrains the direction cosine of two line vectors, so two edges that
    run opposite ways need `other=True`.

All of these draw in the workplane `wp` of sketch group `g`, in the sketch's own
(u, v) axes; the helpers do not know or care where in the world that is.
"""
from slvs_write import (POINTS_COINCIDENT, HORIZONTAL, VERTICAL, PT_PT_DISTANCE,
                        SYMMETRIC_HORIZ, SYMMETRIC_VERT, EQUAL_RADIUS, DIAMETER,
                        ARC_LINE_TANGENT, PT_PLANE_DISTANCE,
                        ENT_YZ_WORKPLANE, ENT_ZX_WORKPLANE)


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


def rect_at(S, g, wp, cx, cy, hx, hy, origin=(0.0, 0.0)):
    """A closed rectangle centred at WORLD (cx, cy), half-sizes hx and hy, in a
    horizontal workplane (u = +x, v = +y) whose origin is at world `origin`.

    `rect` can only be centred on its workplane's origin; this is for the second
    and third bars of a set (a divider, a rib) that sit elsewhere.  Fully
    constrained, 16 unknowns against 16 equations: 4 coincidences, all four
    edges horizontal or vertical, width and height, and the bottom-left corner
    placed in x and y against the reference planes.  Pinning against the world
    planes (not the workplane origin) is what lets two bars share one sketch
    group without constraints between them: they are independent.

    Rectangles in one sketch must not overlap (an extrude wants disjoint closed
    loops).  Dividers that cross go in separate groups and are unioned.
    """
    ox, oy = origin
    c = [(cx - hx - ox, cy - hy - oy), (cx + hx - ox, cy - hy - oy),
         (cx + hx - ox, cy + hy - oy), (cx - hx - ox, cy + hy - oy)]
    L = [S.line(g, wp, c[i], c[(i + 1) % 4]) for i in range(4)]
    for i in range(4):
        S.constraint(POINTS_COINCIDENT, g, wp, ptA=L[i][2], ptB=L[(i + 1) % 4][1])
    S.constraint(HORIZONTAL, g, wp, entityA=L[0][0])
    S.constraint(HORIZONTAL, g, wp, entityA=L[2][0])
    S.constraint(VERTICAL, g, wp, entityA=L[1][0])
    S.constraint(VERTICAL, g, wp, entityA=L[3][0])
    S.constraint(PT_PT_DISTANCE, g, wp, valA=2 * hx, ptA=L[0][1], ptB=L[0][2],
                 disp=(0.0, -hy - 3.0, 0.0))
    S.constraint(PT_PT_DISTANCE, g, wp, valA=2 * hy, ptA=L[1][1], ptB=L[1][2],
                 disp=(hx + 3.0, 0.0, 0.0))
    S.constraint(PT_PLANE_DISTANCE, g, valA=cx - hx, ptA=L[0][1],
                 entityA=ENT_YZ_WORKPLANE)
    S.constraint(PT_PLANE_DISTANCE, g, valA=cy - hy, ptA=L[0][1],
                 entityA=ENT_ZX_WORKPLANE)
    return L


def corner_wedge(S, g, wp, corner, along_wall, along_face, ch, over, pin):
    """One 45 deg chamfer, drawn in the plane perpendicular to the edge it cuts.

    `corner` is where the groove wall meets the seam face; `along_wall` and
    `along_face` are unit directions leading away from it, up the wall and
    outboard across the seam face.  The chamfer itself is the line between the
    two points `ch` along each.

    The triangle actually drawn is that one pushed `over` mm back along both
    directions, which leaves its hypotenuse on exactly the same line (the two
    offsets cancel) while moving its two legs out of the part and into open
    space.  Without that, the legs would sit exactly on the groove wall and on
    the seam face, and a cutter face coincident with a face of the part is the
    boolean's least favourite thing.

    `pin` fixes a sketch point with two dimensions; three pinned vertices plus
    three coincidences is 12 equations for the triangle's 12 params.
    """
    def pt(a, b):
        return (corner[0] - over * (along_wall[0] + along_face[0]) +
                a * along_wall[0] + b * along_face[0],
                corner[1] - over * (along_wall[1] + along_face[1]) +
                a * along_wall[1] + b * along_face[1])
    leg = ch + 2 * over
    tri = [pt(0.0, 0.0), pt(leg, 0.0), pt(0.0, leg)]
    L = [S.line(g, wp, tri[i], tri[(i + 1) % 3]) for i in range(3)]
    for i in range(3):
        S.constraint(POINTS_COINCIDENT, g, wp, ptA=L[i][2], ptB=L[(i + 1) % 3][1])
    for i in range(3):
        pin(g, wp, L[i][1], tri[i])


def spherical_cap(S, tag, datum_pt, face, sg, across, height, sphere_r, combine,
                  visible=False, along="x"):
    """A spherical cap standing on (UNION) or cut into (DIFFERENCE) a vertical face:
    a snap dome or a dimple.

    face      where the face is along the cap's axis, SIGNED (x = -36.85 for the
              left lip face, y = +40.4 for the back one)
    sg        the direction the APEX points, from the face, along `along`: -1 or
              +1.  For a dome that is the face's outward normal.  For a dimple it
              is the opposite: INTO the material.  Get this wrong and the sphere's
              hemisphere lands in the material instead of the void behind the
              face, and a dimple cuts twice its volume (4.43 mm^3 for a 2.29 cap).
    across    the cap's centre ALONG the face: y for an x-axis cap, x for a y-axis cap
    height    how far the apex stands off (or cuts into) the face
    sphere_r  the sphere's radius.  Cap height, base radius b and sphere radius
              R are tied by R = (b^2 + h^2) / (2h): fix any two.
    along     "x" (a cap on a face square to x) or "y" (square to y).  `datum_pt`
              is a datum point at the cap's centre on the face; the profile's
              horizontal sketch plane passes through its z.

    The cap is a revolved quarter-disc.  The profile is a closed triangle of three
    edges drawn in a horizontal plane through the cap's centre:

        C -- the centre of the sphere, on the axis, just INSIDE the face
        A -- the apex, on the axis, `height` outside the face
        E -- on the sphere's equator, R off the axis

    with an edge C-A that is the axis, an edge C-E square to it, and an arc E..A
    of the sphere.  Revolving that about C-A gives the cap PLUS the hemisphere
    behind it, which sits in solid material (a dome) or in empty space (a
    dimple).  A cap cut off exactly at the face would leave a boolean face
    COINCIDENT with the part's, and coincident faces are what these booleans
    handle worst.  An extrude cannot make a cap at all: its end faces are flat.

    For a y-axis cap the sketch's u axis is +y and its v axis is -x, which keeps
    (u, v, normal) right-handed with the normal +z; the sphere is symmetric about
    the axis so which side E falls on is immaterial.

    Fully constrained: 7 points (14 unknowns) against 4 coincidences, the axis
    horizontal, the square edge vertical, one radius dimension, two placement
    dimensions and the arc's own equal-radius equation.  The one placed point is
    the sphere's centre.
    """
    if along == "x":
        u, v = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
        along_plane, across_plane = ENT_YZ_WORKPLANE, ENT_ZX_WORKPLANE
    elif along == "y":
        u, v = (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0)
        along_plane, across_plane = ENT_ZX_WORKPLANE, ENT_YZ_WORKPLANE
    else:
        raise ValueError("along must be 'x' or 'y', not %r" % (along,))
    R = sphere_r
    cin = R - height                                  # centre, inside the face
    g, wp = S.workplane_group(tag + "-profile", datum_pt, u, v, visible=False)
    C = (-sg * cin, 0.0)                              # relative to the face point
    A = (sg * height, 0.0)
    E = (-sg * cin, R)
    axis = S.line(g, wp, C, A)
    side = S.line(g, wp, C, E)
    # the arc runs counter-clockwise: E -> A on a negative face (90 -> 180 degrees
    # about C), A -> E on a positive one (0 -> 90)
    arc = S.arc(g, wp, C, E, A) if sg < 0 else S.arc(g, wp, C, A, E)
    a_start, a_end = (arc[2], arc[3])
    S.constraint(POINTS_COINCIDENT, g, wp, ptA=axis[1], ptB=side[1])
    S.constraint(POINTS_COINCIDENT, g, wp, ptA=arc[1], ptB=axis[1])
    S.constraint(POINTS_COINCIDENT, g, wp, ptA=(a_end if sg < 0 else a_start),
                 ptB=axis[2])
    S.constraint(POINTS_COINCIDENT, g, wp, ptA=(a_start if sg < 0 else a_end),
                 ptB=side[2])
    S.constraint(HORIZONTAL, g, wp, entityA=axis[0])
    S.constraint(VERTICAL, g, wp, entityA=side[0])
    S.constraint(PT_PT_DISTANCE, g, wp, valA=R, ptA=side[1], ptB=side[2],
                 disp=(-3.0 * sg, R / 2.0, 0.0))
    # the sphere's centre is the one point that is placed, against the reference
    # planes (the sketch plane itself is z = the datum's z)
    S.constraint(PT_PLANE_DISTANCE, g, valA=face - sg * cin,
                 ptA=axis[1], entityA=along_plane)
    S.constraint(PT_PLANE_DISTANCE, g, valA=across, ptA=axis[1],
                 entityA=across_plane)
    return S.lathe(tag, g, axis[0], axis[1], combine=combine, visible=visible)
