import json
import math
import os
import random
import sys
from collections.abc import Generator

import pygame
# import pygame.gfxdraw
import pygame.draw
import logging
LOG = logging.getLogger(__name__)
LOG.info('Importing pytmx...')
import pytmx
LOG.info('pytmx imported.')

from src import settings
from src.enums import Direction
from src.settings import SCALE_FACTOR, SCALED_TILE_SIZE, TILE_SIZE, Coordinate


def resource_path(relative_path: str):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if sys.platform in ('emscripten','wasi'):
        return relative_path
    relative_path = relative_path.replace("/", os.sep)
    try:
        base_path = sys._MEIPASS  # noqa
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_path, relative_path)


# Might be changed later on if we use pygame.freetype instead
def import_font(size: int, font_path: str) -> pygame.font.Font:
    return pygame.font.Font(resource_path(font_path), size)


def import_image(img_path: str, alpha: bool = True) -> pygame.Surface:
    full_path = resource_path(img_path)
    surf = (
        pygame.image.load(full_path).convert_alpha()
        if alpha
        else pygame.image.load(full_path).convert()
    )
    return pygame.transform.scale_by(surf, SCALE_FACTOR)


def import_folder(fold_path: str) -> list[pygame.Surface]:
    frames = []
    for folder_path, _, file_names in os.walk(resource_path(fold_path)):
        for file_name in sorted(file_names, key=lambda name: int(name.split(".")[0])):
            full_path = os.path.join(folder_path, file_name)
            frames.append(
                pygame.transform.scale_by(
                    pygame.image.load(full_path).convert_alpha(), SCALE_FACTOR
                )
            )
    return frames


def import_folder_dict(fold_path: str) -> dict[str, pygame.Surface]:
    frames = {}
    for folder_path, _, file_names in os.walk(resource_path(fold_path)):
        for file_name in file_names:
            full_path = os.path.join(folder_path, file_name)
            frames[file_name.split(".")[0]] = pygame.transform.scale_by(
                pygame.image.load(full_path).convert_alpha(), SCALE_FACTOR
            )
    return frames


def tmx_importer(tmx_path: str) -> settings.MapDict:
    LOG.info('tmx_importer()')
    files = {}
    for folder_path, _, file_names in os.walk(resource_path(tmx_path)):
        for file_name in file_names:
            full_path = os.path.join(folder_path, file_name)
            LOG.info('tmx_importer(): running load_pygame')
            files[file_name.split(".")[0]] = pytmx.util_pygame.load_pygame(full_path)
            LOG.info('tmx_importer(): running load_pygame -> DONE')
    return files


