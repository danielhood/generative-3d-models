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

source_file = "path/to/source.stl";

projection(cut = false)
    rotate([90, 0, 0])   // adjust to your part's own orientation
        import(source_file);
