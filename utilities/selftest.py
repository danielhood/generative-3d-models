#!/usr/bin/env python3
"""Do the mesh_* and slvs_* tools in this folder actually work?

    python3 selftest.py            # all of it
    python3 selftest.py --quick    # only the pure-Python mesh tests (no SolveSpace)

Every check in this repo has, at some point, been wrong in a way that passed: a
ray cast that read an interference where there was none, a plane grouping that
shifted a measurement by 0.0002 mm, a "sound" file that SolveSpace's GUI called
unsolvable, a check that could not tell a missing feature from a present one
(its whole history is in `coasters/coaster_helm_of_awe_spec.md` C4 and
`mtg-deck-boxes/ultra_guard_pro_100_spec.md` 6.2, 6.7, 6.10).  The cure each time
was the same: run the tool on something whose answer is KNOWN, and, for a
checker, on something broken that it MUST reject.  This file does both.

Two kinds of test.

  * Known answers.  A box 10 x 20 x 30 has volume 6000, six faces of known area,
    and a column through it that is solid for exactly its height.  A block with a
    spherical cap of known height and radius lathed onto it must be found, at that
    height, by the feature finder, and its sphere fit must recover the radius.
  * Things that must FAIL.  A constraint pointed at a request instead of an
    entity (SolveSpace silently deletes it), a sketch left under-constrained
    (the mesh is fine and only a jitter test notices), and a top with a dome but
    no dimple (the engagement test must see the overlap).  A checker that has only
    ever said "fine" has not been shown to work.

Exit status 0 only if every test passed.  The SolveSpace tests are skipped, loudly,
if `solvespace-cli` is not on the PATH.
"""
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FAILED = []
PASSED = [0]


def check(name, ok, detail=""):
    if ok:
        PASSED[0] += 1
        print("  ok    %s" % name)
    else:
        FAILED.append(name)
        print("  FAIL  %s   %s" % (name, detail))


def close(a, b, tol=1e-6):
    return abs(a - b) <= tol


