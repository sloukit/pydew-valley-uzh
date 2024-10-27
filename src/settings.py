import pygame  # noqa
import pytmx

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

# chunk size >= largest sprite size
# largest obj: piknik blanket (48x48)
# largest char: rabbit (48x48)
RENDER_CHUNK_W = 48 * SCALE_FACTOR
RENDER_CHUNK_H = 48 * SCALE_FACTOR

# +1 as int rounds down,
# +2 to render objects slightly offscreen - one tile off the screen edge on both sides
RENDER_CHUNKS_X = int(SCREEN_WIDTH / RENDER_CHUNK_W) + 3
RENDER_CHUNKS_Y = int(SCREEN_HEIGHT / RENDER_CHUNK_H) + 3

# chunk size >= largest hitbox size
# largest obj hitbox: tree_fallen_medium (32w) / bed (19h)
# largest map collider: 32x32
COLLISION_CHUNK_W = 32 * SCALE_FACTOR
COLLISION_CHUNK_H = 32 * SCALE_FACTOR

RANDOM_SEED = 123456789

GAME_MAP = Map.NEW_FARM

ENABLE_NPCS = True
TEST_ANIMALS = True

SETUP_PATHFINDING = any((ENABLE_NPCS, TEST_ANIMALS))

EMOTE_SIZE = 48

GROW_SPEED = {"corn": 1, "tomato": 0.7}

OVERLAY_POSITIONS = {
    "tool": (86, 150),
    "seed": (47, 142),
    "clock": (SCREEN_WIDTH - 10, 10),
    "FPS": (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10),
}

APPLE_POS = {
    "small": [(18, 17), (30, 37), (12, 50), (30, 45), (20, 30), (30, 10)],
    "default": [(12, 12), (46, 10), (40, 34), (3, 42), (65, 55), (32, 59)],
    "bush": [(10, 10), (8, 37), (25, 25), (40, 13), (33, 40)],
}

CHARS_PER_LINE = 45
TB_SIZE = (493, 264)

HEALTH_DECAY_VALUE = 0.002
BATH_STATUS_TIMEOUT = 30

DEFAULT_ANIMATION_NAME = "intro"

EMOTES_LIST = [
    "cheer_ani",
    "cool_ani",
    "furious_ani",
    "love_ani",
    "sad_ani",
    "sleep_ani",
    "smile_ani",
    "wink_ani",
]

TOMATO_OR_CORN_LIST = [
    "tomato",
    "corn",
]
