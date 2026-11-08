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

from slvs_write import Sketch, ENT_ORIGIN, UNION
from stl_io import load_stl

# SolveSpace's own bundled Bitstream Vera Sans.  Chosen over a system font
# because it resolves on every SolveSpace install -- a request naming a font
# the machine lacks draws a big X instead of text.  It is also a close Verdana
# relative: both are wide, open humanist sans faces with large x-heights.
BUILTIN_FONT = "BitstreamVeraSans-Roman-builtin.ttf"

_CAP = 100.0          # test height; large so mesh facets are small against it

MAX_LEN = 32          # a label that long is unreadable on a 70 mm panel anyway


class TextError(ValueError):
    """The string cannot be engraved as asked.  The message says why in terms
    a person renaming the label can act on."""


def validate(string):
    """Reject strings the .slvs format or the panel cannot carry.  Request.str
    is stored as one line of the file, so anything that is not plain printable
    text on one line would corrupt it."""
    if not string or not string.strip():
        raise TextError("the label is empty (or only spaces)")
    if len(string) > MAX_LEN:
        raise TextError("the label is %d characters; the limit is %d"
                        % (len(string), MAX_LEN))
    bad = sorted({c for c in string if not c.isprintable()})
    if bad:
        raise TextError("the label contains non-printable characters: %s"
                        % ", ".join("U+%04X" % ord(c) for c in bad))


def _missing_glyphs(output):
    """Characters the font lacks, from SolveSpace's own messages.

    A missing glyph does NOT fail.  FreeType reports "CID-to-GID mapping ...
    failed" on stderr, SolveSpace carries on using the character code as a
    glyph index, and what comes out is a shape from some unrelated glyph -- or
    nothing -- in an otherwise normal-looking mesh.  The message is the only
    signal there is, so it has to be turned into an error here.
    """
    found = []
    for m in re.finditer(r"CID-to-GID mapping for CID 0x([0-9a-fA-F]+)", output):
        ch = chr(int(m.group(1), 16))
        if ch not in found:
            found.append(ch)
    return found


def measure(string, font=BUILTIN_FONT):
    """-> dict(aspect, x0, x1, z0, z1): the request's aspect ratio, and the ink
    box of `string` relative to the bottom-left point, all in cap heights.

    Raises TextError for a string that cannot be engraved, including one with a
    character the font does not have."""
    validate(string)
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "t.slvs")
        stl = os.path.join(tmp, "t.stl")
        S = Sketch()
        g, wp = S.workplane_group("t", ENT_ORIGIN, (1, 0, 0), (0, 1, 0))
        S.text(g, wp, string, font, (0.0, 0.0), _CAP, 1.0)     # aspect: a guess
        S.extrude("e", g, (0.0, 0.0, 5.0), combine=UNION)
        S.write(src)

        # regenerate rewrites the file with the aspect ratio SolveSpace computed
        r1 = subprocess.run(["solvespace-cli", "regenerate", src],
                            capture_output=True, text=True)
        text = open(src, "rb").read().decode("utf-8", "replace")
        missing = _missing_glyphs(r1.stdout + r1.stderr)
        if missing:
            raise TextError(
                "%s not in font %s -- SolveSpace would draw garbage for %s, not "
                "an error.  Use characters the font has (plain ASCII is safe)."
                % (", ".join("%r (U+%04X)" % (c, ord(c)) for c in missing),
                   font, "it" if len(missing) == 1 else "them"))
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
            raise TextError("%r has no outline to engrave (is it all spaces?)"
                            % string)
        tris = load_stl(stl)

    xs = [v[0] for t in tris for v in t]
    ys = [v[1] for t in tris for v in t]
    return {"aspect": aspect,
            "x0": min(xs) / _CAP, "x1": max(xs) / _CAP,
            "z0": min(ys) / _CAP, "z1": max(ys) / _CAP}


_stem_cache = {}


def stem_width(font=BUILTIN_FONT):
    """The font's vertical stroke thickness, in cap heights.

    Measured, not remembered: a capital I in a sans face is a plain vertical
    bar, so its ink width IS the stem.  This is what has to survive printing --
    a stroke thinner than two nozzle widths (~0.8 mm) prints as a ragged line or
    drops out.
    """
    if font not in _stem_cache:
        m = measure("I", font)
        _stem_cache[font] = m["x1"] - m["x0"]
    return _stem_cache[font]


def fit(string, font, panel_w, panel_h):
    """Size and place `string` to fill a panel_w x panel_h panel, centred.

    Fitting is by the INK box, never the cap height or the advance width: round
    letters overshoot the cap height, descenders (g, j, p, q, y) and tall
    letters (b, d, f, h, k, l) extend well past it, and side bearings shift the
    horizontal centre.  For "MTG" the ink is 1.04 cap-heights tall; for "Spock"
    it is 1.33, because the p's descender and the k's ascender both count.

    Returns the cap height `cap` in mm, rounded DOWN to 0.01 (a clean number in
    the GUI), the ink size in mm, the bottom-left origin (`ou`, `ov`) relative
    to the panel centre that puts the ink box on it, and `binding`: which panel
    dimension limits the size, "height" or "width".
    """
    m = measure(string, font)
    ink_w, ink_h = m["x1"] - m["x0"], m["z1"] - m["z0"]
    by_h, by_w = panel_h / ink_h, panel_w / ink_w
    cap = int(min(by_h, by_w) * 100) / 100.0
    return {"cap": cap, "aspect": m["aspect"],
            "ink_w": ink_w * cap, "ink_h": ink_h * cap,
            "ou": -(m["x0"] + m["x1"]) / 2.0 * cap,
            "ov": -(m["z0"] + m["z1"]) / 2.0 * cap,
            "binding": "height" if by_h <= by_w else "width",
            "measure": m}


if __name__ == "__main__":
    for s in sys.argv[1:] or ["MTG"]:
        m = measure(s)
        print("%r  aspect %.6f   ink x [%.5f, %.5f]  z [%.5f, %.5f]   "
              "ink %.5f wide x %.5f tall (cap heights)"
              % (s, m["aspect"], m["x0"], m["x1"], m["z0"], m["z1"],
                 m["x1"] - m["x0"], m["z1"] - m["z0"]))
