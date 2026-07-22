"""All tuning constants for GLIDE in one place."""

WINDOW_TITLE = "GLIDE"
BG_COLOR = (0.02, 0.02, 0.05, 1.0)

# --- Animation --------------------------------------------------------------
SLIDE_SPEED = 15.0          # cells per second the orb travels
POP_TIME = 0.4              # fill-pop particle lifetime
ORB_BOB = 0.06             # idle vertical bob amplitude
TRAIL_LENGTH = 18          # orb motion-trail samples

# --- Board layout -----------------------------------------------------------
TILE = 1.0                  # spacing between cell centers
TILE_SIZE = 0.84            # visible tile footprint
TILE_THICK = 0.16
ORB_RADIUS = 0.30

# --- Camera -----------------------------------------------------------------
CAM_ANGLE = 57.0            # downward tilt in degrees
CAM_MARGIN = 5.0            # extra distance so the whole board fits

# --- Post-processing --------------------------------------------------------
BLOOM_INTENSITY = 0.65
BLOOM_MINTRIGGER = 0.62
BLOOM_SIZE = "small"

# --- Backdrop ---------------------------------------------------------------
BACKDROP_TOP = (0.02, 0.02, 0.06)
BACKDROP_BOTTOM = (0.10, 0.05, 0.16)
STAR_COUNT = 320
FLOOR_COLOR = (0.05, 0.06, 0.11)

# --- Colors -----------------------------------------------------------------
EMPTY_COLOR = (0.12, 0.14, 0.22)
EMPTY_EDGE = (0.20, 0.24, 0.36)
FILLED_COLOR = (0.15, 0.98, 0.82)
START_COLOR = (1.0, 0.82, 0.30)
STOP_COLOR = (1.0, 0.55, 0.15)
ORB_COLOR = (1.0, 0.99, 0.90)
WIN_COLOR = (0.55, 1.0, 0.7)
TRAIL_COLOR = (0.4, 1.0, 0.9)
