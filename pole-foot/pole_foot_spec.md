# Design spec: pole foot (29 x 27 mm elliptical pole, PETG)

Part: `pole_foot.scad` -> `pole_foot.stl`, `fit_test_ring.stl`
Revision: rev B (elliptical), 2026-09-07. Rev A was circular Ø27 - superseded.
Status: designed and mesh-verified; not yet printed

---

## 1. Requirements

| # | Requirement | Value |
|---|---|---|
| R1 | Pole section | elliptical, 29 mm x 27 mm |
| R2 | Pole insertion depth | 40 mm |
| R3 | Material below the end of the pole | 4 mm |
| R4 | Side wall thickness | 1.5 mm |
| R5 | Target material | PETG (rigid) |
| R6 | Vertical interior ridges for a tight fit | 0.4 mm |

### Assumptions made where the brief was open

| # | Assumption | Reasoning |
|---|---|---|
| A1 | R3 means a flat 4 mm floor, not a wider ground pad | The wording describes thickness under the pole, not a footprint. Flagged: a 32.8 x 30.8 x 44 mm cylinder is tippy if free-standing. **Open.** |
| A2 | R6 means ridges standing 0.4 mm proud of the bore wall | The alternative reading (0.4 mm wide ridges) gives no fit control - the height is what sets the interference. |
| A3 | R4 is a uniform 1.5 mm all round, measured off the bore | Uniform wall = uniform stiffness and a predictable print. Achieved with a true offset, not a scale (see C7). |
| A4 | 8 ridges, on ellipse parameters t = 0, 45 ... 315 | Puts a ridge at each of the four axis extremes, keeps the pattern symmetric about both axes, and leaves no direction of lean more than ~22.5 deg from a ridge. |
| A5 | Chamfers on all four exposed edges | Not requested; they cost nothing and remove the elephant's foot and the sharp mouth that would catch the pole. |
| A6 | The 29 mm axis lies along X | Arbitrary but fixed, so the ridge maths and the drawings agree. |

### Consequence of the elliptical section

The socket accepts the pole in **two rotations, 180 deg apart**. That is inherent
to the section, not a design choice - but it is a usability fact worth stating,
and it means the pole cannot be inserted 90 deg out and "nearly" work: at 90 deg
it is 2 mm oversize on one axis and simply will not enter.

---

## 2. Fit scheme

A plain 29.0 x 27.0 bore in a rigid material is a coin toss: 0.1 mm of print
variance separates "won't go in" from "falls out". Instead:

    bore        = offset(nominal, +clearance)          -> 29.8 x 27.8
    crest locus = offset(bore, -ridge_h) = nominal     -> 29.0 x 27.0

With `clearance == ridge_h == 0.4` the crests land exactly on the nominal pole
ellipse, everywhere around the section. Consequences:

- The pole beds on **8 narrow lines**, not one loose wall. Contact pressure is
  high enough to grip, and the contact area is small enough that print
  variation shows up as crest deflection rather than a jam.
- A 0.4 mm tall, Ø1.6 rounded PETG crest has enough give to squash slightly
  under interference. The 1.5 mm wall is not asked to flex.
- The 0.4 mm gap between crests gives a stray blob, a burr or dirt somewhere to
  go instead of preventing insertion.
- One tuning knob: `clearance`. `ridge_h` stays at the specified 0.4.

Ridge cross-section is a circle of Ø1.6 with its axis on `offset(nominal, 0.8)`,
so exactly 0.4 mm protrudes and the remaining 1.2 mm of root is buried in the
wall. Round crest over triangular: predictable line contact, prints as a solid
~4-line bump rather than an unfillable sharp corner, and a wide buried root that
cannot peel off the wall.

Ridges taper to nothing over the top 3 mm; the crest reaches the bore wall
halfway through, so the pole enters a plain 29.8 x 27.8 bore, squares up, and
only then meets the interference at z = 42.5.

---

## 3. Verified dimensions

Measured from the exported mesh, not from intent (section 5):