def box(x0, x1, y0, y1, z0, z1):
    """A closed box as 12 triangles with outward normals.  Each quad is flipped,
    if need be, to face away from the centre, so this does not rely on getting
    any winding right by hand."""
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    corners = lambda xs, ys, zs: [(x, y, z) for x in xs for y in ys for z in zs]
    faces = [  # four points around each face
        [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
        [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)],
        [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
    ]
    out = []
    for q in faces:
        for tri in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
            a, b, cc = tri
            n = ((b[1] - a[1]) * (cc[2] - a[2]) - (b[2] - a[2]) * (cc[1] - a[1]),
                 (b[2] - a[2]) * (cc[0] - a[0]) - (b[0] - a[0]) * (cc[2] - a[2]),
                 (b[0] - a[0]) * (cc[1] - a[1]) - (b[1] - a[1]) * (cc[0] - a[0]))
            mid = tuple(sum(p[i] for p in tri) / 3 - c[i] for i in range(3))
            if sum(n[i] * mid[i] for i in range(3)) < 0:
                tri = (a, cc, b)
            out.append(tri)
    return out


# ---------------------------------------------------------------------------
def pure_python_tests():
    from mesh_geom import (bbox, volume, shift, tri_normal_area, point_tri_distance,
                           SurfaceIndex, surface_samples)
    from mesh_rays import axis_spans, ray_spans, is_inside, overlap, max_overlap
    from mesh_section import section, loops
    from mesh_planes import group_planes, axis_planes, fit_plane, slope_degrees
    from mesh_compare import compare

    B = box(0, 10, 0, 20, 0, 30)
    print("\nmesh_geom")
    check("box volume is 6000", close(volume(B), 6000.0), volume(B))
    check("box bbox", bbox(B) == ((0, 0, 0), (10, 20, 30)), bbox(B))
    check("a mesh shifted by d has its bbox shifted by d",
          bbox(shift(B, (1, 2, 3))) == ((1, 2, 3), (11, 22, 33)))
    n, a = tri_normal_area(((0, 0, 0), (2, 0, 0), (0, 2, 0)))
    check("triangle normal and area", n == (0.0, 0.0, 1.0) and close(a, 2.0), (n, a))
    check("a degenerate triangle has no normal",
          tri_normal_area(((0, 0, 0), (1, 0, 0), (2, 0, 0)))[0] is None)
    T = ((0, 0, 0), (1, 0, 0), (0, 1, 0))
    check("distance above a face", close(point_tri_distance((.25, .25, 2), *T), 2.0))
    check("distance to a vertex", close(point_tri_distance((2, 0, 0), *T), 1.0))
    check("distance to an edge", close(point_tri_distance((.5, -1, 0), *T), 1.0))
    idx = SurfaceIndex(B)
    check("surface index: 3 above the top face", close(idx.nearest((5, 10, 33)), 3.0, 1e-9))
    check("surface index: centre is 5 from the nearest wall",
          close(idx.nearest((5, 10, 15), limit=10.0), 5.0, 1e-9))
    check("...and the default limit of 3.5 caps that answer (documented)",
          close(idx.nearest((5, 10, 15)), 3.5, 1e-9))
    check("surface index caps at `limit`", close(idx.nearest((5, 10, 90), limit=3.5), 3.5))
    check("a box yields 4 samples per triangle", len(list(surface_samples(B))) == 48)

    print("\nmesh_rays")
    for axis, ab, want in ((2, (5, 10), [(0, 30)]), (1, (5, 15), [(0, 20)]),
                           (0, (10, 15), [(0, 10)])):
        got = axis_spans(B, axis, *ab)
        check("axis_spans along %s through the box" % "xyz"[axis],
              len(got) == 1 and close(got[0][0], want[0][0]) and close(got[0][1], want[0][1]), got)
    check("a column that misses the box finds nothing", axis_spans(B, 2, 15, 10) == [])
    two = box(0, 10, 0, 10, 0, 10) + box(0, 10, 0, 10, 20, 30)
    got = axis_spans(two, 2, 5, 5)
    check("two stacked boxes give two spans",
          len(got) == 2 and close(got[0][1], 10) and close(got[1][0], 20), got)
    got = ray_spans(B, (-3, 5, 7), (2, 0, 0))
    check("ray_spans along an off-origin line", len(got) == 1 and close(got[0][0], 3) and close(got[0][1], 13), got)
    check("is_inside: inside / outside", is_inside(B, (5, 10, 15)) and not is_inside(B, (15, 10, 15)))
    A2, B2 = box(0, 10, 0, 20, 0, 30), box(5, 15, 0, 20, 0, 30)
    worst, where = max_overlap(A2, B2, [(10, 15), (3, 7)], axis=0)
    check("overlap of boxes sharing 5 mm in x is 5", close(worst, 5.0) and where is not None, (worst, where))
    check("boxes that only touch do not overlap",
          max_overlap(A2, box(10, 20, 0, 20, 0, 30), [(10, 15)], axis=0)[0] < 1e-6)

    print("\nmesh_section")
    lp = loops(B, 2, 15)
    area = 0.0
    if lp:
        p = lp[0]
        area = abs(sum(p[i][0] * p[i + 1][1] - p[i + 1][0] * p[i][1] for i in range(len(p) - 1))) / 2
    check("a z slice of the box is one rectangle of area 200",
          len(lp) == 1 and close(area, 200.0, 1e-6), (len(lp), area))
    check("slicing outside the part gives nothing", loops(B, 2, 99) == [])
    check("section returns (y, z) pairs when slicing x",
          all(len(s) == 2 and len(s[0]) == 2 for s in section(B, 0, 5)))

    print("\nmesh_planes")
    fs = group_planes(B, min_area=1.0)
    check("a box has six faces", len(fs) == 6, len(fs))
    check("its largest face is 600 (20 x 30)", close(fs[0]["area"], 600.0, 1e-6), fs[0]["area"])
    ap = axis_planes(B, min_area=1.0)
    check("faces square to x are at 0 (facing -x) and 10 (facing +x)",
          [(f["sign"], round(f["pos"], 6)) for f in ap["x"]] == [(-1, 0.0), (1, 10.0)], ap["x"])
    check("a reference normal keeps only that face",
          len(group_planes(B, ref=(0, 0, 1), min_area=1.0)) == 1)
    nrm, d = fit_plane([(x, y, 3.0 + 0.0 * x) for x in range(5) for y in range(5)])
    check("fit_plane recovers z = 3", close(abs(nrm[2]), 1.0, 1e-6) and close(abs(d), 3.0, 1e-6), (nrm, d))
    check("slope of a 30 degree plane", close(slope_degrees((0, -math.sin(math.radians(30)), math.cos(math.radians(30))), 2), 30.0, 1e-6))

    print("\nmesh_compare")
    res = compare(B, B, thresh=0.1)
    check("a mesh differs from itself nowhere", res["total"] == 0 and not res["clusters"], res["total"])
    stub = box(0, 10, 0, 20, 0, 30) + box(4, 6, 9, 11, 30, 35)       # a 5 mm post on top
    res = compare(stub, B, thresh=0.25)
    near = [c for c in res["clusters"] if math.dist(c["centre"], (5, 10, 33)) < 3.0]
    check("a post the other mesh lacks is found as a cluster", len(near) >= 1 and res["clusters"],
          [c["centre"] for c in res["clusters"]])
    res2 = compare(stub, B, thresh=0.25, explain=lambda q: "the post" if q[2] > 30.1 else None)
    check("explained regions are set aside, not hidden", res2["explained"].get("the post", 0) > 0
          and not any(q[2] > 30.1 for q, _ in res2["far"]), res2["explained"])


# ---------------------------------------------------------------------------
def solvespace_tests():
    from slvs_cli import have_solvespace, export_mesh, count_records, regenerate_counts
    if not have_solvespace():
        print("\nSKIPPED: solvespace-cli is not on the PATH, so the slvs_* tests did not run")
        return
    from slvs_write import (Sketch, ENT_ORIGIN, UNION, DIFFERENCE, HORIZONTAL, POINTS_COINCIDENT,
                            TWO_SIDED, dof_report)
    from slvs_shapes import rect, datums, spherical_cap
    from slvs_check import check_file, jitter_file
    from slvs_info import load, describe_constraint, summary
    from mesh_features import features_beyond, fit_sphere_cap
    from mesh_compare import compare
    from mesh_geom import volume

    H, BASE_R = 0.7721, 1.299
    R = (BASE_R ** 2 + H ** 2) / (2 * H)

    def block(with_bump=True, rect_dim=True, drop_constraint=False):
        S = Sketch()
        g, wp = S.workplane_group("base", ENT_ORIGIN, (1, 0, 0), (0, 1, 0))
        L = rect(S, g, wp, 10.0, 10.0, dim=rect_dim)
        if drop_constraint:
            # the classic mistake: the REQUEST's handle where the ENTITY's belongs
            S.constraint(HORIZONTAL, g, wp, entityA=L[0][0] >> 16)
        S.extrude("block", g, (0.0, 0.0, 10.0), combine=UNION)           # z in 0..20
        if with_bump:
            (pt,) = datums(S, [(10.0, 0.0, 10.0)])
            spherical_cap(S, "bump", pt, 10.0, +1, 0.0, H, R, UNION, visible=True)
        return S

    with tempfile.TemporaryDirectory() as tmp:
        def write(name, S):
            p = os.path.join(tmp, name)
            S.write(p)
            return p

        good = write("good.slvs", block())
        plain = write("plain.slvs", block(with_bump=False))

        print("\nslvs_write / slvs_shapes")
        S = block()
        rows = dof_report(S, S.group_names)
        check("every constrained group of a block with a cap is 0 DOF, 0 redundant",
              all(r["dof"] == 0 and r["redundant"] == 0 for r in rows if r["equations"]),
              [(r["name"], r["dof"], r["redundant"]) for r in rows])
        Sb = block(rect_dim=False)
        bad = [r for r in dof_report(Sb, Sb.group_names) if r["name"] == "base"][0]
        check("rect(dim=False) is reported 4 DOF", bad["dof"] == 4, bad["dof"])

        print("\nslvs_cli")
        r = export_mesh(good)
        check("a good block exports one mesh with no boolean failure",
              r["tris"] is not None and not r["boolean_failed"] and not r["self_intersecting"], r["messages"])
        check("its volume is the block plus the cap",
              close(volume(r["tris"]), 8000.0 + math.pi * H * (3 * BASE_R ** 2 + H * H) / 6, 0.15),
              volume(r["tris"]))
        c = count_records(good)
        check("count_records sees the groups", c["groups"] >= 4 and c["constraints"] > 10, c)
        before, after = regenerate_counts(good)
        check("a good file keeps its constraints through regenerate",
              before["constraints"] == after["constraints"], (before, after))

        print("\nslvs_info")
        d = load(good)
        names = [row[2] for row in summary(d)]
        check("the groups are read, by name", "bump" in names and "block" in names, names)
        lathe = [row for row in summary(d) if row[2] == "bump"][0]
        check("the lathe group is recognised and shown as a union", lathe[1] == "lathe" and "union" in lathe[3], lathe)
        lines = describe_constraint(d, int(d["constraints"][0]["h.v"], 16))
        check("a constraint handle resolves to a type and a group",
              lines and "pts-coincident" in lines[0], lines)
        check("an unknown handle returns None", describe_constraint(d, 0xfffff) is None)

        print("\nmesh_features / mesh_compare against the real cap")
        tris = r["tris"]
        fs = features_beyond(tris, 0, 10.0, +1)
        check("exactly one feature stands off the +x face", len(fs) == 1, len(fs))
        f = fs[0]
        check("its height is the cap's", close(f["height"], H, 0.002), f["height"])
        check("its centre is (y=0, z=10)", close(f["centre"][0], 0, 0.01) and close(f["centre"][1], 10, 0.01), f["centre"])
        check("its base radius is 1.299", close(f["half_extents"][0], BASE_R, 0.01), f["half_extents"])
        s = fit_sphere_cap(f)
        check("the sphere fit recovers the radius", close(s["radius"], R, 0.03), s)
        check("...and the height, and the mouth", close(s["height"], H, 0.01) and close(s["mouth"], BASE_R, 0.02), s)
        check("...with a small misfit", s["rms"] < 0.02, s["rms"])
        plain_tris = export_mesh(plain)["tris"]
        res = compare(tris, plain_tris, thresh=0.1)
        near = [c for c in res["clusters"] if math.dist(c["centre"], (10.35, 0, 10)) < 1.5]
        check("compare finds the cap the plain block lacks", len(near) == 1, [c["centre"] for c in res["clusters"]])
        # NOT tested: the reverse direction.  It reports samples only where the
        # source's own surface lies under or inside the other mesh's extra
        # feature, which a coarse flat face reaches only along its diagonal.
        # See mesh_compare's limits.

        print("\nslvs_check: it must PASS a sound file and FAIL broken ones")
        p = check_file(good, amp=0.3, seeds=2, out=lambda *_: None)
        check("a sound file passes all three checks", p == [], p)
        broken = write("dropped.slvs", block(with_bump=False, drop_constraint=True))
        b1, a1 = regenerate_counts(broken)
        p = check_file(broken, amp=0.3, seeds=1, jitter=False, out=lambda *_: None)
        check("a constraint aimed at a REQUEST is dropped by SolveSpace (the counts differ)",
              a1["constraints"] < b1["constraints"], (b1, a1))
        check("...and slvs_check reports it", any("regenerate" in x for x in p), p)
        loose = write("loose.slvs", block(with_bump=False, rect_dim=False))
        p = check_file(loose, amp=0.3, seeds=2, out=lambda *_: None)
        check("an under-constrained sketch exports a fine mesh yet is caught by the jitter test",
              any("not held by its constraints" in x for x in p), p)
        n = jitter_file(good, os.path.join(tmp, "j.slvs"), 0.3, 0)
        check("jitter_file moves sketch parameters and nothing else", n > 20, n)
        d0, d1 = load(good), load(os.path.join(tmp, "j.slvs"))
        same = [h for h in d0["params"] if h >= 0x80000000 and d0["params"][h] != d1["params"].get(h)]
        check("...it leaves the extrusion vector alone", not same, same[:3])


def main():
    quick = "--quick" in sys.argv
    print("pure-Python mesh tools")
    pure_python_tests()
    if not quick:
        solvespace_tests()
    print("\n%d passed, %d failed" % (PASSED[0], len(FAILED)))
    for f in FAILED:
        print("  FAILED: " + f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
