"""Thin, honest wrappers around `solvespace-cli`.

    from slvs_cli import export_mesh, count_records, regenerate_counts, thumbnail

    r = export_mesh("part.slvs")         # -> dict(tris, messages, self_intersecting)
    count_records("part.slvs")           # -> {"groups": 24, "requests": 36, "constraints": 98, ...}
    regenerate_counts("part.slvs")       # before and after SolveSpace rewrites the file

Everything the part scripts used to do inline, in one place.  Needs
`solvespace-cli` on the PATH (`have_solvespace()` says whether it is).

Why these wrappers are not trivial.

  * `export-mesh` is NOT deterministic.  Three runs over an unchanged .slvs gave
    three different STLs with different triangle counts (258, 260, 260), all
    geometrically identical (same volume to 0.001 mm^3, same bounding box).  So
    never compare two exports byte for byte, and expect an STL to show as
    modified in git when nothing changed.  The .slvs, written by a script, IS
    reproducible, which is the point of generating it.
  * It prints a great deal of noise, almost none of it a problem: missing
    translations, timing lines, `failed: I=...` and `print N edges` from the
    boolean's retries, and `Vector::WithMagnitude(1) of zero vector!` once per
    lathe (the zero-width surface an axis-edge sweeps out).  `messages` has the
    noise filtered out; what is left is worth reading.  The ones that matter:
    `trim was empty`, `failed to assemble polygon to trim nurbs surface`, and
    "The mesh is self-intersecting" -- the boolean has failed.  Distinct from
    those: `didn't converge (surface intersecting line)` and
    `AllPointsIntersectingUntrimmed failed` are RETRIES, counted in `retries`.
    They came with the snap dimples (56 of them) and nothing else, and the mesh
    was good every time, but a rising count on a part that used to give none is
    worth a look.
  * A failed boolean may still write an STL, of a part that is not the part.
    `self_intersecting` is the flag; do not trust `tris` when it is set.
  * `regenerate` REWRITES the file (it reloads, solves and saves).  These
    wrappers always work on a copy.  What it is for: SolveSpace silently deletes
    any constraint that refers to something that does not exist (a wrong entity
    handle), reporting it only as a dialog box in the GUI.  Counting constraints
    before and after is the one cheap way to see that from a script.
"""
import os
import shutil
import subprocess
import tempfile

from stl_io import load_stl

# lines solvespace-cli prints that are not problems
NOISE = (
    "Missing (absent) translation",
    "Generate::ALL took",
    "Written '",
    "failed: I=",
    "print ",
    "trim was",           # followed by "empty"/"unterminated": see BOOLEAN_FAILURE
    "Vector::WithMagnitude",
    "Message: Additional sketch elements were deleted",
)
# the ones in NOISE that are, in fact, symptoms of a failed boolean when they
# appear alongside an empty or self-intersecting mesh
BOOLEAN_FAILURE = ("trim was empty", "trim was unterminated", "failed to assemble polygon")
# SolveSpace's surface-intersection solver reporting that it had to retry.  Seen
# in pairs, dozens at a time, when a sphere is cut into a flat wall (the snap
# dimples: 56 of them, none for the domes), with a final mesh that is watertight,
# one shell, and measures to its parameters.  Counted, not listed.
BOOLEAN_RETRY = ("didn't converge", "AllPointsIntersectingUntrimmed")


def have_solvespace():
    return shutil.which("solvespace-cli") is not None


def _run(args):
    return subprocess.run(["solvespace-cli"] + args, capture_output=True, text=True)


def export_mesh(slvs, chord_tol=0.02, out=None):
    """Triangulate the sketch's solid.

    chord_tol  mm; the largest gap between a curve and its facets.  The default
               suits small parts; 0.01 for a sphere you will measure, 0.1 for a
               quick look.  Smaller means a lot more triangles.
    out        write the STL here and keep it; default is a temporary file.

    Returns {"tris": triangles or None, "messages": [...], "retries": int,
             "self_intersecting": bool, "boolean_failed": bool}.  `tris` is None if
    no mesh was written (typically: an empty solid, or a boolean that failed
    outright).  `messages` is de-duplicated, with "(xN)" on repeats; the
    surface-intersection retries are only counted, in `retries`.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = out or os.path.join(tmp, "export.stl")
        if os.path.exists(path):
            os.remove(path)
        r = _run(["export-mesh", "--chord-tol", str(chord_tol), "--output", path, slvs])
        text = r.stdout + r.stderr
        tris = load_stl(path) if os.path.exists(path) else None
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith(NOISE)]
    retries = sum(1 for l in lines if l.startswith(BOOLEAN_RETRY))
    seen, msgs = {}, []
    for l in lines:
        if l.startswith(BOOLEAN_RETRY):
            continue
        seen[l] = seen.get(l, 0) + 1
    for l, n in seen.items():
        msgs.append(l if n == 1 else "%s   (x%d)" % (l, n))
    return {"tris": tris, "messages": msgs, "retries": retries,
            "self_intersecting": "self-intersecting" in text,
            "boolean_failed": any(b in text for b in BOOLEAN_FAILURE)}


_MARKERS = {"AddGroup": "groups", "AddRequest": "requests", "AddConstraint": "constraints",
            "AddParam": "params", "AddEntity": "entities", "AddStyle": "styles"}


def count_records(path):
    """How many groups, requests, constraints, params ... a .slvs file holds."""
    counts = {v: 0 for v in _MARKERS.values()}
    with open(path, "rb") as fh:
        for line in fh.read().split(b"\n"):
            k = _MARKERS.get(line.strip().decode("latin-1"))
            if k:
                counts[k] += 1
    return counts


def regenerate_counts(path):
    """-> (before, after): `count_records` of the file as written, and of a COPY
    after SolveSpace has reloaded, solved and re-saved it.  `after` should match
    `before` in groups, requests and constraints; a lower constraint count means
    SolveSpace deleted constraints that referred to nothing."""
    before = count_records(path)
    with tempfile.TemporaryDirectory() as tmp:
        copy = os.path.join(tmp, "copy.slvs")
        shutil.copyfile(path, copy)
        _run(["regenerate", copy])
        after = count_records(copy)
    return before, after


def thumbnail(slvs, out, view="isometric", size="560x560", chord_tol=0.05):
    """Render a PNG.  `view` is top/bottom/left/right/front/back/isometric.

    SolveSpace's view names are NOT the obvious ones for a Z-up part: "front"
    looks straight down the Z axis at the XY plane, and the faces of a box are
    seen from "top" and "bottom" (which look along Y).  Try them; it is quicker
    than reasoning.  The render shows every VISIBLE group's wireframe, so a part
    whose scaffolding is not hidden looks like a thicket."""
    r = _run(["thumbnail", "--output", out, "--size", size, "--view", view,
              "--chord-tol", str(chord_tol), slvs])
    return os.path.exists(out)
