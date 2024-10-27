from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.dijkstra import DijkstraFinder

from src.npc.bases.chicken_base import ChickenBase
from src.npc.bases.cow_base import CowBase
from src.npc.bases.npc_base import NPCBase
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
            NPCBase.pf_finder = DijkstraFinder()
            ChickenBase.pf_finder = DijkstraFinder(
                diagonal_movement=DiagonalMovement.only_when_no_obstacle
            )
            CowBase.pf_finder = DijkstraFinder(
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
