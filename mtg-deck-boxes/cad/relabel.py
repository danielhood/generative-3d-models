#!/usr/bin/env python3
"""Change the label engraved on the bottom's front face.

    python3 cad/relabel.py "Spock"                 # DRY RUN: fit report + trial build
    python3 cad/relabel.py "Spock" --apply         # really change the label
    python3 cad/relabel.py "Spock" --apply --archive

The default changes nothing.  It reports how the string will be sized and
placed, then builds the bottom with it in a temporary folder and checks the
result, so a label that cannot be engraved -- a character the font lacks, a
glyph combination SolveSpace's boolean chokes on, too little wall left -- is
found out before anything is touched.

--apply then does the whole routine:

  1. rewrites TEXT in cad/ugp100_params.py        (the one place the label lives)
  2. rebuilds both .slvs                          (the top must come out unchanged)
  3. exports the bottom to ultra_guard_pro_100_bottom.stl
  4. runs the full verification, cad/check_ugp100.py

--archive also copies the STL to archive/ultra_guard_pro_100_bottom-<label>.stl,
matching the files already there.  It will not overwrite one.

Exit status is 0 only if everything it did passed.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PART = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))
sys.path.insert(0, HERE)

import mesh_check
import slvs_text
import ugp100_params as P
import build_ugp100 as builder
import check_ugp100 as checker
from stl_io import load_stl

PARAMS = os.path.join(HERE, "ugp100_params.py")
BOTTOM_SLVS = os.path.join(PART, "ultra_guard_pro_100_bottom.slvs")
TOP_SLVS = os.path.join(PART, "ultra_guard_pro_100_top.slvs")
BOTTOM_STL = os.path.join(PART, "ultra_guard_pro_100_bottom.stl")

MIN_STEM = 0.8          # two 0.4 mm nozzle widths: below this a stroke is unreliable
THIN_STEM = 1.2         # below this it prints, but only just


def slug(text):
    """Filename-safe form of a label, for the archive."""
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_") or "label"


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def report(text):
    """Fit the string and print how it will be engraved.  Returns (fit, warnings)."""
    f = slvs_text.fit(text, P.TEXT_FONT, P.PANEL_W, P.PANEL_H)
    stem = slvs_text.stem_width(P.TEXT_FONT) * f["cap"]
    flat_x = P.EXT_HX - P.EXT_CORNER_R
    side = flat_x - f["ink_w"] / 2.0
    top = P.Z_FRONT_TOP - (P.PANEL_ZC + P.PANEL_H / 2.0)
    warn = []

    print("  label        %r   (currently %r)" % (text, P.TEXT))
    print("  font         %s" % P.TEXT_FONT)
    print("  panel        %.0f x %.0f mm, centred on the front face" %
          (P.PANEL_W, P.PANEL_H))
    print("  sized by     %s   (the text is as large as the panel's %s allows)"
          % (f["binding"].upper(), f["binding"]))
    print("  cap height   %.2f mm     (capital letters; a lowercase x-height is "
          "smaller)" % f["cap"])
    print("  ink          %.2f wide x %.2f tall mm   -> %.0f%% of the panel's "
          "width, %.0f%% of its height" % (f["ink_w"], f["ink_h"],
                                           100 * f["ink_w"] / P.PANEL_W,
                                           100 * f["ink_h"] / P.PANEL_H))
    print("  stroke       ~%.2f mm thick" % stem)
    print("  depth        %.2f mm, leaving %.2f mm of wall" %
          (P.TEXT_DEPTH, P.WALL_Y - P.TEXT_DEPTH))
    print("  margins      %.2f mm to each side's corner tangent, %.2f above and "
          "below" % (side, top))

    desc = f["measure"]["z0"] < -0.02
    if f["binding"] == "width":
        warn.append("the label is WIDTH-limited: it is long enough that the 70 mm "
                    "panel, not the 20 mm height, sets the size, so the letters "
                    "are only %.1f mm tall" % f["cap"])
    if desc:
        warn.append("the label has descenders (g j p q y): they count toward the "
                    "20 mm height, so the capitals are %.1f mm rather than the "
                    "%.1f a label without them would get" % (
                        f["cap"], P.PANEL_H / (
                            f["measure"]["z1"] - 0.0)))
    if stem < MIN_STEM:
        warn.append("strokes are ~%.2f mm: thinner than two 0.4 mm nozzle widths, "
                    "so they will not print reliably" % stem)
    elif stem < THIN_STEM:
        warn.append("strokes are ~%.2f mm: printable, but only just" % stem)
    return f, warn


def trial(text):
    """Build the bottom with `text` in a temp folder and check it.  Changes
    nothing in the repo.  Returns a list of problems (empty = fine)."""
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "trial.slvs")
        out = os.path.join(tmp, "trial.stl")
        builder.build_bottom(text=text).write(src)
        r = subprocess.run(["solvespace-cli", "export-mesh", "--chord-tol", "0.02",
                            "--output", out, src], capture_output=True, text=True)
        if not os.path.exists(out):
            return ["SolveSpace produced no mesh for this label"], None, None
        if "self-intersecting" in (r.stdout + r.stderr):
            problems.append("SolveSpace reports a self-intersecting mesh: its "
                            "boolean failed on this label's outlines")
        health = mesh_check.check(out, verbose=False)
        tris = load_stl(out)
    if health["non_manifold_edges"]:
        problems.append("%d non-manifold edges: the mesh is not watertight"
                        % health["non_manifold_edges"])
    if not health["winding_consistent"]:
        problems.append("inconsistent triangle winding")
    if health["shells"] != 1:
        problems.append("%d separate shells instead of one" % health["shells"])

    # the same engraving checks the full verification runs
    before = len(checker.FAIL)
    with contextlib.redirect_stdout(io.StringIO()):
        data = checker.check_engraving(tris)
    problems += checker.FAIL[before:]
    del checker.FAIL[before:]
    return problems, data, health


def set_label(text):
    src = open(PARAMS).read()
    new, n = re.subn(r'(?m)^TEXT = .*$', "TEXT = " + json.dumps(text, ensure_ascii=False),
                     src, count=1)
    if n != 1:
        raise RuntimeError("could not find the TEXT = ... line in %s" % PARAMS)
    open(PARAMS, "w").write(new)


def run(cmd, quiet=False):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=PART)
    if not quiet:
        sys.stdout.write(r.stdout)
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", help="the new label")
    ap.add_argument("--apply", action="store_true",
                    help="really change the label (the default is a dry run)")
    ap.add_argument("--archive", action="store_true",
                    help="also copy the new STL to archive/, named by label")
    args = ap.parse_args()
    text = args.text

    print("=" * 72)
    print("fit report")
    print("=" * 72)
    try:
        f, warn = report(text)
    except slvs_text.TextError as e:
        print("  CANNOT ENGRAVE: %s" % e)
        return 2
    for w in warn:
        print("  note: " + w)

    print()
    print("=" * 72)
    print("trial build (temporary folder; nothing in the repo is touched)")
    print("=" * 72)
    try:
        problems, data, health = trial(text)
    except slvs_text.TextError as e:
        print("  CANNOT ENGRAVE: %s" % e)
        return 2
    if health:
        print("  mesh         %d triangles, %d shell, %.1f mm^3" %
              (health["triangles"], health["shells"], health["volume"]))
    if data:
        print("  pocket       %.2f mm^3 removed, %.2f mm of wall behind it" %
              (data["removed"], data["wall"]))
    if problems:
        for p in problems:
            print("  PROBLEM: " + p)
        print("\nnot applied: this label does not engrave cleanly.")
        return 1
    print("  all engraving checks pass")

    if not args.apply:
        print("\ndry run: nothing was changed.  Re-run with --apply to use it.")
        return 0

    archive = None
    if args.archive:
        archive = os.path.join(PART, "archive",
                               "ultra_guard_pro_100_bottom-%s.stl" % slug(text))
        if os.path.exists(archive):
            print("\nnot applied: %s already exists and will not be overwritten."
                  % os.path.relpath(archive, PART))
            return 1

    print()
    print("=" * 72)
    print("applying")
    print("=" * 72)
    top_before = md5(TOP_SLVS)
    set_label(text)
    print("  1. TEXT = %s   in cad/ugp100_params.py" % json.dumps(text))
    r = run([sys.executable, os.path.join(HERE, "build_ugp100.py")], quiet=True)
    if r.returncode:
        sys.stdout.write(r.stdout + r.stderr)
        print("  rebuild FAILED")
        return 1
    print("  2. rebuilt both .slvs")
    r = run(["solvespace-cli", "export-mesh", "--chord-tol", "0.02", "--output",
             BOTTOM_STL, BOTTOM_SLVS], quiet=True)
    if not os.path.exists(BOTTOM_STL):
        print("  STL export FAILED")
        return 1
    print("  3. exported ultra_guard_pro_100_bottom.stl")

    print("  4. running the full verification ...")
    r = run([sys.executable, os.path.join(HERE, "check_ugp100.py")], quiet=True)
    tail = [l for l in r.stdout.splitlines() if l.startswith(("all checks", "  FAIL",
            "  - ", "CHECK"))]
    for l in tail:
        print("     " + l.strip())
    if r.returncode:
        print("  verification FAILED -- the files on disk are the new label's, "
              "but it does not pass.")
        return 1

    if md5(TOP_SLVS) != top_before:
        print("  WARNING: the top's .slvs changed.  A relabel should not touch it; "
              "something other than the label differs.")
        return 1
    print("     the top's .slvs is unchanged, as it should be")

    if archive:
        os.makedirs(os.path.dirname(archive), exist_ok=True)
        shutil.copyfile(BOTTOM_STL, archive)
        print("  5. archived as %s" % os.path.relpath(archive, PART))

    print()
    print("done.  Review with `git status` / `git diff --stat`; expect the bottom's")
    print(".slvs and .stl, ugp100_params.py and the spec to change, and nothing else.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
