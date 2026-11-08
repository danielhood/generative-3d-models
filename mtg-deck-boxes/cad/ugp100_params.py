"""Ultra Guard Pro 100+ deck box -- design parameters recovered from the
source STLs in mtg-deck-boxes/orig/.

The originals turned out to be a clean design that was then NON-UNIFORMLY
SCALED, which is why almost every measured number is ugly and every number
divided by the scale factor below is round:

    base design   76 x 72 mm exterior, 4.0 wall, 68 x 64 interior,
                  2.2 / 1.8 wall split at the lip, r2.0 exterior corners,
                  r0.5 edge fillets, seam plane at exactly 30 deg
    scaled by     sx = 1.0294 in x, sy = 1.1953 in y, 1.0 in z
    which is      70.0 / 68  and  76.5 / 64  -- i.e. the scale was chosen to
                  land the *interior* on 70.0 x 76.5 mm, the dimension that
                  has to fit the cards.

Everything here is in the rebuild's own frame:
  * x and y centred on the box axis
  * z = 0 at the exterior underside of the bottom part
  * the two parts share this frame, so bottom + top is the assembly
"""
import math

# ---- the original's scale factors (kept so the base numbers stay readable) --
SX = 1.0294
SY = 1.1953

# ---- footprint -------------------------------------------------------------
EXT_HX = 38.0 * SX          # 39.1172   exterior half-width  (78.2344 overall)
EXT_HY = 36.0 * SY          # 43.0308   exterior half-depth  (86.0616 overall)
INT_HX = 34.0 * SX          # 34.9996   interior half-width  -> 69.9992 ~ 70.0
INT_HY = 32.0 * SY          # 38.2496   interior half-depth  -> 76.4992 ~ 76.5
WALL_X = EXT_HX - INT_HX    #  4.1176
WALL_Y = EXT_HY - INT_HY    #  4.7812

# ---- heights ---------------------------------------------------------------
FLOOR_T   = 4.0             # bottom part's floor
CEIL_T    = 4.0             # top part's ceiling
H_TOTAL   = 102.05          # assembled exterior height
Z_CEIL    = H_TOTAL - CEIL_T    # 98.05  interior ceiling
INT_H     = Z_CEIL - FLOOR_T    # 94.05  interior height (critical: card length)

# ---- the slanted seam ------------------------------------------------------
# 30 deg in the base design; the y scale flattens it in the finished part.
SEAM_TAN   = math.tan(math.radians(30.0)) / SY   # 0.483017041
SEAM_ANGLE = math.degrees(math.atan(SEAM_TAN))   # 25.781334 deg
SEAM_COS   = 1.0 / math.sqrt(1.0 + SEAM_TAN ** 2)
SEAM_SIN   = SEAM_TAN * SEAM_COS
# height of the seam plane on the box axis (y = 0); it rises toward +y
Z_SEAM = 48.038960
# seam plane: z = Z_SEAM + y * SEAM_TAN ; upward normal:
SEAM_N = (0.0, -SEAM_SIN, SEAM_COS)

# ---- the lip / groove ------------------------------------------------------
LIP_H  = 6.0                        # lip stands this far (vertically) above the seam
Z_LIP  = Z_SEAM + LIP_H             # lip-top plane, parallel to the seam
LIP_HX = (38.0 - 2.2) * SX          # 36.852520  lip outer face
LIP_HY = (36.0 - 2.2) * SY          # 40.401140
LIP_T_X = LIP_HX - INT_HX           #  1.852920  lip thickness (inner face = interior wall)
LIP_T_Y = LIP_HY - INT_HY           #  2.151540
# Clearance between the bottom's lip and the top's groove.  MEASURED from the
# original pair, not a round design value -- it is different on the two axes
# and is what makes the "-tight" top tight.  Keeping the measured values means
# a rebuilt half still mates with an original half.
CLEAR_X = 0.011760
CLEAR_Y = 0.078127
GROOVE_HX = LIP_HX + CLEAR_X        # 36.864280
GROOVE_HY = LIP_HY + CLEAR_Y        # 40.479267

# ---- lead-in bevel at the groove mouth -------------------------------------
# A 45 deg chamfer where the groove's walls meet the top's seam face, so the
# lip is funnelled in instead of having to be lined up before it will enter.
# The original carries 0.4 x 0.4 here; 0.6 trades a little more of the seam
# land (2.25 / 2.55 mm wide) and of the lip's full-width engagement (6.0 mm)
# for more capture.  Both legs are equal, measured from the corner along the
# wall and along the seam face.
MOUTH_CHAMFER = 0.6
# how far each cutter is pushed past the corner into open space, so no cutter
# face is ever coincident with a face of the part
CHAMFER_OVER = 1.0

