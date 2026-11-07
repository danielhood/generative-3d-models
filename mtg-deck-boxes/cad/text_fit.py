"""Measure a string in a SolveSpace font, using SolveSpace.

Fitting text into a panel needs two things the .slvs format does not let you
compute yourself without reimplementing FreeType:

  * the string's aspect ratio (advance width / cap height) -- it is stored in
    the request and must be right, because the text's other two corner points
    are pinned to it
  * where the INK sits inside that box -- advance width is not ink width (side
    bearings), and cap height is not ink height (round glyphs such as G
    overshoot it)

So this builds a throwaway sketch with the text at a known size, has
`solvespace-cli regenerate` write back the aspect ratio it computed, extrudes
the text and reads the ink box off the exported mesh.  Everything comes back
in units of cap height, so it scales to any size by multiplication.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "utilities"))

from slvs_write import Sketch, ENT_ORIGIN, UNION
from stl_io import load_stl

# SolveSpace's own bundled Bitstream Vera Sans.  Chosen over a system font
# because it resolves on every SolveSpace install -- a request naming a font
# the machine lacks draws a big X instead of text.  It is also a close Verdana
# relative: both are wide, open humanist sans faces with large x-heights.
BUILTIN_FONT = "BitstreamVeraSans-Roman-builtin.ttf"

_CAP = 100.0          # test height; large so mesh facets are small against it


def measure(string, font=BUILTIN_FONT):
    """-> dict(aspect, x0, x1, z0, z1): the request's aspect ratio, and the ink
    box of `string` relative to the bottom-left point, all in cap heights."""
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "t.slvs")
        stl = os.path.join(tmp, "t.stl")
        S = Sketch()
        g, wp = S.workplane_group("t", ENT_ORIGIN, (1, 0, 0), (0, 1, 0))
        S.text(g, wp, string, font, (0.0, 0.0), _CAP, 1.0)     # aspect: a guess
        S.extrude("e", g, (0.0, 0.0, 5.0), combine=UNION)
        S.write(src)

        # regenerate rewrites the file with the aspect ratio SolveSpace computed
        subprocess.run(["solvespace-cli", "regenerate", src], capture_output=True)
        text = open(src, "rb").read().decode("utf-8", "replace")
        m = re.search(r"Request\.aspectRatio=([-0-9.eE+]+)", text)
        if not m:
            raise RuntimeError("regenerate did not report an aspect ratio")
        aspect = float(m.group(1))
        if abs(aspect - 1.0) < 1e-12:
            raise RuntimeError("font %r did not resolve (aspect stayed at the "
                               "seed)" % font)

        # export at the REAL aspect so the ink box is the real one
        subprocess.run(["solvespace-cli", "export-mesh", "--chord-tol", "0.01",
                        "--output", stl, src], capture_output=True)
        if not os.path.exists(stl):
            raise RuntimeError("could not extrude text %r" % string)
        tris = load_stl(stl)

    xs = [v[0] for t in tris for v in t]
    ys = [v[1] for t in tris for v in t]
    return {"aspect": aspect,
            "x0": min(xs) / _CAP, "x1": max(xs) / _CAP,
            "z0": min(ys) / _CAP, "z1": max(ys) / _CAP}


if __name__ == "__main__":
    for s in sys.argv[1:] or ["MTG"]:
        m = measure(s)
        print("%r  aspect %.6f   ink x [%.5f, %.5f]  z [%.5f, %.5f]   "
              "ink %.5f wide x %.5f tall (cap heights)"
              % (s, m["aspect"], m["x0"], m["x1"], m["z0"], m["z1"],
                 m["x1"] - m["x0"], m["z1"] - m["z0"]))