| | |
|---|---|
| Overall | 32.80 x 30.80 x 44.00 mm |
| Socket depth | 40.00 mm |
| Floor under pole | 4.00 mm |
| Side wall | 1.50 mm, uniform all round |
| Bore | 29.80 x 27.80 |
| Crest locus | on the nominal ellipse: measured +0.000 to +0.006 mm from it |
| Bore between ridges | +0.395 to +0.396 mm from nominal (target +0.400) |
| Ridges | 8 x 0.40 proud, Ø1.6 crest, full grip from z = 4 to 41 |
| Lead-in | crests recede from z = 41, flush with the bore by z = 42.5 |
| Chamfers | 0.8 bottom outer / 0.6 top outer / 0.6 bore mouth / 0.6 socket floor, uniform on both axes |
| Volume | 8.947 cm^3 (hand calc via Steiner: ~8.93) |
| Mesh | watertight, 1 shell, consistent winding, outward normals |

Residual errors are all from the 120-segment base ellipse: chord sagitta at
r = 14.5 is 0.005 mm, which is where the +0.006 at the crests and the 0.004
shortfall between ridges come from. Both are an order of magnitude below print
resolution.

---

## 4. Structure of the model

Everything derives from one base ellipse and 2D offsets of it:

    ell(off)              offset(r=off) of the nominal pole ellipse
    prism(off, z0, z1)    straight section
    taper(o0,z0,o1,z1)    hull of two thin slabs - this is how a chamfer is
                          made on a non-axisymmetric part

    outer_solid()   taper + prism + taper       (offset 1.9, chamfered both ends)
      - bore_cutter()   taper + prism + taper + axial overshoot   (offset 0.4)
      + ridges() clipped to outer_solid()

Ridge axes are placed with the ellipse's true outward normal (C9). Lead-in is
built into the ridge geometry as a cone, so there is no cutter to go tangent
(C2).

    openscad -o pole_foot.stl pole_foot.scad
    openscad -D 'part="fit_test"' -o fit_test_ring.stl pole_foot.scad

`part = "foot" | "fit_test"`; the test ring reuses every fit parameter, so it
cannot drift from the real part.

---

## 5. Verification method

Two dependency-free scripts, both reading ASCII or binary STL.

**`check_stl.py`** - shape-agnostic mesh integrity:

- **Topology** - every edge shared by exactly 2 faces; consistent winding
- **Orientation** - signed volume positive (outward normals)
- **Shells** - connected components over merged vertices; must be 1
- **Volume** - checked against a closed-form hand calculation
- **Bounding box**

**`check_fit.py`** - the fit itself, ellipse-aware. Polar radius is meaningless
on an ellipse, so instead it casts rays from the axis at a given height, finds
the first material boundary, and reports its **signed distance from the nominal
pole ellipse** (closest-point by dense sample + golden-section refine). The
design targets fall out directly:

    at a ridge crest   ->  0.000
    between ridges     -> +0.400

Four independent channels, each of which caught something the others missed:

| Channel | What it caught |
|---|---|
| Numbers (volume vs hand calc) | C1 hollowed base, C4 vanished ridges |
| Topology (manifold / shells) | C2, C3 non-manifold booleans |
| Fit probe (distance from nominal) | confirmed the rev B fit scheme end to end |
| Eyes (rendered PNG) | C5 ridges through the chamfer, C10 preview/CGAL mismatch |

OpenSCAD's own console line is a free pre-check: a single-body part should
report `Simple: yes` and `Volumes: 2` (the solid plus the unbounded outside).
The first broken version reported `Volumes: 4`.

---

## 6. Build log - challenges and solutions

Ten defects across two sessions. Eight of them produced a file that looked fine.

### Session 1 - circular rev A

#### C1 - A subtracted cone is not a chamfer

**Symptom.** Volume 7.961 cm^3 against a hand calculation of ~8.5; the bottom
of the foot was hollowed into a cone.

**Cause.** Chamfers cut with `difference() { body; cylinder(r1=..., r2=...); }`.
Subtracting a cone removes everything *inside* it, and at its wide end that is
the full cross-section of the part. A chamfer needs the *complement* - the
material outside the cone - which a plain cone cutter cannot express.

**Fix.** Build the silhouette as `rotate_extrude(polygon(profile))` with every
chamfer a vertex of the profile.

> **Pattern.** For an axisymmetric part, revolve a 2D (r, z) profile. Chamfers,
> lips, steps and shoulders become polygon points, which cannot be inverted and
> cannot leave slivers. Reserve booleans for genuinely non-axisymmetric
> features. (Superseded for non-axisymmetric parts by C8, not contradicted.)

