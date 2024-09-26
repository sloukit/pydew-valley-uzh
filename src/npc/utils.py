import math
import warnings
from contextlib import AbstractContextManager, contextmanager
from typing import Generator

from pathfinding.core.grid import Grid

from src.exceptions import PathfindingWarning
from src.npc.bases.ai_behaviour_base import AIBehaviourBase
from src.npc.setup import AIData
from src.settings import SCALED_TILE_SIZE, TILE_SIZE
from src.support import near_tiles


# region
@contextmanager
def pf_grid_temporary_exclude(positions: set[tuple[int, int]], pf_grid: Grid = None):
    if pf_grid is None:
        pf_grid = AIData.Grid

    _old_walkable_values: dict[tuple[int, int], bool] = {}

    try:
        for x, y in positions:
            try:
                _old_walkable_values[(x, y)] = pf_grid.walkable(x, y)
                pf_grid.node(x, y).walkable = False
            except IndexError:
                pass
        yield
    finally:
        for x, y in positions:
            pf_grid.node(x, y).walkable = _old_walkable_values[(x, y)]


@contextmanager
def pf_exclude_player_position(pf_grid: Grid = None):
    if pf_grid is None:
        pf_grid = AIData.Grid

    player_hitbox = AIData.player.hitbox_rect
    player_x_min = int(player_hitbox.left / SCALED_TILE_SIZE)
    player_x_max = math.ceil(player_hitbox.right / SCALED_TILE_SIZE)
    player_y_min = int(player_hitbox.top / SCALED_TILE_SIZE)
    player_y_max = math.ceil(player_hitbox.bottom / SCALED_TILE_SIZE)

    player_tile_positions = [
        (x + player_x_min, y + player_y_min)
        for x in range(player_x_max - player_x_min)
        for y in range(player_y_max - player_y_min)
    ]

    with pf_grid_temporary_exclude(set(player_tile_positions), pf_grid=pf_grid) as ctx:
        yield ctx


@contextmanager
def pathfinding_context(
    *args, pf_grid: Grid = None
) -> Generator[AbstractContextManager, None, None]:
    if pf_grid is None:
        pf_grid = AIData.Grid

    positions = set()
    for obj in AIData.moving_collideable_objects:
        current_hitbox = obj.hitbox_rect
        x_min = int(current_hitbox.left / SCALED_TILE_SIZE)
        x_max = math.ceil(current_hitbox.right / SCALED_TILE_SIZE)
        y_min = int(current_hitbox.top / SCALED_TILE_SIZE)
        y_max = math.ceil(current_hitbox.bottom / SCALED_TILE_SIZE)

        current_positions = [
            (x + x_min, y + y_min)
            for x in range(x_max - x_min)
            for y in range(y_max - y_min)
        ]

        for pos in current_positions:
            positions.add(pos)

    with pf_grid_temporary_exclude(positions, pf_grid=pf_grid) as ctx:
        yield ctx


def pf_add_matrix_collision(
    matrix: list[list[int]], pos: tuple[float, float], size: tuple[float, float]
):
    """
    Add a collision rect to the given matrix at the given position.
    The given position will be the topleft corner of the rectangle.
    The values given to this method should equal to the values as defined
    in Tiled (scaled up by TILE_SIZE, not scaled up by SCALE_FACTOR)
    :param matrix: Matrix to add collision to
    :param pos: position of collision rect (x, y) (rounded-down)
    :param size: size of collision rect (width, height) (rounded-up)
    """
    tile_x = int(pos[0] / TILE_SIZE)
    tile_y = int(pos[1] / TILE_SIZE)
    tile_w = math.ceil((pos[0] + size[0]) / TILE_SIZE) - tile_x
    tile_h = math.ceil((pos[1] + size[1]) / TILE_SIZE) - tile_y

    for w in range(tile_w):
        for h in range(tile_h):
            try:
                matrix[tile_y + h][tile_x + w] = 0
            except IndexError as e:
                warnings.warn(
                    f"Failed adding non-walkable Tile to pathfinding matrix: {e}",
                    PathfindingWarning,
                )


def pf_move_to(
    ai: AIBehaviourBase,
    target_tile: tuple[int, int],
    max_length: int = -1,
    pf_grid: Grid = None,
):
    """
    Makes the Entity move to the given tile.
    :param ai: Entity that should move
    :param target_tile: Tile the Entity should move to
    :param max_length: (Optional) maximum length of the created path
    :param pf_grid: (Optional) pathfinding grid to use. Defaults to self.pf_grid
    :return: True if path has successfully been created, otherwise False
    """
    with pathfinding_context(pf_grid=pf_grid):
        if ai.create_path_to_tile(target_tile, pf_grid=pf_grid):
            if 0 < max_length < len(ai.pf_path):
                ai.pf_path = ai.pf_path[:max_length]
            return True
    return False


def pf_wander(ai: AIBehaviourBase, radius: int = 5, pf_grid: Grid = None) -> bool:
    """
    Makes the Entity wander to a random tile in the given radius.
    :param ai: Entity that should wander
    :param radius: (Optional) radius in which the Entity should wander
    :param pf_grid: (Optional) pathfinding grid to use. Defaults to self.pf_grid
    :return: True if path has successfully been created, otherwise False
    """
    # current position on the tilemap
    tile_coord = ai.get_tile_pos()

    for pos in near_tiles(tile_coord, radius, shuffle=True):
        if pf_move_to(ai, pos, max_length=radius, pf_grid=pf_grid):
            return True
    return False
