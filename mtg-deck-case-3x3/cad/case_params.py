"""Dimensions of the 3 x 3 deck case: a lid and a tray holding nine of the
Ultra Guard Pro 100+ deck boxes' card slots.

Almost nothing here is a new number.  The case is the single deck box
(`mtg-deck-boxes/`) multiplied: its slot, its outer walls, its lip and groove,
its clearances, its snap domes and its mouth bevel are all IMPORTED from that
box's parameters, so "the outer walls remain the same as the single box" is true
by construction and stays true if the single box is ever retuned.  What is new
is the arrangement: a grid of slots with thin dividers, a FLAT seam (no front-to-
back slope), snap domes on all four sides, and a lid with dividers in one
direction only.

Frame (the same convention as the single box, so the two parts assemble in
place): x and y centred on the case's axis, z = 0 at the underside of the tray;
the lid sits in the same frame, so tray + lid is the assembly.

x is the case's width (left-right), y its depth (front-back, the direction the
card stacks are thick in), z its height.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "mtg-deck-boxes", "cad"))
import ugp100_params as B            # B for "the single Box"

# ---- the grid -------------------------------------------------------------
N_COLS = 3                           # slots across x
N_ROWS = 3                           # slots along y
INNER_T = 1.6                        # divider thickness: 4 x a 0.4 mm extrusion width (3.0 in rev A-C, 1.5 in rev D)

# one slot is exactly the single box's cavity
SLOT_X = 2 * B.INT_HX                # 69.9992
SLOT_Y = 2 * B.INT_HY                # 76.4992
PITCH_X = SLOT_X + INNER_T           # slot centre to slot centre
PITCH_Y = SLOT_Y + INNER_T

# interior of the whole case, then the outside: the single box's walls, unchanged
IN_HX = (N_COLS * SLOT_X + (N_COLS - 1) * INNER_T) / 2.0      # 107.9988
IN_HY = (N_ROWS * SLOT_Y + (N_ROWS - 1) * INNER_T) / 2.0      # 117.7488
WALL_X, WALL_Y = B.WALL_X, B.WALL_Y                           # 4.1176, 4.7812
EXT_HX, EXT_HY = IN_HX + WALL_X, IN_HY + WALL_Y               # 112.1164, 122.53
EXT_CORNER_R = B.EXT_CORNER_R

# the lip on the tray and the groove in the lid: the single box's thicknesses and
# clearances, around the bigger perimeter
LIP_H = B.LIP_H
LIP_HX, LIP_HY = IN_HX + B.LIP_T_X, IN_HY + B.LIP_T_Y
LIP_CORNER_R = B.LIP_CORNER_R
CLEAR_X, CLEAR_Y = B.CLEAR_X, B.CLEAR_Y
GROOVE_HX, GROOVE_HY = LIP_HX + CLEAR_X, LIP_HY + CLEAR_Y
MOUTH_CHAMFER = B.MOUTH_CHAMFER
CHAMFER_OVER = B.CHAMFER_OVER

# ---- the finger ledge -----------------------------------------------------
# A shelf on the FRONT (-y) of each half, to hook fingertips on when the case is too
# wide for one hand to grip across: the lid's is flush with the top of the lid (lift
# from underneath), the tray's flush with the bottom of the tray (press down on top).
# In plan view it is a flat front LEDGE_OUT proud of the wall, running out into two
# tangent arcs that fade to nothing where they meet the wall.  Its width at the wall
# is LEDGE_SPAN_FRAC of the front.  The flat's width comes from the shape first
# proposed: one arc of sagitta LEDGE_ARC_SAG over that span, clipped flat at
# LEDGE_OUT; the corners where it would meet the clip are then rounded by replacing
# the cut-off arc with two arcs tangent to the flat, so there is no corner to catch.
LEDGE_OUT = 3.0                      # how far it stands proud of the front wall
LEDGE_H = 2.0                        # how thick it is (z)
LEDGE_SPAN_FRAC = 2.0 / 3.0          # of the case's width, measured at the wall
LEDGE_ARC_SAG = 6.0                  # the underlying arc's height; sets the flat's width (4.0 at 2 mm out,
                                     # 6.0 at 3 mm keeps the flat about 106 wide)
LEDGE_OVERLAP = 1.0                  # how far its profile runs into the wall, to join it

LEDGE_HX = LEDGE_SPAN_FRAC * EXT_HX                      # half the span, at the wall
_R0 = (LEDGE_HX ** 2 + LEDGE_ARC_SAG ** 2) / (2.0 * LEDGE_ARC_SAG)
LEDGE_FLAT_HX = ((_R0 ** 2) - (_R0 - LEDGE_ARC_SAG + LEDGE_OUT) ** 2) ** 0.5   # half the flat
# each flank: an arc tangent to the flat that drops LEDGE_OUT over the remaining width
LEDGE_FLANK_R = ((LEDGE_HX - LEDGE_FLAT_HX) ** 2 + LEDGE_OUT ** 2) / (2.0 * LEDGE_OUT)
assert LEDGE_OUT < LEDGE_ARC_SAG, "the clip must cut the arc, not lie beyond it"
assert LEDGE_HX < EXT_HX - EXT_CORNER_R, "the ledge must stay on the front's straight part"

# the print bed: the ledge adds to the case's depth (y) and nothing to its width
BED = 250.0
assert 2 * EXT_HX < BED and 2 * EXT_HY + LEDGE_OUT < BED, (
    "the case is %.2f x %.2f mm; the bed is %.0f" % (2 * EXT_HX, 2 * EXT_HY + LEDGE_OUT, BED))

# ---- heights --------------------------------------------------------------
# The brief: the tray is as tall as the back (tall) edge of the single box's
# bottom, and the seam is flat.  "Tall edge" is read as the single bottom's
# bounding-box height -- its lip top at the back, 73.553 -- so the tray is that
# tall INCLUDING its lip, and its outer walls stop LIP_H below that.  (Reading it
# as the back wall's top, 68.824, would put the seam 1.27 mm higher and make the
# tray 74.824 with the lip; one number to change if that is what was meant.)
TRAY_H = B.Z_LIP + B.LIP_HY * B.SEAM_TAN          # 73.5534
Z_LIP = TRAY_H                                    # lip top == groove roof
Z_S = TRAY_H - LIP_H                              # the seam: the walls' mating plane

# card space and the top and bottom skins are the single box's, so the same cards
# fit; the lid is whatever remains of the total height
FLOOR_T, CEIL_T, INT_H = B.FLOOR_T, B.CEIL_T, B.INT_H
H_TOTAL = FLOOR_T + INT_H + CEIL_T                # 102.05
Z_CEIL = H_TOTAL - CEIL_T                         # underside of the lid's ceiling
LID_H = H_TOTAL - Z_S                             # 34.50

# ---- dividers -------------------------------------------------------------
# The tray's dividers run both ways and rise to just under the lip-top plane; the
# lid's run front-to-back only (so a stack leaning front or back, off vertical, is
# not met by a wall in the lid) and hang to just over the groove roof.  Each leaves
# DIV_GAP of clearance, so where a tray divider meets a lid divider the gap is
# 2 * DIV_GAP and the lip and roof, not the dividers, own the seam.  The gap also
# keeps the dividers' faces off the lip's top and the groove's roof: a bar whose top
# lay exactly in the lip's top plane would put a coplanar face into the boolean.
DIV_GAP = 0.15
DIV_TRAY_TOP = Z_LIP - DIV_GAP
DIV_LID_BOTTOM = Z_LIP + DIV_GAP
DIV_BASE_Z = 1.0                     # tray dividers start inside the floor
DIV_OVERLAP = 1.0                    # how far a bar runs into the wall (or ceiling) it joins


def divider_centres(n, pitch):
    """Positions of the n - 1 dividers between n slots, centred on 0."""
    return [(i - (n - 2) / 2.0) * pitch for i in range(n - 1)]


DIV_Y = divider_centres(N_ROWS, PITCH_Y)          # the tray's dividers running along x
DIV_X = divider_centres(N_COLS, PITCH_X)          # dividers running along y (tray AND lid)

# ---- snap domes and dimples ----------------------------------------------
# Three per side, on all four sides, each centred on a slot.  The dome and dimple
# are the single box's, and so is their height above the seam; that box's two
# domes sit 2.505 and 2.809 mm above its (sloping) seam, and a flat seam has one
# height, so the mean.
BUMP_H, BUMP_SPHERE_R = B.BUMP_H, B.BUMP_SPHERE_R
DENT_DEPTH, DENT_SPHERE_R = B.DENT_DEPTH, B.DENT_SPHERE_R
_above = [z - (B.Z_SEAM + B.SEAM_TAN * y) for (y, z) in B.SNAP_POINTS]
DOME_ABOVE_SEAM = sum(_above) / len(_above)       # 2.657
DOME_Z = Z_S + DOME_ABOVE_SEAM
# slot centres: along y for the left and right faces, along x for front and back
SLOT_CENTRES_Y = [(k - (N_ROWS - 1) / 2.0) * PITCH_Y for k in range(N_ROWS)]
SLOT_CENTRES_X = [(k - (N_COLS - 1) / 2.0) * PITCH_X for k in range(N_COLS)]

# how far past a part a cutter reaches, where it does not matter
OVER = 2.0