#### C2 - Tangent cutters produce non-manifold geometry

**Symptom.** 20 edges shared by 4 faces, 50 mismatched directed edges, 3 shells;
OpenSCAD reported `Volumes: 4`.

**Cause.** The lead-in cone started at exactly the crest radius - tangent to the
ridge cylinders, grazing them along a line instead of crossing them. Separately,
the ridges were clipped with `intersection(ridges, cylinder(r = bore_r + eps))`,
putting a cut surface 0.01 mm from a surface it was meant to coincide with.

**Fix.** Start the cone inside the crest circle so it crosses transversally;
delete the eps-offset intersection.

> **Pattern.** A cutter must never be tangent to, or epsilon-offset from, the
> surface it cuts. Either it crosses at a clear angle and overshoots
> generously, or it shares the *exact same expression* as the surface it must
> line up with. "Nearly coincident" is the worst of the three.

#### C3 - Epsilon belongs on the axis, never on a radius

**Symptom.** The first fit-test ring had 192 four-way edges and 8 six-way edges.

**Cause.** Cone cutters written as `r = bore_r + eps` shaved a 0.01 mm ring off
the bore wall - material too thin to tessellate into anything sane.

**Fix.** `eps` only as axial overshoot on a through-cut. Where a taper had to
die out at a face, taper the *added* geometry instead of cutting it away.

> **Pattern.** Axial eps = harmless overshoot into empty space. Radial eps =
> a zero-width sliver of real material. Same constant, opposite consequences.

#### C4 - Boolean order silently deleted a whole feature

**Symptom.** The test ring passed *every* topology check - watertight, one
shell, correct bounding box, consistent winding. Its volume was exactly
pi(R^2 - r^2)h for a plain ring: all eight ridges were gone.

**Cause.** `difference(union(wall, ridges), bore_cutter)`. The ridges protrude
*into* the bore by definition, so the bore cutter ate them.

**Fix.** Cut the bore first, then union the ridges into the result.

> **Pattern 1.** Any feature that protrudes into a cut volume must be added
> *after* that cut. Ridges, tabs, keys, snap bumps, thread starts.
>
> **Pattern 2 (the important one).** A mesh that passes every topology check can
> still be the wrong part. Topology says "this is a valid solid", not "this is
> the solid you meant". Always check volume against a closed-form expectation -
> and be most suspicious when it matches the *simpler* shape.

#### C5 - Added material escaping the silhouette

**Symptom.** The rendered top view showed 8 bumps interrupting the top chamfer;
max radius at z = 43.99 was 15.10 where the chamfer should have given 14.81.

**Cause.** Ridge stock sat comfortably inside the straight wall - but not inside
the chamfered part of it.

**Fix.** `intersection(ridges, outer_solid())`.

> **Pattern.** "It's inside the wall" is only true where the silhouette is at
> full size. Clip added features against the silhouette solid instead of
> reasoning about whether they fit; it is one line and it is unconditional.

#### C6 - A verification artifact that looked like a defect

**Symptom.** Cross-sections at z = 2.5 and z = 7.5 reported no ridge protrusion.

**Cause.** Not the model. Those planes are exactly where ridge segments meet, so
the mesh has a ring of vertices *at* that Z and the strict crossing test
`(z1-z)(z2-z) < 0` saw nothing.

**Fix.** Sample away from junction planes.

> **Pattern.** Sample cross-sections at heights that are not feature boundaries.
> When a measurement disagrees with the model, check the instrument before
> changing the part.
>
> **This recurred in rev B** - a probe at z = 41.000, exactly where the ridge
> cylinder meets its taper cone, reported the crest at +1.898 mm (it had missed
> the ridge entirely and hit the outer wall). z = 41.001 reported +0.000.
> The pattern was already written down, which is the only reason it cost
> seconds instead of an afternoon.

### Session 2 - elliptical rev B

#### C7 - Offsetting an ellipse is not scaling an ellipse

**Symptom.** Caught in design, not in the mesh. Unlike C9 this one does bite at
this eccentricity: the bore would have been 0.03 mm loose on the major
semi-axis (0.06 mm on the diameter) and the wall would have varied by 0.14 mm
around the section - a 9% swing on a 1.5 mm wall.