def animation_importer(
    *ani_path: str, frame_size: int = None, resize: int = None
) -> settings.AniFrames:
    if frame_size is None:
        frame_size = TILE_SIZE

    animation_dict = {}
    for folder_path, _, file_names in os.walk(os.path.join(*ani_path)):
        for file_name in file_names:
            full_path = os.path.join(folder_path, file_name)
            surf = pygame.image.load(full_path).convert_alpha()
            animation_dict[str(file_name.split(".")[0])] = []
            for col in range(surf.get_width() // frame_size):
                subsurf_rect = pygame.Rect(col * frame_size, 0, frame_size, frame_size)
                cutout_surf = surf.subsurface(subsurf_rect)

                if resize:
                    animation_dict[str(file_name.split(".")[0])].append(
                        pygame.transform.scale(cutout_surf, (resize, resize))
                    )
                else:
                    animation_dict[str(file_name.split(".")[0])].append(
                        pygame.transform.scale_by(cutout_surf, SCALE_FACTOR)
                    )

    return animation_dict


def sound_importer(*snd_path: str, default_volume: float = 0.5) -> settings.SoundDict:
    sounds_dict = {}

    for sound_name in os.listdir(resource_path(os.path.join(*snd_path))):
        key = sound_name.split(".")[0]
        value = pygame.mixer.Sound(os.path.join(*snd_path, sound_name))
        value.set_volume(default_volume)
        sounds_dict[key] = value
    return sounds_dict


def save_data(data, file_name):
    folder_path = resource_path("data/settings")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    with open(resource_path("data/settings/" + file_name), "w") as file:
        json.dump(data, file, indent=4)


def load_data(file_name):
    with open(resource_path("data/settings/" + file_name), "r") as file:
        return json.load(file)


def map_coords_to_tile(pos):
    return pos[0] // SCALED_TILE_SIZE, pos[1] // SCALED_TILE_SIZE


def generate_particle_surf(img: pygame.Surface) -> pygame.Surface:
    px_mask = pygame.mask.from_surface(img)
    ret = px_mask.to_surface()
    ret.set_colorkey("black")
    return ret


def flip_items(d: dict) -> dict:
    """Returns a copy of d with key-value pairs flipped (i.e. keys become values and vice-versa)."""
    ret = {}
    for key, val in d.items():
        ret[val] = key
    return ret


def tile_to_screen(pos):
    tile_size = TILE_SIZE * SCALE_FACTOR
    return pos[0] * tile_size, pos[1] * tile_size


def screen_to_tile(pos):
    tile_size = TILE_SIZE * SCALE_FACTOR
    return pos[0] // tile_size, pos[1] // tile_size


def get_flight_matrix(
    pos: tuple[int, int], radius: int, angle: float = math.pi / 2
) -> list[list[int]]:
    """
    Returns a matrix with the width and height of radius * 2 + 1, with a value
    of 1 if the matrix position can be fled to and 0 if not.
    The position from which the flight is to be started is always in the centre
    of the matrix. The position of the object to be fled from should be
    relative to the start position, but does not have to be within the
    matrix coordinates.

    TODO: Could be optimised so that instead of a matrix with integer / boolean
     values a matrix with the weight of each possible position is returned, of
     which the walkable position with the greatest weight is then fled to.

    :param pos: Position of the object that should be fled from
    :param radius: Radius / distance of the flight vector.
                   The returned matrix has a width and height of radius * 2 + 1
    :param angle: Angle of the flight vector (measured in radians)
                  Default: PI / 2 (90°)
    :return: Matrix with positions that can be fled to
    """

    diameter = radius * 2 + 1

    p1 = (radius, radius)
    p2 = (pos[0] + radius, pos[1] + radius)

    matrix = [[0 for _ in range(diameter)] for _ in range(diameter)]

    # For further calculations the angle gets inverted and divided by two
    # Can probably be optimised
    angle = math.pi - angle / 2

    # The exact angle of the position that should be fled from, measured from
    # the centre of the matrix
    dangerous_angle = math.atan2((p1[0] - p2[0]), (p1[1] - p2[1]))

    for y in range(len(matrix)):
        for x in range(len(matrix[0])):
            # Angle from the centre of the matrix to the currently checked pos
            current_angle = math.atan2((p1[0] - x), (p1[1] - y))
            # Angular distance of the dangerous angle and the current angle
            distance_ = dangerous_angle - current_angle

            # Distance could be greater than half a turn,
            # in which case the result is rotated to the other extreme
            if distance_ > math.pi:
                distance_ = distance_ - (math.pi * 2)
            elif distance_ < -math.pi:
                distance_ = distance_ + (math.pi * 2)

            if -angle < distance_ < angle:
                matrix[y][x] = 0
            else:
                matrix[y][x] = 1

    return matrix


def draw_aa_line(
    surface: pygame.Surface,
    center_pos: tuple[float, float],
    thickness: int,
    length: int,
    deg: float,
    color: tuple[int, int, int],
):
    ul = (
        center_pos[0]
        + (length / 2.0) * math.cos(deg)
        - (thickness / 2.0) * math.sin(deg),
        center_pos[1]
        + (thickness / 2.0) * math.cos(deg)
        + (length / 2.0) * math.sin(deg),
    )
    ur = (
        center_pos[0]
        - (length / 2.0) * math.cos(deg)
        - (thickness / 2.0) * math.sin(deg),
        center_pos[1]
        + (thickness / 2.0) * math.cos(deg)
        - (length / 2.0) * math.sin(deg),
    )
    bl = (
        center_pos[0]
        + (length / 2.0) * math.cos(deg)
        + (thickness / 2.0) * math.sin(deg),
        center_pos[1]
        - (thickness / 2.0) * math.cos(deg)
        + (length / 2.0) * math.sin(deg),
    )
    br = (
        center_pos[0]
        - (length / 2.0) * math.cos(deg)
        + (thickness / 2.0) * math.sin(deg),
        center_pos[1]
        - (thickness / 2.0) * math.cos(deg)
        - (length / 2.0) * math.sin(deg),
    )

    # pygame.gfxdraw.aapolygon(surface, (ul, ur, br, bl), color)
    pygame.draw.aalines(
        surface=surface,
        color=color,
        closed=True,
        points=(ul, ur, br, bl),
    )
    # pygame.gfxdraw.filled_polygon(surface, (ul, ur, br, bl), color)
    # equivalent to pygame.gfxdraw.filled_polygon:
    pygame.draw.polygon(
        surface=surface,
        color=color,
        points=(ul, ur, br, bl),
        width=0,  # width=0 -> filled
    )


def get_entity_facing_direction(
    direction: tuple[float, float] | pygame.math.Vector2,
    default_value: Direction = Direction.RIGHT,
) -> Direction:
    """
    :param direction: Direction to use.
    :param default_value: Default direction to use.
    :return: String of the direction the entity is facing
    """
    # prioritizes vertical animations, flip if statements to get horizontal
    # ones
    if direction[0]:
        return Direction.RIGHT if direction[0] > 0 else Direction.LEFT
    if direction[1]:
        return Direction.DOWN if direction[1] > 0 else Direction.UP
    return default_value


def rand_circular_pos(
    center: Coordinate, max_radius: float, min_radius: float
) -> Coordinate:
    """returns a random position from a circular range"""
    angle = random.random() * 2 * math.pi
    radius = min_radius + ((max_radius - min_radius) * random.random())
    rand_x = center[0] + radius * math.cos(angle)
    rand_y = center[1] + radius * math.sin(angle)
    return (rand_x, rand_y)


def oscilating_lerp(a: float | int, b: float | int, t: float) -> float:
    """returns a value smoothly iterpolated from a to b and back to a"""
    angle = 0 + math.pi * t
    # the sine of this range of angles (0 to pi) gives a value from 0 to 1 to 0
    t = math.sin(angle)
    return pygame.math.lerp(a, b, t)


def near_tiles(
    pos: tuple[int, int], radius: int, shuffle: bool = False
) -> Generator[tuple[int, int], None, None]:
    """
    :param pos: The centre of the generated positions
    :param radius: The radius of the square
    :param shuffle: Whether the positions should be yielded in a random order
    :return: Generator for all positions within a square of the width and
    height of radius * 2 + 1 around the given position
    """
    horizontal = list(range(radius * 2 + 1))
    vertical = list(range(radius * 2 + 1))

    horizontal.pop(radius)
    vertical.pop(radius)

    if shuffle:
        random.shuffle(horizontal)
        random.shuffle(vertical)

    for i in horizontal:
        for j in vertical:
            yield int(pos[0] - radius + i), int(pos[1] - radius + j)


def distance(pos1, pos2):
    return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
