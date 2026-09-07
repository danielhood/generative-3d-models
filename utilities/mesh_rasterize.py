"""Rasterize a flat Z-slice of a mesh (e.g. the top face of a
`linear_extrude()`d part) straight to a PNG, by filling its actual
triangles -- no OpenSCAD, no renderer, no camera/projection math to get
subtly wrong. This is the ground-truth visual check: when a render, a
preview, or a piece of derived math disagrees with what a part is "supposed"
to look like, rasterize the real exported mesh and look at that.

Requires Pillow (`pip install Pillow`) -- the one utility here with a
dependency; everything else in this folder is stdlib-only.

Usage:
    python3 mesh_rasterize.py part.stl out.png [z] [px_per_mm]

    from mesh_rasterize import rasterize_z_slice
    from stl_io import load_stl
    im = rasterize_z_slice(load_stl("coaster.stl"), z=3.0)
    im.save("check.png")

Background provided by coasters/coaster_helm_of_awe_spec.md section 6 (C4):
this exact technique is what finally settled a dispute between a hand-rolled
"proof" (wrong) and a direct report from opening the file in OrcaSlicer and
FreeCAD (right) about whether a pattern was solid or hollow in the final
part. Prefer this over trying to reason your way to an answer.
"""
from mesh_slice import flat_triangles_at_z


def rasterize_z_slice(tris, z, px_per_mm=9.0, size=1000, fill=(0, 140, 90), background=(255, 255, 255)):
    """Returns a PIL Image: the flat slice at height z, filled solid,
    centered in the image at the given scale. Increase `size`/`px_per_mm`
    together to keep the part centered and fully in frame for larger parts."""
    from PIL import Image, ImageDraw

    flat = flat_triangles_at_z(tris, z)
    im = Image.new("RGB", (size, size), background)
    draw = ImageDraw.Draw(im)

    def to_px(pt):
        x, y = pt
        return (size / 2 + x * px_per_mm, size / 2 - y * px_per_mm)

    for a, b, c in flat:
        draw.polygon([to_px(a), to_px(b), to_px(c)], fill=fill)
    return im


if __name__ == "__main__":
    import sys

    from stl_io import load_stl

    path, out = sys.argv[1], sys.argv[2]
    z = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    px_per_mm = float(sys.argv[4]) if len(sys.argv) > 4 else 9.0
    im = rasterize_z_slice(load_stl(path), z=z, px_per_mm=px_per_mm)
    im.save(out)
    print(f"saved {out}")
