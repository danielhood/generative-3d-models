"""Cut a mesh with an axis-aligned plane and get the outline.

    from mesh_section import section, loops, plot

    loops(tris, 0, 41.5)               # outlines of the slice x = 41.5, as (y, z) loops
    python3 mesh_section.py part.stl --plane x=41.5            # print them
    python3 mesh_section.py a.stl b.stl --plane y=-31.74 --win -38 -33 31 39 -o out.png

A section answers questions a render or a pile of statistics cannot: what is the
profile of this groove, how thick is that wall at this height, does one part nest
inside the other.  It is also what turns an unexplained number into a picture --
a 0.73 mm "overlap" between two parts was a thin sliver, and only a section said
so.  `plot` overlays several meshes' sections in one PNG for exactly that.

The plane is x, y or z = a value.  The loop coordinates are the OTHER two axes in
ascending order: slicing x gives (y, z) points; slicing y gives (x, z); slicing z
gives (x, y).  Keep that in mind when reading numbers off a result.

Things that will bite you:

  * A vertex lying EXACTLY on the cutting plane produces degenerate segments, and
    a plane through a flat face (z = the floor's height) cuts that whole face
    into slivers.  Slice at a value a hair off a face.  A zero-area 2-point
    "loop" in the output is this; `loops` drops them (`min_points`).
  * `simplify` drops collinear points.  It is lossless to `tol`, but a curve
    sampled finely enough to look straight to `tol` will come back as a polygon.
    Raise `tol` to see only the corners of a profile, lower it to see a fillet.
  * Section loops are only as good as the mesh: a non-manifold mesh gives loops
    that do not close.  Run `mesh_check.py` first.

`plot` needs Pillow; nothing else in this file does.
"""
import math
import os


def section(tris, axis, value, eps=1e-9):
    """Segments where the plane axis=value cuts the mesh: [((u,v),(u,v)), ...]
    in the other two axes, ascending."""
    other = [i for i in range(3) if i != axis]
    segs = []
    for tri in tris:
        d = [v[axis] - value for v in tri]
        pts = []
        for i in range(3):
            j = (i + 1) % 3
            if abs(d[i]) < eps:
                pts.append(tuple(tri[i][k] for k in other))
            if (d[i] > eps and d[j] < -eps) or (d[i] < -eps and d[j] > eps):
                t = d[i] / (d[i] - d[j])
                pts.append(tuple(tri[i][k] + t * (tri[j][k] - tri[i][k]) for k in other))
        uniq = []
        for p in pts:
            if not any(abs(p[0] - q[0]) < eps and abs(p[1] - q[1]) < eps for q in uniq):
                uniq.append(p)
        if len(uniq) == 2:
            segs.append((uniq[0], uniq[1]))
    return segs


def chain(segs, tol=1e-6):
    """Join segments end to end into polylines (closed ones repeat their first
    point at the end)."""
    segs = list(segs)
    out = []
    while segs:
        a, b = segs.pop()
        loop = [a, b]
        changed = True
        while changed:
            changed = False
            for i, (p, q) in enumerate(segs):
                e, s = loop[-1], loop[0]
                if math.dist(p, e) < tol:
                    loop.append(q); segs.pop(i); changed = True; break
                if math.dist(q, e) < tol:
                    loop.append(p); segs.pop(i); changed = True; break
                if math.dist(p, s) < tol:
                    loop.insert(0, q); segs.pop(i); changed = True; break
                if math.dist(q, s) < tol:
                    loop.insert(0, p); segs.pop(i); changed = True; break
        out.append(loop)
    return out


def simplify(loop, tol=1e-3):
    """Drop points collinear with their neighbours (sine of the turning angle
    below `tol`).  Keeps a closed loop closed."""
    if len(loop) < 3:
        return loop
    closed = math.dist(loop[0], loop[-1]) < 1e-6
    pts = loop[:-1] if closed else loop[:]
    n = len(pts)
    out = []
    for i in range(n):
        if not closed and (i == 0 or i == n - 1):
            out.append(pts[i])
            continue
        p0, p1, p2 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        ax, ay, bx, by = p1[0] - p0[0], p1[1] - p0[1], p2[0] - p1[0], p2[1] - p1[1]
        la, lb = math.hypot(ax, ay), math.hypot(bx, by)
        if la < 1e-12 or lb < 1e-12:
            continue
        if abs(ax * by - ay * bx) / (la * lb) > tol:
            out.append(p1)
    if closed and out:
        out.append(out[0])
    return out


