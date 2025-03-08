import os
import sys

import pygame  # noqa
import pytmx  # type:ignore [import-untyped]

from src.enums import Map
from src.import_checks import *  # noqa: F403

type Coordinate = tuple[int | float, int | float]
type SoundDict = dict[str, pygame.mixer.Sound]
type MapDict = dict[str, pytmx.TiledMap]
type AniFrames = dict[str, list[pygame.Surface]]
type GogglesStatus = bool | None
type NecklaceStatus = bool | None
type HatStatus = bool | None
type HornStatus = bool | None
type OutgroupSkinStatus = bool | None

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
TILE_SIZE = 16
CHAR_TILE_SIZE = 48
SCALE_FACTOR = 4
SCALED_TILE_SIZE = TILE_SIZE * SCALE_FACTOR

RANDOM_SEED = 123456789

GAME_MAP = Map.NEW_FARM

ENABLE_NPCS = True
TEST_ANIMALS = True

GAME_LANGUAGE = os.environ.get("GAME_LANGUAGE", "de")
DEBUG_MODE_VERSION = 0
# True  => virtual game time
# False => real world time
USE_GAME_TIME = False
# number of seconds per in game minute (reference - in Stardew Valley each minute is 0.7 seconds)
# change to e.g. 0.1 for debug to speed-up day/night cycle
SECONDS_PER_GAME_MINUTE = 0.7
# should be 1.0 - increase x10 for debug to speed-up round end
WORLD_TIME_MULTIPLIER = 1.0
# USE_SERVER = False
USE_SERVER = True

# position is normally only logged after movement and when the character stands still
# this is the minimum accumulated moving time to trigger logging for this scenario, to reduce server load
POS_MIN_LOG_INTERVAL = 1
# if a player moves for a long time continuously, we log the position during movement
POS_MOVE_LOG_INTERVAL = 15
# tool log interval after n accumulative uses of all tools and seeds, the statistics are sent to the server
TOOLS_LOG_INTERVAL = 5

IS_WEB = sys.platform in ("emscripten", "wasm")
# for now, in web mode, do not use dummy server (which requires `requests` module not available via pygbag)
if not IS_WEB:
    # If we're running locally, set this via environment variable:
    if os.getenv("USE_SERVER") == "true":
        USE_SERVER = True
    else:
        USE_SERVER = False


# NOTE(larsbutler): Don't change this line at all.
# WEB_SERVER_URL is populated during build,
# and build scripts expect this value exactly
# so we can populate it with the actual server URL
# at deploy time.
WEB_SERVER_URL = "WEB_SERVER_URL_PLACEHOLDER"
if IS_WEB:
    # For the web distribution, this should be replaced during
    # build time.
    SERVER_URL = WEB_SERVER_URL
else:
    SERVER_URL = os.getenv("SERVER_URL", "http://127.0.0.0:8888")

SETUP_PATHFINDING = any((ENABLE_NPCS, TEST_ANIMALS))

EMOTE_SIZE = 48

SAM_BORDER_SIZE = (
    122,
    131,
)  # absolute size of the border around self-assessment manikins

SOCIAL_IDENTITY_ASSESSMENT_BORDER_SIZE = (
    122,
    131,
)

GROW_SPEED = {
    "corn": 1.40,
    "tomato": 1.40,
    "beetroot": 1.40,
    "carrot": 1.40,
    "eggplant": 1.40,
    "pumpkin": 1.40,
    "parsnip": 1.40,
}

BASE_ALLOWED_CROPS = [
    "wood",
    "apple",
    "blackberry",
    "blueberry",
    "raspberry",
    "orange",
    "peach",
    "pear",
]


OVERLAY_POSITIONS = {
    "tool": (86, 150),
    "seed": (47, 141),
    "money": (115, 205),
    "box_info_label": (15, SCREEN_HEIGHT - 50),
    "box_info": (150, 90),
    "clock": (SCREEN_WIDTH - 10, 10),
    "FPS": (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 5),
}

APPLE_POS = {
    "small": [(18, 17), (30, 37), (12, 50), (30, 45), (20, 30), (30, 10)],
    "default": [(12, 12), (46, 10), (40, 34), (3, 42), (65, 55), (32, 59)],
    "bush": [(10, 10), (8, 37), (25, 25), (40, 13), (33, 40)],
}

CHARS_PER_LINE = 45
TB_SIZE = (403, 264)

# tutorial and intro text box position
TUTORIAL_TB_LEFT = SCREEN_WIDTH - TB_SIZE[0]
TUTORIAL_TB_TOP = SCREEN_HEIGHT / 1.5 - TB_SIZE[1]

HEALTH_DECAY_VALUE = 0.002
BATH_STATUS_TIMEOUT = 30

DEFAULT_ANIMATION_NAME = "intro"

EMOTES_LIST = [
    "furious_ani",
    "love_ani",
    "sad_ani",
    "smile_ani",
    "wink_ani",
]

TOMATO_OR_CORN_LIST = [
    "tomato",
    "corn",
]
