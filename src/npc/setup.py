import math
from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.bases.chicken_base import ChickenBase
from src.npc.bases.cow_base import CowBase
from src.npc.bases.npc_base import NPCBase
from src.npc.behaviour.ai_behaviour import AIBehaviour
from src.settings import SCALED_TILE_SIZE
from src.sprites.entities.entity import Entity
from src.sprites.entities.player import Player


class AIData:
    Matrix: list[list[int]] = None
    Grid: Grid = None

    player: Player = None
    moving_collideable_objects: list[Entity] = None

    setup: bool = False

    @classmethod
    def update(
        cls,
        pathfinding_matrix: list[list[int]],
        player: Player,
        moving_collideable_objects: list[Entity] = None,
    ) -> None:
        if not cls.setup:
            AIBehaviour.pathfinding_context = pathfinding_context

            NPCBase.pf_finder = AStarFinder()
            ChickenBase.pf_finder = AStarFinder(
                diagonal_movement=DiagonalMovement.only_when_no_obstacle
            )
            CowBase.pf_finder = AStarFinder(
                diagonal_movement=DiagonalMovement.only_when_no_obstacle
            )

            cls.setup = True

        cls.Matrix = pathfinding_matrix
        cls.Grid = Grid(matrix=cls.Matrix)

        for ai in (NPCBase, ChickenBase, CowBase):
            ai.pf_matrix = cls.Matrix
            ai.pf_grid = cls.Grid

        cls.player = player

        cls.moving_collideable_objects = moving_collideable_objects
        if cls.moving_collideable_objects is None:
            cls.moving_collideable_objects = []
        cls.moving_collideable_objects.append(cls.player)


@contextmanager
def pf_grid_temporary_exclude(positions: set[tuple[int, int]]):
    _old_walkable_values: dict[tuple[int, int], bool] = {}

    try:
        for x, y in positions:
            _old_walkable_values[(x, y)] = AIData.Grid.walkable(x, y)
            AIData.Grid.node(x, y).walkable = False
        yield
    finally:
        for x, y in positions:
            AIData.Grid.node(x, y).walkable = _old_walkable_values[(x, y)]


@contextmanager
def pf_exclude_player_position():
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

    with pf_grid_temporary_exclude(set(player_tile_positions)) as ctx:
        yield ctx


@contextmanager
def pathfinding_context(
    *args, **kwargs
) -> Generator[AbstractContextManager, None, None]:
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

    with pf_grid_temporary_exclude(positions) as ctx:
        yield ctx
