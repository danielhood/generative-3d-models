"""Dimensions of the adjustable 3-lane deck case: a tray, a lid, and one divider
that can be placed anywhere along any lane.

This case is the 3 x 3 case (`mtg-deck-case-3x3/`) rethought: instead of nine fixed
slots, three LANES run the whole depth, and thin dividers are dropped in wherever a
section should end.  The outer shell is unchanged: the single deck box's walls,
lip, groove, clearances, snap domes and mouth bevel, and the 3 x 3 case's finger
ledge, are all reused, and all of those printed well.  What is new is inside.

  * Four 5 mm LANE WALLS run front to back: two partitions between the lanes and a
    LINER against each outer wall.  (The outer walls carry the snap lip, which is
    1.85 mm thick and cannot hold a hole, so the liner sits inside it and the outer
    shell stays exactly as it was.)
  * Each lane wall has a column of vertical square HOLES in its middle, at a fixed
    pitch, and over each hole a SLIT through the lane-side skin, 3 mm deep.  The
    lane faces stay smooth below the slits.
  * The DIVIDER is a flat 1.6 mm plate with a BRIDGE and an ARM at each top corner:
    the arm goes down the hole, the bridge fills the slit and rests on the skin, and
    the 1.6 mm slot between arm and body takes the 1.5 mm skin.  It hangs from its
    bridges, vertical, with its top 12 mm above the walls.

Frame (the same as the single box and the 3 x 3 case): x and y centred on the case's
axis, z = 0 at the underside of the tray.  x is the width (across the lanes), y the
depth (front to back, along the lanes, the direction a card stack is thick in).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "mtg-deck-boxes", "cad"))
import ugp100_params as B            # B for "the single Box"

# ---- the lanes -------------------------------------------------------------
N_LANES = 3
LANE_W = 2 * B.INT_HX                # 69.9992: one lane, the single box's cavity width
WALL_T = 5.0                         # the four lane walls: 2 partitions + 2 liners
SLOT_Y = 2 * B.INT_HY                # 76.4992, the single box's cavity depth

# The interior depth is the 3 x 3 case's, unchanged: three single-box depths and the
# two 1.6 mm dividers that case had between them.
_LEGACY_DIVIDER = 1.6
IN_HY = (3 * SLOT_Y + 2 * _LEGACY_DIVIDER) / 2.0              # 116.3488
IN_HX = (N_LANES * LANE_W + 4 * WALL_T) / 2.0                 # 114.9988
WALL_X, WALL_Y = B.WALL_X, B.WALL_Y                           # the outer walls: 4.1176, 4.7812
EXT_HX, EXT_HY = IN_HX + WALL_X, IN_HY + WALL_Y               # 119.1164, 121.13
EXT_CORNER_R = B.EXT_CORNER_R

LANE_PITCH = LANE_W + WALL_T                                  # lane centre to lane centre
LANE_CENTRES_X = [(k - (N_LANES - 1) / 2.0) * LANE_PITCH for k in range(N_LANES)]
# the four lane walls, left to right: (x of the lane-side face(s), "liner-l" | "part" | "liner-r")
WALL_CENTRES_X = [-IN_HX + WALL_T / 2.0, -LANE_W / 2.0 - WALL_T / 2.0,
                  LANE_W / 2.0 + WALL_T / 2.0, IN_HX - WALL_T / 2.0]
WALL_KINDS = ["liner-l", "part", "part", "liner-r"]

# ---- the lip, groove, bevel: the single box's -------------------------------
LIP_H = B.LIP_H
LIP_HX, LIP_HY = IN_HX + B.LIP_T_X, IN_HY + B.LIP_T_Y
LIP_CORNER_R = B.LIP_CORNER_R
CLEAR_X, CLEAR_Y = B.CLEAR_X, B.CLEAR_Y
GROOVE_HX, GROOVE_HY = LIP_HX + CLEAR_X, LIP_HY + CLEAR_Y
MOUTH_CHAMFER = B.MOUTH_CHAMFER
CHAMFER_OVER = B.CHAMFER_OVER

# ---- the finger ledge: the 3 x 3 case's ------------------------------------
LEDGE_OUT = 3.0                      # how far it stands proud of the front wall
LEDGE_H = 2.0                        # how thick it is (z)
LEDGE_SPAN_FRAC = 2.0 / 3.0          # of the case's width, measured at the wall
LEDGE_ARC_SAG = 6.0                  # the underlying arc's height; sets the flat's width
LEDGE_OVERLAP = 1.0                  # how far its profile runs into the wall, to join it
LEDGE_HX = LEDGE_SPAN_FRAC * EXT_HX
_R0 = (LEDGE_HX ** 2 + LEDGE_ARC_SAG ** 2) / (2.0 * LEDGE_ARC_SAG)
LEDGE_FLAT_HX = ((_R0 ** 2) - (_R0 - LEDGE_ARC_SAG + LEDGE_OUT) ** 2) ** 0.5
LEDGE_FLANK_R = ((LEDGE_HX - LEDGE_FLAT_HX) ** 2 + LEDGE_OUT ** 2) / (2.0 * LEDGE_OUT)
assert LEDGE_OUT < LEDGE_ARC_SAG
assert LEDGE_HX < EXT_HX - EXT_CORNER_R

# the print bed
BED = 250.0
assert 2 * EXT_HX < BED and 2 * EXT_HY + LEDGE_OUT < BED, (
    "the case is %.2f x %.2f mm; the bed is %.0f" % (2 * EXT_HX, 2 * EXT_HY + LEDGE_OUT, BED))

# ---- heights: the 3 x 3 case's ----------------------------------------------
TRAY_H = B.Z_LIP + B.LIP_HY * B.SEAM_TAN          # 73.5534
Z_LIP = TRAY_H
Z_S = TRAY_H - LIP_H
FLOOR_T, CEIL_T, INT_H = B.FLOOR_T, B.CEIL_T, B.INT_H
H_TOTAL = FLOOR_T + INT_H + CEIL_T                # 102.05
Z_CEIL = H_TOTAL - CEIL_T
LID_H = H_TOTAL - Z_S

# The lane walls stop just under the lip top; the lid's hang to just over the groove
# roof; so a 0.30 mm gap where they meet, and the lip and roof own the seam.  (The
# gap also keeps the walls' tops off the lip's top plane: coplanar faces in a
# boolean are what these handle worst.)
DIV_GAP = 0.15
WALL_TOP = Z_LIP - DIV_GAP                        # the tray's lane walls, and the bridges' top
LID_WALL_BOTTOM = Z_LIP + DIV_GAP
WALL_BASE_Z = 1.0                    # lane walls start inside the floor
WALL_OVERLAP = 1.0                   # how far a wall runs into the outer wall, front and back
OVER = 2.0                           # how far a cutter reaches past a part, where it does not matter

# ---- the holes and slits ------------------------------------------------------
HOLE = 2.0                           # square, centred in the wall
SKIN = (WALL_T - HOLE) / 2.0         # 1.5: the wall either side of a hole
HOLE_PITCH = 4.0                     # centre to centre along y
HOLE_DEPTH = 60.0                    # from the wall top
SLIT_H = 3.0                         # the slit is the top 3 mm of the lane-side skin
SLIT_W = HOLE                        # along y, the same as the hole
HOLE_MARGIN = 2.0                    # the end holes stay this far from the front/back walls
HOLE_N = int((2 * IN_HY - 2 * HOLE_MARGIN - HOLE) // HOLE_PITCH) + 1     # 57
HOLE_Y0 = -(HOLE_N - 1) / 2.0 * HOLE_PITCH                               # -112.0: symmetric
HOLE_YS = [HOLE_Y0 + k * HOLE_PITCH for k in range(HOLE_N)]
assert HOLE_Y0 - HOLE / 2.0 > -IN_HY + HOLE_MARGIN - 1e-9
HOLE_BOTTOM = WALL_TOP - HOLE_DEPTH               # 13.4

# ---- the divider ---------------------------------------------------------------
DIV_T = 1.6                          # plate thickness, y
ARM_W = 1.6                          # arm width, x (and its thickness, y: the same extrude)
ARM_LEN = 58.0                       # from the wall top: 2 mm short of the hole's bottom
BRIDGE_H = SLIT_H                    # fills the slit exactly, so the top is flush and it hangs
SKIN_GAP = 1.6                       # lane face to the arm's lane-side face: holds the 1.5 skin
BODY_CLEAR = 0.2                     # the body is this much narrower than the lane, per side
DIV_ABOVE = 12.0                     # the body stands this far above the wall top
DIV_FLOOR_CLEAR = 0.5                # the body's bottom is this far above the floor
DIV_BODY_HX = LANE_W / 2.0 - BODY_CLEAR
DIV_ARM_IN = LANE_W / 2.0 + SKIN_GAP          # the arm's lane-side face, from the lane's axis
DIV_ARM_OUT = DIV_ARM_IN + ARM_W
DIV_BOTTOM = FLOOR_T + DIV_FLOOR_CLEAR
DIV_TOP = WALL_TOP + DIV_ABOVE
DIV_BRIDGE_BOTTOM = WALL_TOP - BRIDGE_H
DIV_ARM_BOTTOM = WALL_TOP - ARM_LEN
assert ARM_LEN < HOLE_DEPTH
assert DIV_ARM_IN > LANE_W / 2.0 + SKIN                   # the arm clears the skin ...
assert DIV_ARM_OUT < LANE_W / 2.0 + SKIN + HOLE           # ... and stays inside the hole
assert DIV_TOP < Z_CEIL                                   # ... and the lid clears the divider

# ---- the snap domes and dimples: the 3 x 3 case's, centred on the lanes -------
BUMP_H, BUMP_SPHERE_R = B.BUMP_H, B.BUMP_SPHERE_R
DENT_DEPTH, DENT_SPHERE_R = B.DENT_DEPTH, B.DENT_SPHERE_R
_above = [z - (B.Z_SEAM + B.SEAM_TAN * y) for (y, z) in B.SNAP_POINTS]
DOME_ABOVE_SEAM = sum(_above) / len(_above)       # 2.657
DOME_Z = Z_S + DOME_ABOVE_SEAM
SNAP_CENTRES_X = LANE_CENTRES_X                   # front and back faces: one per lane
SNAP_CENTRES_Y = [-(SLOT_Y + _LEGACY_DIVIDER), 0.0, SLOT_Y + _LEGACY_DIVIDER]   # left and right faces, as before
