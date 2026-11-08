# Ultra Guard Pro 100+ deck box

Parametric SolveSpace models of both halves of a 100+ card deck box, rebuilt
from the STLs in `orig/`. The bottom has a label engraved on its front face.
Design rationale, measurements and the build log are in
[`ultra_guard_pro_100_spec.md`](ultra_guard_pro_100_spec.md); this file is how
to *use* it.

| Path | What it is |
|---|---|
| `ultra_guard_pro_100_bottom.slvs` / `.stl` | the bottom, with the label |
| `ultra_guard_pro_100_top.slvs` / `.stl` | the top |
| `cad/ugp100_params.py` | every dimension, including the label text |
| `cad/build_ugp100.py` | generates both `.slvs` |
| `cad/relabel.py` | **changes the label** |
| `cad/check_ugp100.py` | full verification against the source STLs |
| `cad/audit_missing.py` | finds features the original has and the rebuild lacks |
| `archive/` | kept STLs, named `ultra_guard_pro_100_bottom-<label>.stl` |
| `orig/` | the source STLs |

Needs `solvespace-cli` on the path and Python 3 (standard library only).
Run the commands below from this folder.

## Changing the label

The label lives in exactly one place, `TEXT` in `cad/ugp100_params.py`, but
**do not edit it by hand**: a new string changes the text's size and position,
and `relabel.py` does that, rebuilds, and verifies.

### 1. Look before you change anything

```bash
python3 cad/relabel.py "Spock"
```

This is a **dry run**. It changes nothing. It fits the string, then builds the
bottom with it in a temporary folder and checks the result. Read the report:

```
  sized by     HEIGHT   (the text is as large as the panel's height allows)
  cap height   15.06 mm
  ink          60.76 wide x 19.99 tall mm   -> 87% of the panel's width, 100% of its height
  stroke       ~2.04 mm thick
  depth        3.00 mm, leaving 1.78 mm of wall
  margins      6.53 mm to each side's corner tangent, 3.63 above and below
  note: the label has descenders ...
```

| You see | It means |
|---|---|
| `sized by HEIGHT` | the 20 mm panel height sets the size. Normal for short labels. |
| `sized by WIDTH` | the label is long enough that the 70 mm width sets the size, so letters are smaller. A `note:` says so. |
| `note: ... descenders` | g j p q y hang below the baseline and count toward the 20 mm, so the **capitals are smaller than a label without them would get**. Expected, not a bug. |
| `stroke ~1.2 mm` or less | thin. Under 1.2 mm is "printable but only just"; under 0.8 mm (two 0.4 mm nozzle widths) it will not print reliably. A rule of thumb, not a measurement of your printer. |
| `CANNOT ENGRAVE: ... not in font` | a character the font does not have. See below. |
| `PROBLEM: ...` after the trial build | the label does not engrave cleanly. Nothing was changed. |

Try as many labels as you like; the dry run is free.

### 2. Apply it

```bash
python3 cad/relabel.py "Spock" --apply
```

It rewrites `TEXT`, rebuilds both `.slvs`, exports the bottom's STL, runs the
full verification (`cad/check_ugp100.py`), and checks the top's `.slvs` came out
unchanged. It exits 0 only if all of that passed. Add `--archive` to also copy
the new STL to `archive/ultra_guard_pro_100_bottom-<label>.stl`; it will not
overwrite an existing one.

**Keep the outgoing label first.** `--archive` stores the *new* label. If you
want the old one kept, copy `ultra_guard_pro_100_bottom.stl` into `archive/`
under its label name *before* relabelling.

### 3. Look at the file

```bash
solvespace ultra_guard_pro_100_bottom.slvs
```

The verification is this repo's own check, not SolveSpace's, so open the file
once and confirm it comes up without "unsolvable constraint" messages. (An
earlier version passed every check and still failed here; spec 6.7.)

### 4. Commit

Expect **exactly** these to have changed, and nothing else:

```
cad/ugp100_params.py                   the TEXT line
ultra_guard_pro_100_bottom.slvs
ultra_guard_pro_100_bottom.stl
ultra_guard_pro_100_spec.md            if you update the label's numbers there
archive/...                            only if you used --archive
```

If `ultra_guard_pro_100_top.slvs` shows as modified, stop: a relabel does not
touch the top, so something other than the label changed.

The `.stl` is not reproducible. `solvespace-cli export-mesh` gives different
triangulations on every run, so an STL can show as modified when nothing
changed. That is why only the bottom's STL is regenerated, and only on a
relabel. Do not regenerate the top's STL to "tidy up".

## What can go wrong

**`not in font`.** The label has a character the font lacks (anything outside
plain Latin letters, digits and common punctuation is at risk: `☃`, `日`).
SolveSpace does *not* fail on these; it draws an unrelated glyph and exports
happily, so the tool refuses instead. Use characters the font has.

**`over the 32-character limit`, or `empty`.** Self-explanatory. 32 characters
is already unreadable on a 70 mm panel.

**`PROBLEM: self-intersecting mesh`.** SolveSpace's boolean failed on that
label's outlines. Never seen with a real label so far (touching pairs like
`AVAV`, `Ty To` and `fjfj` all pass), but it is the failure that measurement
cannot predict, which is why the dry run actually builds. Try a different
spelling or case, and if you hit a label you need, note the string in the
spec's build log (6.9) so the next person knows.

**Capitals look small.** Descenders (see the table above), or the label is
width-limited. Shorten it, or change the panel in `cad/ugp100_params.py`
(`PANEL_W`, `PANEL_H`) and re-run `relabel.py "<same text>" --apply`.

**Reverting.** `python3 cad/relabel.py "MTG" --apply`, or `git checkout` the
files listed above.

## The snap

Four domes on the bottom's lip (two per side) seat in four dimples in the top's
groove, and that is what holds the lid shut. They are built as spherical caps
by lathing, parameterised in `cad/ugp100_params.py` (`BUMP_*`, `DENT_*`,
`SNAP_POINTS`). The dome is a circular cap, not the source's ellipse: it matches
the source's height and its profile along the direction the lid slides, but is
about 0.5 mm narrower in y. If the printed lid is too loose, that is the first
thing to widen. Spec D11 and 6.10.

Whenever a part is rebuilt from a source, run

```bash
python3 cad/audit_missing.py            # ~25 s; exit 0 = nothing unexplained
python3 cad/audit_missing.py --prove    # shows it can see a missing feature
```

as well as `check_ugp100.py`. The checks compare what the rebuild *has*; this
asks what it *lacks*.

## Other changes

These are not label changes, so there is no helper. Edit `cad/ugp100_params.py`,
then:

```bash
python3 cad/build_ugp100.py     # regenerate both .slvs
python3 cad/check_ugp100.py     # verify
```

`check_ugp100.py` compares against the *original* STLs, so after a deliberate
change to a fit dimension its face-by-face section will report the difference.
That is its job. The spec's tuning table (section 8) lists what each parameter
does.

## The font

The label is set in Bitstream Vera Sans, the font SolveSpace bundles, not
Verdana. If a font is missing SolveSpace does not substitute another; it draws
a big X, so a font the machine lacks would make the file fail there. Vera is
compiled into SolveSpace and always resolves, and it is a close Verdana
relative. To use another font, set `TEXT_FONT` in `cad/ugp100_params.py` to its
file name, but only if it is installed on every machine that will open the
file. Spec decision D10.
