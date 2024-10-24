from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import ClassVar

from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.enums import AIState
from src.npc.behaviour.ai_behaviour_tree_base import NodeWrapper
from src.npc.path_scripting import AIScriptedPath
from src.sprites.entities.entity import Entity


class AIBehaviourBase(Entity, ABC):
    # Pathfinding
    pf_matrix: ClassVar[list[list[int]] | None]
    """A representation of the in-game tilemap,
       where 1 stands for a walkable tile, and 0 stands for a
       non-walkable tile. Each list entry represents one row of the tilemap."""

    pf_grid: ClassVar[Grid | None]
    pf_finder: ClassVar[AStarFinder | None]
    pf_state: AIState
    pf_state_duration: float

    pf_path: list[tuple[int, int]]
    """The current path on which the NPC is moving.
       Each tile on which the NPC is moving is represented by its own
       coordinate tuple, while the first one in the list always being the NPCs
       current target position."""

    _script: AIScriptedPath | None

    __on_path_abortion_funcs: list[Callable[[], None]]
    __on_path_completion_funcs: list[Callable[[], None]]

    __on_stop_moving_funcs: list[Callable[[], None]]

    __on_script_finish_funcs: list[Callable[[], None]]

    @property
    @abstractmethod
    def conditional_behaviour_tree(self):
        pass

    @conditional_behaviour_tree.setter
    @abstractmethod
    def conditional_behaviour_tree(self, value: NodeWrapper | None):
        pass

    @property
    @abstractmethod
    def continuous_behaviour_tree(self):
        pass

    @continuous_behaviour_tree.setter
    @abstractmethod
    def continuous_behaviour_tree(self, value: NodeWrapper | None):
        pass

    @abstractmethod
    def create_path_to_tile(self, coord: tuple[int, int], pf_grid: Grid) -> bool:
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
    def stop_moving(self):
        pass

    @abstractmethod
    def move(self, dt: float):
        pass
