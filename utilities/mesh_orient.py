"""Get a flat plate-like mesh into the XY plane, and find its faces.

    from mesh_orient import plate_axis, face_planes, load_oriented

    axis, lo, hi = plate_axis(tris)        # which axis is the thickness?
    planes       = face_planes(tris, axis) # where are the flat faces?
    flat         = load_oriented("insert.stl")   # faces now lie in XY

Source inserts in this repo do not arrive lying in XY. `Insert-tree.stl`,
for instance, is a 107.2 x 107.2 x 2.5 mm plate lying in XZ with its
thickness along Y and its centre at native y = 59.25, z = 60. Everything
downstream -- `mesh_slice.flat_triangles_at_z`, `mesh_rasterize`,
`mesh_query.is_solid_at`, `projection()` -- wants the face plane to be XY,
so something has to do this reorientation, and doing it ad hoc each time is
how sign errors get in.

READ THIS BEFORE TRUSTING THE RESULT
------------------------------------
Reorienting a plate is exactly where orientation bugs come from, and this
module cannot check your work for you. Two separate things can go wrong and
only one of them is obvious:

  * WHICH WAY IS UP. Swapping the thickness axis into Z leaves a choice of
    sign for the remaining in-plane axis, and the two choices differ by a
    vertical flip. OpenSCAD's `rotate([90,0,0])` maps (x,y,z) -> (x,-z,y);
    this module's `orient_to_xy(tris, axis=1)` maps (x,y,z) -> (x,z,y).
    Those are NOT the same view -- they are upside down relative to each
    other. That difference stood a Tree of Life on its head for most of a
    build (coasters/coaster_tree_of_life_spec.md section 6, D6a).

  * WHICH FACE YOU ARE LOOKING FROM. A through-cut plate seen from +Y and
    from -Y are mirror images. On a left-right symmetric design this is
    invisible, so it will not announce itself.

Nothing measurable distinguishes any of these: area, radius, component
count and width distributions are all identical under a mirror and all
agree with each other. **Settle it by measurement against the source, with
`pattern_trace.orientation_iou()`**, which scores all four variants for you.
Do not settle it by eye on a near-symmetric design.

Stdlib only.
"""
from collections import Counter

from stl_io import load_stl


def bbox(tris):
    xs = [v[0] for t in tris for v in t]
    ys = [v[1] for t in tris for v in t]
    zs = [v[2] for t in tris for v in t]
    return [(min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))]


def plate_axis(tris):
    """(axis, lo, hi) for the thinnest bounding-box dimension -- i.e. the
    plate's thickness direction. axis is 0/1/2 for X/Y/Z."""
    bb = bbox(tris)
    axis = min(range(3), key=lambda i: bb[i][1] - bb[i][0])
    return axis, bb[axis][0], bb[axis][1]


def face_planes(tris, axis, tol=1e-6, min_tris=1):
    """Where the flat faces sit along `axis`, most populated first.

    Returns [(coordinate, triangle_count), ...]. For a through-cut plate the
    top two entries are the two faces and carry almost every triangle; small
    trailing entries are blind pockets or engraved detail that does not go
    all the way through -- worth noticing, because a blind feature shows up
    on a face raster but NOT in a `projection()` shadow, and that
    discrepancy is otherwise confusing. (Insert-tree.stl has four such
    corner pockets.)"""
    counts = Counter()
    for t in tris:
        a, b, c = t
        if abs(a[axis] - b[axis]) < tol and abs(b[axis] - c[axis]) < tol:
            counts[round(a[axis], 6)] += 1
    return [(k, n) for k, n in counts.most_common() if n >= min_tris]


def orient_to_xy(tris, axis, center=True, flip_u=False, flip_v=False):
    """Remap so `axis` becomes Z and the face plane becomes XY.

    axis=0: (x,y,z) -> (y,z,x)
    axis=1: (x,y,z) -> (x,z,y)
    axis=2: unchanged

    `center` subtracts the in-plane bounding-box centre, so the part sits on
    the origin. Z is left alone, so the returned face heights are still the
    source's own coordinates and can be fed straight to
    `flat_triangles_at_z` using a value from `face_planes`.

    `flip_u` / `flip_v` negate the in-plane axes. These exist because the
    correct combination is not derivable here -- see the module docstring --
    and must be chosen by measurement."""
    def remap(v):
        if axis == 0:
            return [v[1], v[2], v[0]]
        if axis == 1:
            return [v[0], v[2], v[1]]
        return [v[0], v[1], v[2]]

    out = [[remap(v) for v in t] for t in tris]
    if center:
        us = [v[0] for t in out for v in t]
        vs = [v[1] for t in out for v in t]
        cu = (min(us) + max(us)) / 2.0
        cv = (min(vs) + max(vs)) / 2.0
        for t in out:
            for v in t:
                v[0] -= cu
                v[1] -= cv
    if flip_u or flip_v:
        for t in out:
            for v in t:
                if flip_u:
                    v[0] = -v[0]
                if flip_v:
                    v[1] = -v[1]
    return [tuple(tuple(v) for v in t) for t in out]


def load_oriented(path, axis=None, center=True, flip_u=False, flip_v=False):
    """load_stl + plate_axis + orient_to_xy in one call."""
    tris = load_stl(path)
    if axis is None:
        axis = plate_axis(tris)[0]
    return orient_to_xy(tris, axis, center=center, flip_u=flip_u, flip_v=flip_v)


if __name__ == "__main__":
    import sys

    tris = load_stl(sys.argv[1])
    bb = bbox(tris)
    axis, lo, hi = plate_axis(tris)
    print("bbox        x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f"
          % (bb[0][0], bb[0][1], bb[1][0], bb[1][1], bb[2][0], bb[2][1]))
    print("plate axis  %s  (thickness %.3f mm, %.3f .. %.3f)"
          % ("XYZ"[axis], hi - lo, lo, hi))
    print("flat faces along that axis (coordinate, triangles):")
    for k, n in face_planes(tris, axis)[:8]:
        print("   %10.4f  %6d %s" % (k, n, "" if n > 100 else "<- small: blind pocket, not a through feature?"))
