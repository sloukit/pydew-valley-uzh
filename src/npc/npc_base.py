from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import IntEnum

from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.overlay.soil import SoilLayer
from src.sprites.entity import Entity


# TODO: Refactor NPCState into Entity.state (maybe override Entity.get_state())
class NPCState(IntEnum):
    IDLE = 0
    MOVING = 1


class NPCBase(Entity, ABC):
    # Pathfinding
    pf_matrix: list[list[int]]
    """A representation of the in-game tilemap,
       where 1 stands for a walkable tile,
       and 0 stands for a non-walkable tile.
       Each list entry represents one row of the tilemap."""

    pf_grid: Grid
    pf_finder: AStarFinder
    pf_state: NPCState
    pf_state_duration: float

    pf_path: list[tuple[int, int]]
    """The current path on which the NPC is moving.
       Each tile on which the NPC is moving is represented by its own
       coordinate tuple, while the first one in the list always
       being the NPCs current target position."""

    soil_layer: SoilLayer

    __on_path_abortion_funcs: list
    __on_path_completion_funcs: list

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
    def move(self, dt):
        pass
