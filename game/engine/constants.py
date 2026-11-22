"""Shared constants and tuning values for Python Maze Adventure.

Keeping the numbers in one place lets the game, the tests and the
teaching materials stay in step with each other.
"""

# ---------------------------------------------------------------- gameplay
START_COINS = 30           # first maze level / Create display
PRACTICE_COINS = 50        # Boss practice run before the maze is cleared
COIN_VALUE = 10
CHEST_VALUE = 20
SUPER_ATTACK_COST = 30
FINAL_BONUS_TARGET = 50    # the base tops the final level up to this many coins
MIN_WEAPON_POWER = 1
MAX_WEAPON_POWER = 10
DEFAULT_WEAPON_POWER = 5

# ---------------------------------------------------------------- sandbox
MAX_ACTIONS = 200          # directional move commands and other game actions
MAX_OUTPUT_LINES = 400     # guards against a runaway print loop
FUEL_BUDGET = 2_000_000    # executed line events before we stop the program
TIME_LIMIT_SECONDS = 20.0  # excludes time spent waiting for animation/input
MAX_SOURCE_CHARS = 20_000

# ---------------------------------------------------------------- run states
RUN_IDLE = "idle"
RUN_RUNNING = "running"
RUN_FINISHED = "finished"
RUN_CANCELLED = "cancelled"

# ---------------------------------------------------------------- stages
STAGE_CREATE = 1
STAGE_MAZE = 2
STAGE_BOSS = 3
STAGE_TITLES = {
    STAGE_CREATE: "Create Your Explorer",
    STAGE_MAZE: "Escape the Maze",
    STAGE_BOSS: "Super Attack",
}
STAGE_COUNT = 3

# ---------------------------------------------------------------- directions
# 0 = up, 1 = right, 2 = down, 3 = left  (clockwise order)
DIRECTION_NAMES = ("up", "right", "down", "left")
DIRECTION_DX = (0, 1, 0, -1)
DIRECTION_DY = (-1, 0, 1, 0)

# ---------------------------------------------------------------- palette
COL_BG = (13, 16, 36)
COL_BG_DEEP = (8, 10, 24)
COL_PANEL = (24, 30, 58)
COL_PANEL_LIGHT = (32, 40, 74)
COL_PANEL_EDGE = (52, 64, 116)
COL_PANEL_EDGE_LIGHT = (78, 94, 160)
COL_TEXT = (232, 238, 255)
COL_TEXT_DIM = (150, 162, 200)
COL_TEXT_FAINT = (94, 106, 148)
COL_GOLD = (255, 205, 74)
COL_GOLD_DARK = (196, 140, 24)
COL_CYAN = (77, 226, 240)
COL_CYAN_DARK = (30, 168, 196)
COL_MAGENTA = (255, 111, 181)
COL_RED = (255, 92, 92)
COL_GREEN = (92, 240, 150)
COL_ORANGE = (255, 184, 108)
COL_PURPLE = (189, 147, 249)
COL_STONE = (74, 81, 112)
COL_STONE_LIGHT = (107, 116, 156)
COL_STONE_DARK = (46, 51, 76)
COL_FLOOR_A = (44, 52, 86)
COL_FLOOR_B = (38, 46, 78)

# ---------------------------------------------------------------- window
WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 900
WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 720
TARGET_FPS = 60

# ---------------------------------------------------------------- animation
MOVE_SECONDS = 0.20
TURN_SECONDS = 0.16
PICKUP_SECONDS = 0.35
BEAM_SECONDS = 1.25
SPEED_OPTIONS = ((1.0, "1x"), (2.0, "2x"), (0.0, "Instant"))
