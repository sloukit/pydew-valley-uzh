from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.behaviour.chicken_behaviour_tree import ChickenBehaviourTree
from src.npc.behaviour.cow_behaviour_tree import CowBehaviourTree
from src.npc.behaviour.cow_flee_behaviour_tree import CowFleeBehaviourTree
from src.npc.behaviour.npc_behaviour_tree import NPCBehaviourTree


class AIData:
    Matrix: list[list[int]] = None
    Grid: Grid = None

    NPCPathFinder: AStarFinder = None
    ChickenPathFinder: AStarFinder = None
    CowPathFinder: AStarFinder = None

    @classmethod
    def setup(cls, pathfinding_matrix: list[list[int]]) -> None:
        NPCBehaviourTree.init()
        ChickenBehaviourTree.init()
        CowBehaviourTree.init()
        CowFleeBehaviourTree.init()

        cls.Matrix = pathfinding_matrix
        cls.Grid = Grid(matrix=cls.Matrix)

        cls.NPCPathFinder = AStarFinder()
        cls.ChickenPathFinder = AStarFinder(
            diagonal_movement=DiagonalMovement.only_when_no_obstacle
        )
        cls.CowPathFinder = AStarFinder(
            diagonal_movement=DiagonalMovement.only_when_no_obstacle
        )
