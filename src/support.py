import json
import math
import os
import random
import sys
from collections.abc import Generator
from dataclasses import dataclass

import pygame
import pygame.freetype
import pygame.gfxdraw
import pytmx

from src import settings
from src.enums import Direction
from src.settings import SCALE_FACTOR, SCALED_TILE_SIZE, TILE_SIZE, Coordinate


def resource_path(relative_path: str):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    relative_path = relative_path.replace("/", os.sep)

    # Needed for pygbag runtime environment compatibility:
    if sys.platform in ("emscripten", "wasm"):
        return relative_path

    try:
        base_path = sys._MEIPASS  # noqa
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_path, relative_path)


# Might be changed later on if we use pygame.freetype instead
def import_font(size: int, font_path: str) -> pygame.font.Font:
    return pygame.font.Font(resource_path(font_path), size)


def import_freetype_font(size: int, font_path: str) -> pygame.freetype.Font:
    return pygame.freetype.Font(resource_path(font_path), size)


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
    files = {}
    for folder_path, _, file_names in os.walk(resource_path(tmx_path)):
        for file_name in file_names:
            full_path = os.path.join(folder_path, file_name)
            files[file_name.split(".")[0]] = pytmx.util_pygame.load_pygame(full_path)
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


@dataclass
class WeightedCoordinate:
    x: int
    y: int

    weight: float = 0


def get_flight_matrix(
    pos: tuple[int, int], radius: int
) -> list[list[WeightedCoordinate]]:
    """
    Returns a matrix with the width and height of radius * 2 + 1, with
    WeightedCoordinate objects of a weight between 0 and 1, where 0 is the most
    preferred flight position, and 1 the least preferred flight position.

    The position from which the flight is to be started is always in the centre
    of the matrix, and will have an infinite weight.

    The position of the object to be fled from should be
    relative to the start position, but does not have to be within the
    matrix coordinates.

    :param pos: Position of the object that should be fled from
    :param radius: Radius / distance of the flight vector.
                   The returned matrix has a width and height of radius * 2 + 1
    :return: Matrix with positions that can be fled to
    """

    diameter = radius * 2 + 1

    p1 = (radius, radius)
    p2 = (pos[0] + radius, pos[1] + radius)

    matrix = [
        [WeightedCoordinate(x, y) for x in range(diameter)] for y in range(diameter)
    ]

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

            matrix[y][x].weight = distance(p2, (x, y))
            matrix[y][x].weight *= abs(distance_ / math.pi)

    matrix[radius][radius].weight = float("inf")

    return matrix


def get_sorted_flight_vectors(
    pos: tuple[int, int], radius: int
) -> Generator[WeightedCoordinate, None, None]:
    flight_matrix = get_flight_matrix(pos, radius)

    x = []
    for row in flight_matrix:
        for col in row:
            x.append(col)

    for coord in sorted(x, key=lambda i: i.weight):
        yield coord


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

    pygame.draw.aalines(
        surface=surface,
        color=color,
        closed=True,
        points=(ul, ur, br, bl),
    )
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
    if direction[1]:
        return Direction.DOWN if direction[1] > 0 else Direction.UP
    if direction[0]:
        return Direction.RIGHT if direction[0] > 0 else Direction.LEFT
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


def get_outline(
    surface: pygame.Surface,
    outline_color: tuple[int, int, int] = (0, 0, 0),
    resize: bool = False,
) -> pygame.Surface:
    mask = pygame.mask.from_surface(surface)
    colorkey = (255, 255, 255)
    colorkey = colorkey if outline_color != colorkey else (0, 0, 0)
    mask_surf = mask.to_surface(setcolor=outline_color, unsetcolor=colorkey)
    mask_surf.set_colorkey(colorkey)

    if resize:
        outline = pygame.Surface(
            (surface.get_width() + 2, surface.get_height() + 2), pygame.SRCALPHA
        )
        outline.blit(mask_surf, (2, 1))
        outline.blit(mask_surf, (0, 1))
        outline.blit(mask_surf, (1, 2))
        outline.blit(mask_surf, (1, 0))
        outline.blit(surface, (1, 1))
    else:
        outline = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        outline.blit(mask_surf, (1, 0))
        outline.blit(mask_surf, (-1, 0))
        outline.blit(mask_surf, (0, 1))
        outline.blit(mask_surf, (0, -1))
        outline.blit(surface, (0, 0))
    return outline
