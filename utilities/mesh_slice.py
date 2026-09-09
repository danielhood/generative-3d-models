"""Shared helpers for working with a flat Z-slice of a triangle mesh --
typically the top or bottom face of a `linear_extrude()`d part. Used by
mesh_query.py (point lookup) and mesh_rasterize.py (visual ground truth).

Both of those exist because of one hard lesson (see
coasters/coaster_helm_of_awe_spec.md section 6, C4). That entry originally
concluded that `linear_extrude()` of a multi-contour 2D `difference()` does
not follow literal set-subtraction semantics. That conclusion was WRONG and
has since been retracted -- there is no such quirk; the traced polygons
being subtracted were the artwork's negative space, mislabeled as the
artwork (full account: coasters/coaster_yggdrasil_spec.md section 6, F1).
Booleans behave as documented.

What survives, and why these tools are still worth reaching for: don't trust
a mental model of "what the boolean should produce," and don't trust
OpenSCAD's own preview either (a separate, earlier lesson -- pole-foot's
C10). The only source of truth is the actual exported mesh. These two tools
query and visualize that directly, with no OpenSCAD or rendering pipeline in
between -- and note that the same tools work just as well pointed at a
*source* mesh, which is what would have caught the mislabeling immediately.
"""


def flat_triangles_at_z(tris, z, tol=1e-6):
    """Triangles from `tris` (as loaded by stl_io.load_stl) whose all three
    vertices sit at height `z` -- i.e. a flat face of an extrusion, not a
    sloped/side wall. Returns them as 2D triangles (x, y) tuples, dropping Z."""
    out = []
    for a, b, c in tris:
        if abs(a[2] - z) < tol and abs(b[2] - z) < tol and abs(c[2] - z) < tol:
            out.append(((a[0], a[1]), (b[0], b[1]), (c[0], c[1])))
    return out


def point_in_triangle(p, a, b, c):
    """True if 2D point p is inside (or on the edge of) triangle a,b,c.
    Winding-independent (works whether the triangle is CW or CCW)."""

    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    d1 = sign(p, a, b)
    d2 = sign(p, b, c)
    d3 = sign(p, c, a)
    has_neg = d1 < 0 or d2 < 0 or d3 < 0
    has_pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (has_neg and has_pos)
