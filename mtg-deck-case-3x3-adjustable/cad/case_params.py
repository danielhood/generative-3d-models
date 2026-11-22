"""Dimensions of the adjustable 3-lane deck case: a tray, a lid, and one divider
that can be placed anywhere along any lane.

This case is the 3 x 3 case (`mtg-deck-case-3x3/`) rethought: instead of nine fixed
slots, three LANES run the whole depth, and thin dividers are dropped in wherever a
section should end.  The outer shell is unchanged: the single deck box's walls,
lip, groove, clearances, snap domes and mouth bevel, and the 3 x 3 case's finger
ledge, are all reused, and all of those printed well.  What is new is inside.

  * Four 5 mm LANE WALLS run front to back: two partitions between the lanes and a
    LINER against each outer wall.  (The outer walls carry the snap lip, which is
    1.85 mm thick and cannot hold a slot, so the liner sits inside it and the outer
    shell stays exactly as it was.)
  * Each lane wall has vertical SLOTS cut into its lane faces, 25 mm deep from the wall
    top, 2 mm wide, 3.5 mm into the wall, every 6 mm.  Below the slots the lane faces
    are smooth.
  * The two faces of a partition are STAGGERED: lane 2's slots are 3 mm along from
    lanes 1 and 3's, so a 5 mm wall keeps 1.5 mm behind every slot (3.5 + 3.5 mm from
    both faces at one position would cut it through).
  * The DIVIDER is a flat 1.6 mm plate with a 25 mm TAB at each top corner.  Each tab
    slides down a slot and the divider hangs on its tab bottoms, vertical, with its top
    12 mm above the walls.  (An earlier design held it by arms in square holes; the
    printed test found the arms tight and flexible and the base very slow to print, and
    the tabs alone fitted well.  That design is in `archive/holes-and-arms/`.)

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

# ---- the slots ------------------------------------------------------------------
SLOT_W = 2.0                         # along y
SLOT_DEPTH = 3.5                     # into the wall from the lane face: leaves 1.5 of a 5 mm wall
SLOT_H = 25.0                        # from the wall top down
SLOT_PITCH = 6.0                     # positions along y
STAGGER = SLOT_PITCH / 2.0           # lane 2's slots (set B) are this far along from set A
SKIN = WALL_T - SLOT_DEPTH           # 1.5: what is left of the wall at a slot
SLOT_FLOOR = WALL_TOP - SLOT_H       # 48.4: the slots' bottom, where a tab rests
SLOT_MARGIN = 2.0                    # the end slots stay this far from the front/back walls
# Set A (lanes 1 and 3) is symmetric about y = 0 with a slot AT 0; set B (lane 2) has one
# more, centred between: so B = A shifted by half a pitch and extended by one.
N_A = int((2 * IN_HY - 2 * SLOT_MARGIN - SLOT_W) // SLOT_PITCH)
if N_A % 2 == 0:
    N_A -= 1                         # odd, so there is a slot at y = 0
N_B = N_A + 1
A_YS = [(k - (N_A - 1) / 2.0) * SLOT_PITCH for k in range(N_A)]              # -108 .. +108 (37)
B_YS = [(k - (N_B - 1) / 2.0) * SLOT_PITCH for k in range(N_B)]              # -111 .. +111 (38)
assert B_YS[-1] + SLOT_W / 2.0 <= IN_HY - SLOT_MARGIN + 1e-9
# the six lane faces that carry slots: (x of the face, which way the wall lies from it: +1
# towards +x, -1 towards -x, which set).  Lanes 1 and 3 use set A, lane 2 set B.
SLOT_FACES = [
    (-IN_HX + WALL_T, -1, "A"),                       # the left liner, its lane-1 face
    (-LANE_W / 2.0 - WALL_T, +1, "A"),                # the left partition, its lane-1 face
    (-LANE_W / 2.0, -1, "B"),                         # the left partition, its lane-2 face
    (LANE_W / 2.0, +1, "B"),                          # the right partition, its lane-2 face
    (LANE_W / 2.0 + WALL_T, -1, "A"),                 # the right partition, its lane-3 face
    (IN_HX - WALL_T, +1, "A"),                        # the right liner, its lane-3 face
]

# ---- the divider ---------------------------------------------------------------
DIV_T = 1.6                          # plate and tab thickness (y)
TAB_REACH = 3.2                      # how far a tab goes into the wall from the lane face
TAB_GAP = SLOT_DEPTH - TAB_REACH     # 0.3: the tab stops short of the slot's bottom
TAB_H = SLOT_H                       # the tab is as tall as the slot: it hangs on its bottom
BODY_CLEAR = 0.8                     # the body is this much narrower than the lane, per side (0.2, then 0.4 in the
                                     # slot test; 0.8 here, with the tabs 0.4 longer so they still reach 3.2 into the wall)
DIV_ABOVE = 12.0                     # the body stands this far above the wall top
DIV_FLOOR_CLEAR = 0.8                # the body's bottom is this far above the floor (0.5 in the slot test's design)
DIV_BODY_HX = LANE_W / 2.0 - BODY_CLEAR
DIV_TAB_OUT = LANE_W / 2.0 + TAB_REACH
DIV_BOTTOM = FLOOR_T + DIV_FLOOR_CLEAR
DIV_TOP = WALL_TOP + DIV_ABOVE
DIV_TAB_BOTTOM = WALL_TOP - TAB_H
assert TAB_GAP > 0 and SKIN > 0
assert DIV_TOP < Z_CEIL                                   # the lid clears the divider
assert DIV_TAB_BOTTOM > DIV_BOTTOM                        # the tabs are on the upper part of the body

# ---- the snap domes and dimples: the 3 x 3 case's, centred on the lanes -------
BUMP_H, BUMP_SPHERE_R = B.BUMP_H, B.BUMP_SPHERE_R
DENT_DEPTH, DENT_SPHERE_R = B.DENT_DEPTH, B.DENT_SPHERE_R
_above = [z - (B.Z_SEAM + B.SEAM_TAN * y) for (y, z) in B.SNAP_POINTS]
DOME_ABOVE_SEAM = sum(_above) / len(_above)       # 2.657
DOME_Z = Z_S + DOME_ABOVE_SEAM
SNAP_CENTRES_X = LANE_CENTRES_X                   # front and back faces: one per lane
SNAP_CENTRES_Y = [-(SLOT_Y + _LEGACY_DIVIDER), 0.0, SLOT_Y + _LEGACY_DIVIDER]   # left and right faces, as before
