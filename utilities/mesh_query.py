""""Is there material at this (x, y)?" -- the "isSolid" test.

    from mesh_query import is_solid_at
    from stl_io import load_stl
    tris = load_stl("coaster.stl")
    is_solid_at(tris, x=19.16, y=39.05, z=3.0)   # True/False

Scope: flat-extruded parts only (checks the flat face at height `z`, e.g.
the top of a `linear_extrude()`). It will not tell you anything about a
sloped/curved surface at that height -- for that you'd need a full 3D
point-in-mesh ray cast, which is NOT implemented here (see note below).

Why this exists, and a warning about trusting it blindly
----------------------------------------------------------
This tool exists because of a real, costly mistake (full story:
coasters/coaster_helm_of_awe_spec.md section 6, C4). The first version of
this idea was a hand-rolled point-in-*polygon* test, run against the
*source* 2D polygon data (the traced artwork) rather than the *actual
exported mesh*, to "prove" which parts of a design were solid vs. hollow.
That test had a bug -- picked a point that was nowhere near where it was
assumed to be -- and the resulting "proof" flatly contradicted the correct
answer (which two other people confirmed just by opening the STL in a
slicer). A lot of time went into chasing a phantom OpenSCAD bug before the
actual bug (in the verification code itself) was found.

The fix was to stop reasoning about source polygons and query the *real,
final, exported mesh* instead -- which is what this function does: it reads
the actual triangles at the actual height you're asking about, and tests
literal point-in-triangle containment. There is no synthetic "is this point
supposed to be inside the polygon" step to get subtly wrong.

Lesson for future use: if this function's answer ever conflicts with what a
render/preview seems to show, trust this function (or a slicer/CAD viewer
opening the real file) over the render. If its answer conflicts with a
*different* piece of derived reasoning (e.g. an area calculation, a
hand-traced polygon check), suspect the *other* reasoning first -- rederive
it against the real mesh rather than assuming this function is wrong.

Extending to full 3D (not implemented)
---------------------------------------
A general "is this (x,y,z) point inside the solid, at any height, including
sloped surfaces" test is possible via a vertical ray-cast that counts
crossings through *all* triangles (not just a flat slice) and checks for an
odd count -- the standard even-odd solid-point test. It is not implemented
here because it hasn't been needed or verified yet on a real part in this
repo; if you build it, verify it the same way this file was eventually
fixed (against a real slicer/viewer's rendering of a real mesh), not just
against your own math.
"""
from mesh_slice import flat_triangles_at_z, point_in_triangle


def is_solid_at(tris, x, y, z, tol=1e-6):
    """True if any triangle in the flat slice at height z covers (x, y)."""
    for a, b, c in flat_triangles_at_z(tris, z, tol=tol):
        if point_in_triangle((x, y), a, b, c):
            return True
    return False


if __name__ == "__main__":
    import sys

    from stl_io import load_stl

    path, x, y, z = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    tris = load_stl(path)
    print(is_solid_at(tris, x, y, z))
