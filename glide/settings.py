"""All tuning constants for GLIDE in one place."""

WINDOW_TITLE = "GLIDE"
BG_COLOR = (0.03, 0.03, 0.07, 1.0)

# --- Animation --------------------------------------------------------------
SLIDE_SPEED = 15.0          # cells per second the orb travels
POP_TIME = 0.35             # fill-pop particle lifetime

# --- Board layout -----------------------------------------------------------
TILE = 1.0                  # spacing between cell centers
TILE_SIZE = 0.86            # visible tile footprint
TILE_THICK = 0.12
ORB_RADIUS = 0.30

# --- Camera -----------------------------------------------------------------
CAM_ANGLE = 58.0            # downward tilt in degrees
CAM_MARGIN = 4.5            # extra distance so the whole board fits

# --- Colors -----------------------------------------------------------------
EMPTY_COLOR = (0.13, 0.15, 0.24)
FILLED_COLOR = (0.15, 0.95, 0.80)
START_COLOR = (0.95, 0.85, 0.35)
STOP_COLOR = (1.0, 0.55, 0.15)
ORB_COLOR = (1.0, 0.98, 0.85)
WIN_COLOR = (0.55, 1.0, 0.7)
