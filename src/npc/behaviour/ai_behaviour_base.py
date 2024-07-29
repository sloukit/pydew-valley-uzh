from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import IntEnum

from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.sprites.entities.entity import Entity


# TODO: Refactor NPCState into Entity.state (maybe override Entity.get_state())
class AIState(IntEnum):
    IDLE = 0
    MOVING = 1


class AIBehaviourBase(Entity, ABC):
    # Pathfinding
    pf_matrix: list[list[int]]
    """A representation of the in-game tilemap,
       where 1 stands for a walkable tile, and 0 stands for a
       non-walkable tile. Each list entry represents one row of the tilemap."""

    pf_grid: Grid
    pf_finder: AStarFinder
    pf_state: AIState
    pf_state_duration: float

    pf_path: list[tuple[int, int]]
    """The current path on which the NPC is moving.
       Each tile on which the NPC is moving is represented by its own
       coordinate tuple, while the first one in the list always being the NPCs
       current target position."""

    __on_path_abortion_funcs: [Callable[[], None]]
    __on_path_completion_funcs: list[Callable[[], None]]

    @abstractmethod
    def create_path_to_tile(self, coord: tuple[int, int]) -> bool:
        pass

    @abstractmethod
    def on_path_abortion(self, func: Callable[[], None]):
        pass

    @abstractmethod
    def abort_path(self):
        pass

    @abstractmethod
    def on_path_completion(self, func: Callable[[], None]):
        pass

    @abstractmethod
    def complete_path(self):
        pass

    @abstractmethod
    def exit_idle(self):
        pass

    @abstractmethod
    def exit_moving(self):
        pass

    @abstractmethod
    def move(self, dt: float):
        pass
