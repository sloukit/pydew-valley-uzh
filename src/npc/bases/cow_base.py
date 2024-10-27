from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

import pygame
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.enums import Layer
from src.npc.bases.ai_behaviour import AIBehaviour
from src.npc.bases.animal import Animal
from src.npc.behaviour.ai_behaviour_tree_base import ContextType
from src.settings import Coordinate
from src.sprites.chunk_system.collision_chunks import CollisionManager
from src.sprites.entities.character import Character
from src.sprites.setup import EntityAsset


class CowBase(Animal, AIBehaviour, ABC):
    pf_matrix: ClassVar[list[list[int]] | None] = None
    pf_grid: ClassVar[Grid | None] = None
    pf_finder: ClassVar[AStarFinder | None] = None

    fleeing: bool

    player: Character

    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_manager: CollisionManager,
        behaviour_tree_context: ContextType,
        z: Layer,
    ):
        Animal.__init__(
            self,
            pos=pos,
            assets=assets,
            groups=groups,
            collision_manager=collision_manager,
            z=z,
        )
        AIBehaviour.__init__(self, behaviour_tree_context=behaviour_tree_context)

        self.speed = 150

    @abstractmethod
    def flee_from_pos(self, pos: tuple[int, int], pf_grid: Grid = None) -> bool:
        pass