**Cause.** The obvious way to grow a 29 x 27 ellipse by 0.4 mm is to scale it.
Scaling is *proportional*: the factor that grows the 13.5 mm semi-axis by 0.4
(1.0296...) grows the 14.5 mm semi-axis by 0.43. A scaled ellipse is a
different ellipse, not a parallel curve. The error grows linearly with the
offset - at the 1.9 mm outer offset the wall would have come out 1.9 mm on the
minor axis and 2.04 mm on the major, a 0.14 mm variation around the section.

**Fix.** 2D `offset(r=d)`, which is a true parallel curve (an exact Minkowski
sum with a disc). For a convex profile it is exact everywhere. Every dimension
in the part is now `offset(nominal, d)` for some d - clearance, wall, chamfers
and ridge axes all come off the same base curve.

> **Pattern.** Scaling changes proportions; offsetting changes size at constant
> wall thickness. Anything that is a *thickness* - a clearance, a wall, a
> chamfer, a gap - must be an offset. Reach for `scale()` only when you actually
> want the shape to get proportionally fatter.
>
> Corollary: the true offset of an ellipse is not an ellipse at all (it is a
> higher-order curve), so there is no "correct semi-axis" to compute. Don't try;
> let `offset()` do it.

#### C8 - No axis of revolution means chamfers need a different primitive

**Symptom.** The rev A silhouette-revolve pattern (C1) simply does not apply.

**Cause.** `rotate_extrude` needs an axis of revolution. `linear_extrude(scale=)`
is the usual substitute and is wrong here for exactly the C7 reason - its scale
is proportional, so a "0.6 mm" chamfer would be 0.6 on one axis and 0.64 on the
other.

**Fix.** A chamfer is the hull of two offset profiles at two heights:

    hull() {
        translate([0,0,z0])       linear_extrude(e) ell(off0);
        translate([0,0,z1 - e])   linear_extrude(e) ell(off1);
    }

Both sections are convex, so the hull is exactly the ruled surface between them.
Verified: over the 0.6 mm top chamfer the part loses 1.2 mm on X *and* 1.2 mm on
Y - a true uniform 45 deg break.

> **Pattern.** Axisymmetric -> revolve a profile. Not axisymmetric -> stack
> `prism()` and `hull()`-of-two-offsets `taper()` sections. Two primitives cover
> every chamfer, lip and draft, and both are exact for convex sections.
>
> Known approximation: the taper interpolates over `z1 - z0 - 2e` rather than
> `z1 - z0`, so with e = 0.001 the chamfer angle is off by 0.3%. Measured
> 31.207 mm where 31.200 was ideal. Bounded, documented, and 20x below print
> resolution - but it is an approximation, not an identity.

#### C9 - The normal of an ellipse is not radial

**Symptom.** Caught in design, and - unlike C1-C5 - it would *not* have hurt
this particular part. Worth recording precisely because the size of the error
is not obvious from the size of the angle.

**Cause.** On a circle the outward normal is the radial direction, so rev A
could place ridges at `[r, 0]` rotated by `i*45`. On an ellipse the normal at
parameter t is `grad(x^2/a^2 + y^2/b^2) = (cos t / a, sin t / b)`, which
diverges from the radial direction everywhere except the four extremes - by up
to **4.09 deg** here, worst at t = 45.

But standoff error is a *cosine* of that angle, so it is second order:

| section | max normal-vs-radial | standoff error at 0.8 mm |
|---|---|---|
| 29 x 27 (this part) | 4.09 deg | 0.002 mm |
| 30 x 20 | 22.6 deg | 0.062 mm |
| 40 x 20 | 36.9 deg | 0.160 mm |
| 50 x 10 | 67.4 deg | 0.492 mm |

At 0.002 mm, radial placement would have been indistinguishable in this part -
two orders of magnitude below print resolution. At 40 x 20 it would have eaten
40% of the interference on the diagonal ridges.

**Fix.** Explicit normal maths - correct at any eccentricity, and no more code
than the radial version:

    function ell_nrm(t)    = let (v = [cos(t)/a, sin(t)/b]) v / norm(v);
    function ell_off(t, d) = ell_pt(t) + d * ell_nrm(t);

Verified by the fit probe: all 8 crests sit within 0.006 mm of the nominal
ellipse, not just the ones on the axes.

