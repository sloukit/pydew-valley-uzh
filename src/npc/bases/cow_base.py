from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

import pygame
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.bases.animal import Animal
from src.npc.behaviour.ai_behaviour import AIBehaviour
from src.settings import Coordinate
from src.sprites.character import Character
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
        collision_sprites: pygame.sprite.Group,
        z: int,
    ):
        Animal.__init__(
            self,
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,
            z=z,
        )
        AIBehaviour.__init__(self)

        self.speed = 150

    @abstractmethod
    def flee_from_pos(self, pos: tuple[int, int]) -> bool:
        pass
