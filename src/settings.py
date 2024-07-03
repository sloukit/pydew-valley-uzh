import pygame
import sys
import warnings
# The explicit import is needed, as this module is not automatically
# imported when you import pygame.
import pygame.freetype
if not getattr(pygame, "IS_CE", False):
    raise ImportError(
        "The game requires Pygame CE to function. "
        "(hint: type pip uninstall pygame and then pip install pygame-ce)"
    )
if sys.version_info < (3, 12):
    warnings.warn(
        f"The project is currently running under Python "
        f"{sys.version_info.major}.{sys.version_info.minor}. "
        f"Consider upgrading to 3.12 or the most recent version available "
        f"before running the game further.",
        DeprecationWarning,
    )
import pytmx
from pytmx.util_pygame import load_pygame
from enum import IntEnum, StrEnum
from types import FunctionType as Function


type Coordinate = tuple[int | float, int | float]
type SoundDict = dict[str, pygame.mixer.Sound]
type MapDict = dict[str, pytmx.TiledMap]
type AniFrames = dict[str, list[pygame.Surface]]

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
TILE_SIZE = 16
CHAR_TILE_SIZE = 48
SCALE_FACTOR = 4

LAYERS = {
    'water': 0,
    'lower ground': 1,
    'upper ground': 2,
    'soil': 3,
    'soil water': 4,
    'rain floor': 5,
    'plant': 6,
    'main': 7,
    'fruit': 8,
    'rain drops': 9,
    'particles': 10
}

GROW_SPEED = {'corn': 1, 'tomato': 0.7}

OVERLAY_POSITIONS = {
    'tool': (40, SCREEN_HEIGHT - 15),
    'seed': (70, SCREEN_HEIGHT - 5)}

SALE_PRICES = {
    'wood': 4,
    'apple': 2,
    'corn': 10,
    'tomato': 20
}
PURCHASE_PRICES = {
    'corn seed': 4,
    'tomato seed': 5
}

APPLE_POS = {
    'small': [(18, 17), (30, 37), (12, 50), (30, 45), (20, 30), (30, 10)],
    'default': [(30, 24), (60, 65), (50, 50), (16, 40), (45, 50), (42, 70)]
}


class ItemToUse(IntEnum):
    """Both available options for Player.use_tool. If any more have to be added, put them as members of this enum."""
    REGULAR_TOOL = 0
    SEED = 1


class FarmingTool(IntEnum):
    """Notably used to distinguish the different farming tools (including seeds) in-code."""
    NONE = 0  # Possible placeholder value if needed somewhere
    AXE = 1
    HOE = 2
    WATERING_CAN = 3
    CORN_SEED = 4
    TOMATO_SEED = 5

    @property
    def _swinging_tools(self):
        return {self.HOE, self.AXE}

    def is_swinging_tool(self):
        return self in self._swinging_tools

    @classmethod
    def get_first_tool_id(cls):
        """Return the first tool ID. This might change in the course of development."""
        return cls.AXE

    @classmethod
    def get_tool_count(cls):
        return cls.get_first_seed_id() - cls.get_first_tool_id()

    @classmethod
    def get_seed_count(cls):
        return len(cls) - cls.get_first_seed_id()

    @classmethod
    def get_first_seed_id(cls):
        """Same as get_first_tool_id, but for the seeds. Duh."""
        return cls.CORN_SEED


class InventoryResource(IntEnum):
    """All stored items in the inventory."""
    pass