def loops(tris, axis, value, tol=1e-3, min_points=3):
    """The outlines of the slice, simplified, as a list of point lists.  Loops
    with fewer than `min_points` points (degenerate slivers) are dropped."""
    result = []
    for loop in chain(section(tris, axis, value)):
        s = simplify(loop, tol)
        if len(s) >= min_points:
            result.append(s)
    return result


def plot(meshes, axis, value, window, out_path, scale=130, colours=None, labels=None):
    """Draw several meshes' sections over each other into a PNG.

    meshes   list of triangle lists, already in one frame
    window   (u0, u1, v0, v1): the region to draw, in the section's own (u, v)
             axes (see the module note on which those are)
    scale    pixels per mm
    Returns the image size.  Colours default to blue, orange, green, magenta.
    """
    from PIL import Image, ImageDraw
    colours = colours or [(90, 170, 255), (230, 150, 70), (120, 220, 130), (230, 110, 220)]
    u0, u1, v0, v1 = window
    w, h = int((u1 - u0) * scale), int((v1 - v0) * scale)
    im = Image.new("RGB", (w, h), (18, 18, 22))
    dr = ImageDraw.Draw(im)

    def px(p):
        return ((p[0] - u0) * scale, h - (p[1] - v0) * scale)

    for k, tris in enumerate(meshes):
        col = colours[k % len(colours)]
        for a, b in section(tris, axis, value):
            if (u0 - .1 <= a[0] <= u1 + .1 and v0 - .1 <= a[1] <= v1 + .1) or \
               (u0 - .1 <= b[0] <= u1 + .1 and v0 - .1 <= b[1] <= v1 + .1):
                dr.line([px(a), px(b)], fill=col, width=3)
    dr.text((8, 8), "section %s = %.4f" % ("xyz"[axis], value), fill=(200, 200, 200))
    for k, lab in enumerate(labels or []):               # a legend, in each mesh's own colour
        dr.text((8, 24 + 14 * k), os.path.basename(lab), fill=colours[k % len(colours)])
    dr.text((8, h - 18), "u %.2f..%.2f  v %.2f..%.2f  (%d px/mm)" % (u0, u1, v0, v1, scale),
            fill=(150, 150, 150))
    im.save(out_path)
    return im.size


if __name__ == "__main__":
    import argparse
    from stl_io import load_stl
    ap = argparse.ArgumentParser(
        description="Section one or more STLs with an axis-aligned plane and print "
                    "the outlines, or overlay them in a PNG.")
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--plane", required=True, metavar="AXIS=VALUE", help="e.g. y=-31.74")
    ap.add_argument("--tol", type=float, default=1e-3, help="simplify tolerance")
    ap.add_argument("--win", nargs=4, type=float, metavar=("U0", "U1", "V0", "V1"),
                    help="plot window, in the section's own (u, v) axes")
    ap.add_argument("-o", "--out", help="write a PNG overlaying all the STLs (needs --win)")
    a = ap.parse_args()
    ax_name, val = a.plane.split("=")
    axis, value = "xyz".index(ax_name), float(val)
    meshes = [load_stl(f) for f in a.stl]
    if a.out:
        if not a.win:
            ap.error("--out needs --win U0 U1 V0 V1")
        print("wrote", a.out, plot(meshes, axis, value, a.win, a.out, labels=a.stl))
    labels = [c for c in "xyz" if c != ax_name]
    for f, t in zip(a.stl, meshes):
        for n, loop in enumerate(loops(t, axis, value, a.tol)):
            print("\n%s  loop %d: %d points  [%s, %s]" % (f, n, len(loop), *labels))
            for p in loop:
                print("  %10.4f %10.4f" % p)
