// Recipe referenced by dxf_trace.py: flatten a relief/engraving on an STL
// to an exact 2D outline, exportable to DXF, even when the source mesh is
// non-manifold (has a crack/self-touching vertex that would make a 3D
// boolean against it unreliable -- see dxf_trace.py's module docstring and
// coasters/coaster_helm_of_awe_spec.md section 6, C1).
//
// Usage:
//   1. Edit source_file and the rotate() below to suit your part's own
//      axes (the goal is: whichever plane the relief's face lies in should
//      become the XY plane here, since projection() always projects onto
//      XY).
//   2. Render to DXF:
//        openscad --render -o out.dxf projection_trace_recipe.scad
//   3. Feed out.dxf to dxf_trace.parse_dxf_lines().
//
// CHECK THE ORIENTATION BEFORE YOU BUILD ANYTHING ON THE RESULT.
// rotate([90,0,0]) maps (x,y,z) -> (x,-z,y), so what lands in XY is
// (x, -z): vertically MIRRORED relative to the part as drawn. Whether
// that matters depends on your part, and it is easy to miss, because
// nothing measurable changes under a mirror -- areas, radii, component
// counts and width distributions all come out identical and all agree
// with each other. On coasters/Insert-tree.stl this stood a Tree of Life
// on its head and survived several rounds of measurement before anyone
// rendered the assembled part and looked at it (that spec, section 6, D6a).
// It is the third orientation bug in three coasters here.
//
// Cheap objective check -- rasterize the emitted polygons against the
// source mesh's own face and score the overlap, rather than eyeballing a
// near-symmetric design:
//
//     IoU(traced_polys, source_cut_region)      -> 0.94  correct
//     IoU(mirrored, source_cut_region)          -> 0.28  wrong
//
// Fix it here in the recipe (add mirror([0,1,0]) ahead of projection())
// rather than flipping signs in the extraction script, so there is no
// hidden convention downstream.

source_file = "path/to/source.stl";

projection(cut = false)
    rotate([90, 0, 0])   // adjust to your part's own orientation
        import(source_file);
