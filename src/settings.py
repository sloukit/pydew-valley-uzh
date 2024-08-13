import logging
LOG = logging.getLogger(__name__)

import pygame  # noqa
import pygame.freetype
LOG.info('Importing pytmx...')
import pytmx
LOG.info('pytmx imported.')

from src.enums import Map
from src.import_checks import *  # noqa: F403

type Coordinate = tuple[int | float, int | float]
type SoundDict = dict[str, pygame.mixer.Sound]
type MapDict = dict[str, pytmx.TiledMap]
type AniFrames = dict[str, list[pygame.Surface]]
type GogglesStatus = bool | None

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
TILE_SIZE = 16
CHAR_TILE_SIZE = 48
SCALE_FACTOR = 4
SCALED_TILE_SIZE = TILE_SIZE * SCALE_FACTOR

GAME_MAP = Map.FOREST

ENABLE_NPCS = False
TEST_ANIMALS = False

SETUP_PATHFINDING = any((ENABLE_NPCS, TEST_ANIMALS))

EMOTE_SIZE = 48

GROW_SPEED = {"corn": 1, "tomato": 0.7}

OVERLAY_POSITIONS = {
    "tool": (86, 150),
    "seed": (47, 142),
    "clock": (SCREEN_WIDTH - 10, 10),
}

APPLE_POS = {
    "small": [(18, 17), (30, 37), (12, 50), (30, 45), (20, 30), (30, 10)],
    "default": [(12, 12), (46, 10), (40, 34), (3, 42), (65, 55), (32, 59)],
}

CHARS_PER_LINE = 45
TB_SIZE = (493, 264)
