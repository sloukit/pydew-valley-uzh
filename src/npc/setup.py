from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.bases.chicken_base import ChickenBase
from src.npc.bases.cow_base import CowBase
from src.npc.bases.npc_base import NPCBase
from src.npc.behaviour.chicken_behaviour_tree import ChickenBehaviourTree
from src.npc.behaviour.cow_behaviour_tree import CowBehaviourTree
from src.npc.behaviour.cow_flee_behaviour_tree import CowFleeBehaviourTree
from src.npc.behaviour.npc_behaviour_tree import NPCBehaviourTree
from src.sprites.entities.player import Player


class AIData:
    Matrix: list[list[int]] = None
    Grid: Grid = None

    player: Player = None

    _setup: bool = False

    @classmethod
    def update(cls, pathfinding_matrix: list[list[int]], player: Player) -> None:
        if not cls._setup:
            NPCBehaviourTree.init()
            ChickenBehaviourTree.init()
            CowBehaviourTree.init()
            CowFleeBehaviourTree.init()

            NPCBase.pf_finder = AStarFinder()
            ChickenBase.pf_finder = AStarFinder(
                diagonal_movement=DiagonalMovement.only_when_no_obstacle
            )
            CowBase.pf_finder = AStarFinder(
                diagonal_movement=DiagonalMovement.only_when_no_obstacle
            )

            cls._setup = True

        cls.Matrix = pathfinding_matrix
        cls.Grid = Grid(matrix=cls.Matrix)

        for ai in (NPCBase, ChickenBase, CowBase):
            ai.pf_matrix = cls.Matrix
            ai.pf_grid = cls.Grid

        cls.player = player