> **Pattern.** Any "stand this feature off the surface by d" placement needs the
> surface normal; radial position is only the normal on a circle or a sphere.
> Use the normal unconditionally - it is the same amount of code and it stops
> being negligible without warning as the section gets more eccentric.
>
> **Meta-pattern.** Quantify before claiming a defect matters. The angle here
> looked alarming (4 deg) and the consequence was 0.002 mm. An error that is
> real but negligible is worth fixing quietly; it is not worth reporting as a
> near-miss, and writing it up as one would have put a false lesson in this
> document.

#### C10 - The picture came from a different evaluator than the file

**Symptom.** The top view rendered as a solid disc and the iso view showed the
socket capped by a speckled, z-fighting membrane. Meanwhile the exported STL was
watertight, one shell, right volume, and the fit probe found an open bore at
every height. Two sources flatly contradicting each other.

**Cause.** `openscad -o out.png` renders in **OpenCSG preview** mode, not CGAL.
Preview approximates nested difference/hull/offset trees and z-fights on
coincident faces. The STL export always goes through CGAL. So the image was of
a different (approximate) evaluation than the file being shipped.

**Fix.** `openscad --render -o out.png ...` forces CGAL. The socket appeared
immediately, open and correct.

> **Pattern.** Always `--render` for any image you intend to *inspect*. An image
> from a different evaluator than the export is not evidence about the export -
> it can invent defects (as here) and it can equally well hide them.
>
> **Meta-pattern.** When two verification channels disagree, do not pick the
> scarier one and start editing. Find out which instrument is lying. Here the
> numbers were right and the picture was wrong; in C6 the picture was fine and
> the probe was wrong. Both times the model was innocent.

---

## 7. Checklist for future OpenSCAD parts

**Construction**

1. Is the part axisymmetric? Revolve a 2D profile; chamfers are profile
   vertices. (C1)
2. If not: stack `prism()` sections and `hull()`-of-two-offsets tapers. (C8)
3. Thickness-like dimensions (clearance, wall, chamfer, gap) are `offset()`,
   never `scale()`. (C7)
4. Standing a feature off a surface? Use the real surface normal, not the
   radial direction. (C9)
5. Cutters cross transversally and overshoot; never tangent, never
   eps-offset. (C2)
6. `eps` on the extrusion axis only - never on a radius or a wall. (C3)
7. Order booleans so inward-protruding features are added *after* the cut. (C4)
8. Clip added features against the silhouette solid. (C5)

**Verification** (~10 seconds of compute; caught 8 defects that produced
slicer-acceptable STLs)

9. Check `Simple: yes` / `Volumes: 2` in the OpenSCAD console.
10. Mesh integrity: manifold, single shell, outward normals. (C2, C3)
11. Volume against a hand calculation - topology cannot catch a wrong part. (C4)
12. Measure the fit-critical dimensions in the *exported mesh*, off feature
    boundaries. (C6)
13. Render with `--render` and actually look, including a section view. (C5, C10)
14. When two channels disagree, debug the instrument first. (C6, C10)
15. Emit a small test coupon from the same parameters for anything with a fit.

---

## 8. Tuning

`clearance` is the single knob; the crest locus is `offset(nominal, clearance - ridge_h)`.

| clearance | crest locus | fit |
|---|---|---|
| 0.3 | 0.1 mm inside nominal | firm press fit |
| 0.4 | on nominal - as designed | snug |
| 0.5 | 0.1 mm outside nominal | slip fit |

Print `fit_test_ring.stl` (10 mm, ~10 min) before committing to the foot.

## 9. Printing

Open end up, flat on the bed, no supports - every overhang is a 45 deg chamfer
or a taper. 4+ perimeters: at 1.5 mm the wall is only ~4 lines at 0.4 mm, and
the ridges want to be solid rather than thin-wall gap fill. Solid infill for the
4 mm floor.

## 10. Open items

- **A1 / stability.** 32.8 x 30.8 x 44 mm is a tall, narrow footprint. If the
  foot is free-standing it wants a flared or disc base. Awaiting a decision.
- **Not yet printed.** Everything above is mesh-verified, not fit-verified. The
  crest locus is theory until the test ring meets a real pole.
- **Pole section assumed a true ellipse.** If it is actually a stadium/oval
  (two arcs joined by straights) or a rounded rectangle, the base profile
  changes but nothing else does - every other dimension is an offset of it.
