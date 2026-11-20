"""Dimensions of the SLOT-AND-TAB divider and its short test base.

The first printed test of the adjustable case (square holes, dividers with arms)
showed: the arms had to be pushed into the holes and were flexible at 1.6 mm, the
divider body could bind between the walls, and the base took about 24 h because of
the 60 mm deep holes.  Dividers held by their TABS alone in the 3 mm slits, with the
arms removed, slotted in nicely.  This is that idea made the design:

  * no holes and no arms;
  * the slits become vertical SLOTS cut into the lane faces, 25 mm deep from the
    wall top (they were 3 mm), at a 6 mm pitch (was 4 mm);
  * the divider's tabs are 25 mm tall, so each tab slides down a slot and the
    divider hangs on its tab bottoms, vertical;
  * the divider body is 0.4 mm off each lane face (was 0.2);
  * the slot width (2.0) and the tab thickness (1.6) are unchanged: they fitted.

A partition serves the lane on each side, and a 3.5 mm slot from both faces of a
5 mm wall at the same position would cut it through.  So the two faces' slots are
STAGGERED by half the pitch: set A (lanes 1 and 3) and set B (lane 2) are 3 mm apart,
and the wall keeps 1.5 mm behind every slot.

This is only the TEST: one divider, and a short base holding the two partition walls
of the middle lane, with no front or back wall and a 1 mm floor.  The full tray and
lid are not changed here.  Shared dimensions come from the adjustable case's
`case_params.py`.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "cad"))
import case_params as M              # M for the adjustable case (the main one)

LANE_W = M.LANE_W                    # 69.9992
WALL_T = M.WALL_T                    # 5.0
WALL_TOP = M.WALL_TOP               # 73.4034: the lane walls' top, and the tabs' top
FLOOR_T_REAL = M.FLOOR_T            # 4.0: the real tray's floor (the divider is built for it)
OVER = M.OVER

# ---- the slots ------------------------------------------------------------
SLOT_W = 2.0                         # along y; unchanged from the slits
SLOT_DEPTH = 3.5                     # into the wall from the lane face; leaves 1.5 of a 5 mm wall
SLOT_H = 25.0                        # from the wall top down
SLOT_PITCH = 6.0                     # positions along y (was 4)
STAGGER = SLOT_PITCH / 2.0           # set B is this far along from set A
SKIN = WALL_T - SLOT_DEPTH           # 1.5: what is left of the wall at a slot
SLOT_FLOOR = WALL_TOP - SLOT_H       # 48.4034

# ---- the divider -----------------------------------------------------------
DIV_T = 1.6                          # plate and tab thickness (y); unchanged
TAB_REACH = 3.2                      # how far a tab goes into the wall from the lane face
TAB_GAP = SLOT_DEPTH - TAB_REACH     # 0.3: the tab stops short of the slot's bottom
TAB_H = SLOT_H                       # the tab is as tall as the slot: it hangs on its bottom
BODY_CLEAR = 0.4                     # the body is this much narrower than the lane, per side
DIV_ABOVE = 12.0                     # the body stands this far above the wall top
DIV_FLOOR_CLEAR = 0.5                # the body's bottom is this far above the REAL floor
DIV_BODY_HX = LANE_W / 2.0 - BODY_CLEAR
DIV_TAB_OUT = LANE_W / 2.0 + TAB_REACH
DIV_BOTTOM = FLOOR_T_REAL + DIV_FLOOR_CLEAR
DIV_TOP = WALL_TOP + DIV_ABOVE
DIV_TAB_BOTTOM = WALL_TOP - TAB_H
assert TAB_GAP > 0 and SKIN > 0

# ---- the test base ---------------------------------------------------------
TEST_FLOOR_T = 1.0                   # the real floor is 4; this only has to hold the walls
TEST_HY = 24.0                       # half the length: no front or back wall
TEST_WALL_BASE = 0.5                 # the walls run down into the floor to here
# lane 2's own slots (set B): six, symmetric about y = 0, centred between set A's
B_YS = [(k - 2.5) * SLOT_PITCH for k in range(6)]             # -15 .. +15
# the walls' outer faces carry set A, as the lane 1 and 3 faces would in the real case
A_YS = [B_YS[0] - STAGGER + k * SLOT_PITCH for k in range(7)]   # -18 .. +18
WALL_CX = LANE_W / 2.0 + WALL_T / 2.0                         # the partitions' centres, at +-37.4996
