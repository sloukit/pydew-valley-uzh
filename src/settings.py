import pygame.freetype
import pytmx
from src.import_checks import *

type Coordinate = tuple[int | float, int | float]
type SoundDict = dict[str, pygame.mixer.Sound]
type MapDict = dict[str, pytmx.TiledMap]
type AniFrames = dict[str, list[pygame.Surface]]

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
TILE_SIZE = 16
CHAR_TILE_SIZE = 48
SCALE_FACTOR = 4
SCALED_TILE_SIZE = TILE_SIZE * SCALE_FACTOR
TB_LAYER = 11

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
    'particles': 10,
    "TextBox": TB_LAYER
}

ENABLE_NPCS = False

GROW_SPEED = {'corn': 1, 'tomato': 0.7}

OVERLAY_POSITIONS = {
    'tool': (40, SCREEN_HEIGHT - 15),
    'seed': (70, SCREEN_HEIGHT - 5)}

APPLE_POS = {
    'small': [(18, 17), (30, 37), (12, 50), (30, 45), (20, 30), (30, 10)],
    'default': [(30, 24), (60, 65), (50, 50), (16, 40), (45, 50), (42, 70)]
}

CHARS_PER_LINE = 45
TB_SIZE = (493, 264)

KEYBINDS = {
    'up': {'type': "key", 'value': pygame.K_w, 'text': "Up"},
    'down': {'type': "key", 'value': pygame.K_s, 'text': "Down"},
    'right': {'type': "key", 'value': pygame.K_d, 'text': "Right"},
    'left': {'type': "key", 'value': pygame.K_a, 'text': "Left"},
    'next tool': {'type': "key", 'value': pygame.K_q, 'text': "Cycle Tools"},
    'use': {'type': "mouse", 'value': 0, 'text': "Use"},
    'next seed': {'type': "key", 'value': pygame.K_e, 'text': "Cycle Seeds"},
    'plant': {'type': "mouse", 'value': 2, 'text': "Plant Current Seed"},
    'interact': {'type': "key", 'value': pygame.K_i, 'text': "Interact"},
}