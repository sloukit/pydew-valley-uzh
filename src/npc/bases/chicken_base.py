from __future__ import annotations

from abc import ABC
from typing import ClassVar

import pygame
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.bases.ai_behaviour import AIBehaviour
from src.npc.bases.animal import Animal
from src.npc.behaviour.ai_behaviour_tree_base import ContextType
from src.settings import Coordinate
from src.sprites.chunk_system.collision_chunks import CollisionManager
from src.sprites.setup import EntityAsset


class ChickenBase(Animal, AIBehaviour, ABC):
    pf_matrix: ClassVar[list[list[int]] | None] = None
    pf_grid: ClassVar[Grid | None] = None
    pf_finder: ClassVar[AStarFinder | None] = None

    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_manager: CollisionManager,
        behaviour_tree_context: ContextType,
        z: int,
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

        self.speed = 250
