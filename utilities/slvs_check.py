"""Is a generated SolveSpace file actually sound?

    python3 slvs_check.py part.slvs [more.slvs ...]
    python3 slvs_check.py part.slvs --amp 0.3 --seeds 5

    from slvs_check import check_file, jitter_file

Three independent checks, each of which exists because the one before it let a
real defect through.

  1. THE MESH.  Export, then: one closed shell, consistent winding, no boolean
     failure.  This is what everyone checks, and it is not enough -- see 2 and 3.

  2. THE CONSTRAINTS SURVIVE.  SolveSpace deletes, silently, any constraint that
     refers to an entity that does not exist.  A constraint on a LINE that was
     given the request's handle instead of the request's entity handle
     ((request << 16) | 0) disappears on load: horizontal, vertical, tangent,
     equal-radius and diameter constraints all went, 20 in and 8 out, and the
     exported mesh was unchanged, because the seeded coordinates were right.  The
     only signal is a dialog in the GUI.  This regenerates a copy and compares
     the counts of groups, requests and constraints.

  3. THE SKETCH IS HELD BY ITS CONSTRAINTS, not by its coordinates.  A .slvs
     stores parameter values, and SolveSpace uses them only as a starting guess.
     A group can therefore be rank-deficient -- redundant AND under-constrained
     at once, or not at a solution at all -- and still export a perfect mesh,
     survive `regenerate`, and pass 1 and 2, because the solver starts at the
     answer and has nothing to do.  Only the GUI says "unsolvable constraints".
     So: perturb every sketch parameter by up to `amp` mm, let SolveSpace solve,
     and require the solid to come back.  (`slvs_write.dof_report` is the other
     way to ask this, without SolveSpace; it needs the file to have been written
     by `slvs_write`.)

What passing 3 does and does not mean.  It restores at small `amp` (0.3 mm) when
every group is genuinely constrained.  At larger `amp` an arc can flip to the
other side of its tangent lines -- a rounded rectangle whose corner radius is
smaller than the perturbation has two valid solutions -- and the solid changes
legitimately; that is not a missing constraint.  So `amp` should be smaller than
the smallest radius in the sketch, and a failure at 1 mm that passes at 0.3 mm
is usually that.  Extrusion and lathe parameters (handles >= 0x80000000) are not
perturbed: they are lengths, not sketch geometry, and are free by design.
"""
import os
import random
import tempfile

import mesh_check
from mesh_geom import bbox, volume
from slvs_cli import export_mesh, regenerate_counts, have_solvespace


def jitter_file(src, dst, amp, seed):
    """Write a copy of `src` with every sketch-geometry parameter moved by a
    random amount in [-amp, amp].  Returns how many were moved."""
    rnd = random.Random(seed)
    out, handle, n = [], None, 0
    with open(src, "rb") as fh:
        data = fh.read()
    for line in data.split(b"\n"):
        if line.startswith(b"Param.h.v.="):          # the key itself ends in a dot
            handle = int(line[len(b"Param.h.v.="):], 16)
        if line.startswith(b"Param.val=") and handle is not None and handle < 0x80000000:
            out.append(b"Param.val=%.20f" % (float(line[len(b"Param.val="):]) +
                                             rnd.uniform(-amp, amp)))
            n += 1
            continue
        out.append(line)
    with open(dst, "wb") as fh:
        fh.write(b"\n".join(out))
    return n


def _same_solid(t, ref, vol_tol, box_tol):
    if t is None:
        return False, "no mesh"
    dv = volume(t) - volume(ref)
    lo, hi = bbox(t)
    rlo, rhi = bbox(ref)
    db = max(max(abs(lo[i] - rlo[i]), abs(hi[i] - rhi[i])) for i in range(3))
    return abs(dv) <= vol_tol and db <= box_tol, "volume %+.4f mm^3, bbox %.4f mm" % (dv, db)