# ---- snap bumps and dents ---------------------------------------------------
# The lid is held shut by four small domes on the bottom's lip, two on each x
# face (one toward the front, one toward the back), that seat in matching
# dimples in the top's groove walls.  The lip is 0.012 mm inside the groove, so
# each dome's ~0.77 mm height is real interference while the lid slides over it:
# the walls flex, and the dome clicks into the dimple.  Without them nothing
# keeps the halves together.
#
# Both are spherical caps.  In the unscaled base design the bump is a cap of a
# 1.5 mm sphere, 0.75 high (base radius sqrt(1.5^2 - 0.75^2) = 1.299 -- that is
# where the odd-looking 1.299 comes from); the non-uniform scale then makes its
# base 1.553 (y) x 1.299 (z) and 0.772 high.  The dimple is a cap of a ~1.70 mm
# sphere with a CIRCULAR 1.433 mm mouth, i.e. it was made after the scaling and
# not scaled with the rest.  SolveSpace has no non-uniform scale, so the bump is
# built as a circular cap that keeps the two dimensions that govern the click:
#   - its HEIGHT, 0.7721, and
#   - its base radius IN z, 1.299, which sets the profile along the direction
#     the lid slides (vertical), so how hard it is to get over is unchanged.
# What is lost is the 0.25 mm of extra width in y each side, a little contact
# area along the wall.  The dimple is reproduced exactly.
BUMP_H = 0.7721
BUMP_BASE_R = 1.299
BUMP_SPHERE_R = (BUMP_BASE_R ** 2 + BUMP_H ** 2) / (2 * BUMP_H)       # 1.4788
DENT_DEPTH = 0.7857               # 0.7869 left, 0.7845 right in the source
DENT_MOUTH_R = 1.433
DENT_SPHERE_R = (DENT_MOUTH_R ** 2 + DENT_DEPTH ** 2) / (2 * DENT_DEPTH)  # 1.6998
# Where the dimple's apex is further out than the bump's, in the assembled
# pair: the gap the dome has to seat into.  Measured 0.0254 in the source.
#   (GROOVE_HX + DENT_DEPTH) - (LIP_HX + BUMP_H)
# Centres, (y, z) in this frame, identical on the left and right faces.  The
# source's dimples are coaxial with its domes to within 0.031 mm (dy <= 0.009,
# dz +-0.031), so one set of positions serves both.  They are NOT quite on a
# line parallel to the seam (2.505 and 2.809 mm above it), which is why they
# are listed rather than derived.
SNAP_POINTS = ((-31.7434, 35.2115),     # toward the front (-y)
               (33.8296, 67.1883))      # toward the back (+y)

# ---- engraved label on the bottom's front face ------------------------------
# Text is cut INTO the exterior face of the front (-y) wall, inside a centred
# PANEL_W x PANEL_H panel, TEXT_DEPTH deep.  "Front" is the low, wide face --
# the one the seam is lowest at -- which is 78.2 x 27.25 mm, so a 70 x 20 panel
# sits in it at the same proportions with a 3.6 mm margin above and below.
# (The opposite wide face is 74.5 mm tall at the top of its wall.)
#
# The text is scaled to be as large as fits the panel: for "MTG" the HEIGHT is
# what binds, not the width (ink 2.84 x 1.04 cap-heights against a 3.5 : 1
# panel), so it fills the 20 mm and sits 54.7 mm wide inside the 70.  A longer
# string would flip that and be width-limited, and the fit below handles both.
TEXT = "Spock"
# SolveSpace's own bundled Bitstream Vera Sans: guaranteed to resolve on any
# install, where a system font that is missing draws a big X, and a close
# Verdana relative (wide, open, large x-height).  Verdana itself is not
# installable here and is not redistributable.
TEXT_FONT = "BitstreamVeraSans-Roman-builtin.ttf"
PANEL_W = 70.0
PANEL_H = 20.0
TEXT_DEPTH = 3.0
# the wall is WALL_Y thick; the pocket must leave enough that it still prints as
# a solid wall.  1.2 mm is three 0.4 mm perimeters.
MIN_WALL_BEHIND_TEXT = 1.2
assert WALL_Y - TEXT_DEPTH >= MIN_WALL_BEHIND_TEXT, \
    "text pocket leaves only %.2f mm of wall" % (WALL_Y - TEXT_DEPTH)
# the panel is centred on the front face, whose height is the seam's height at
# the front edge
Z_FRONT_TOP = Z_SEAM - EXT_HY * SEAM_TAN
PANEL_ZC = Z_FRONT_TOP / 2.0
TEXT_LEAD = 1.0             # the cutter starts this far outside the face

# ---- cosmetic rounding -----------------------------------------------------
# The original's exterior corner is an ELLIPSE (r2.0 scaled: 2.0588 x 2.3906)
# and its horizontal perimeter edges carry a 2.0 round.  SolveSpace has no 3D
# fillet and no sweep, so: the vertical corners get one circular radius and the
# horizontal perimeter edges are left sharp.  Both are aesthetic only.
EXT_CORNER_R = 2.2          # vs 2.0588 x 2.3906 in the original
LIP_CORNER_R = 0.55         # vs 0.5147 x 0.5976
# The top's groove corners are left sharp, which relieves them relative to the
# lip's rounded corners -- the original relieves its groove corners too.

# ---- build margins (how far "past the part" the cutting prisms reach) ------
OVER = 12.0