def check_file(path, amp=0.3, seeds=5, jitter=True, chord_tol=0.02, vol_tol=0.05,
               box_tol=0.01, out=print):
    """Run the three checks on one .slvs.  Returns a list of problems (empty =
    sound).  `vol_tol` is generous for a reason: two exports of the same file
    differ in tessellation by a few thousandths of a mm^3."""
    problems = []
    out("== %s" % path)
    if not have_solvespace():
        return ["solvespace-cli is not on the PATH"]

    # 1. the mesh
    with tempfile.TemporaryDirectory() as tmp:
        stl = os.path.join(tmp, "m.stl")
        r = export_mesh(path, chord_tol, out=stl)
        if r["tris"] is None:
            out("  mesh          NONE written")
            return ["no mesh was produced"] + r["messages"][:3]
        h = mesh_check.check(stl, verbose=False)
    out("  mesh          %d triangles, %d shell(s), %s, volume %.2f mm^3"
        % (h["triangles"], h["shells"],
           "watertight" if not h["non_manifold_edges"] else
           "NOT watertight (%d bad edges)" % h["non_manifold_edges"], h["volume"]))
    if r["boolean_failed"] or r["self_intersecting"]:
        problems.append("SolveSpace's boolean failed (self-intersecting mesh / trim errors): "
                        "the solid is not the part")
    if h["non_manifold_edges"]:
        problems.append("%d non-manifold edges" % h["non_manifold_edges"])
    if not h["winding_consistent"]:
        problems.append("inconsistent winding")
    if h["shells"] != 1:
        problems.append("%d shells, expected 1" % h["shells"])
    if r["retries"]:
        out("  boolean       %d surface-intersection retries (see slvs_cli); harmless "
            "when the mesh above is watertight and one shell" % r["retries"])
    for m in r["messages"]:
        out("  message       " + m)

    # 2. the constraints survive a reload
    before, after = regenerate_counts(path)
    lost = {k: before[k] - after[k] for k in ("groups", "requests", "constraints")
            if after[k] != before[k]}
    out("  regenerate    groups %d -> %d, requests %d -> %d, constraints %d -> %d"
        % (before["groups"], after["groups"], before["requests"], after["requests"],
           before["constraints"], after["constraints"]))
    for k, d in lost.items():
        problems.append("regenerate changed the number of %s by %+d (SolveSpace deleted "
                        "records that referred to nothing)" % (k, -d))

    # 3. held by constraints, not by coordinates
    if jitter and r["tris"]:
        ref = r["tris"]
        bad = []
        with tempfile.TemporaryDirectory() as tmp:
            for seed in range(seeds):
                dst = os.path.join(tmp, "j.slvs")
                n = jitter_file(path, dst, amp, seed)
                t = export_mesh(dst, chord_tol)["tris"]
                ok, why = _same_solid(t, ref, vol_tol, box_tol)
                if not ok:
                    bad.append("seed %d: %s" % (seed, why))
        out("  jitter        %d params moved up to +-%.2f mm, %d seeds: %s"
            % (n, amp, seeds, "all restored" if not bad else "%d did NOT restore" % len(bad)))
        for b in bad:
            problems.append("sketch not held by its constraints at +-%.2f mm (%s)" % (amp, b))
    return problems


if __name__ == "__main__":
    import argparse
    import sys
    ap = argparse.ArgumentParser(description="Check generated .slvs files.")
    ap.add_argument("slvs", nargs="+")
    ap.add_argument("--amp", type=float, default=0.3,
                    help="jitter amplitude in mm; keep it below the smallest radius (default 0.3)")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--no-jitter", action="store_true")
    ap.add_argument("--chord-tol", type=float, default=0.02)
    a = ap.parse_args()
    bad = 0
    for f in a.slvs:
        p = check_file(f, a.amp, a.seeds, not a.no_jitter, a.chord_tol)
        if p:
            bad += 1
            for line in p:
                print("  PROBLEM       " + line)
        else:
            print("  sound")
    sys.exit(1 if bad else 0)
