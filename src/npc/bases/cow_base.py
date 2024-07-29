from __future__ import annotations

from abc import ABC, abstractmethod

import pygame
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.bases.animal import Animal
from src.npc.behaviour.ai_behaviour import AIBehaviour
from src.settings import Coordinate
from src.sprites.character import Character
from src.sprites.setup import EntityAsset


class CowBase(Animal, AIBehaviour, ABC):
    fleeing: bool

    player: Character

    def __init__(
            self,
            pos: Coordinate,
            assets: EntityAsset,
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,

            pf_matrix: list[list[int]],
            pf_grid: Grid,
            pf_finder: AStarFinder,

            z: int
    ):
        Animal.__init__(
            self,
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,

            z=z
        )
        AIBehaviour.__init__(
            self,
            pf_matrix=pf_matrix,
            pf_grid=pf_grid,
            pf_finder=pf_finder
        )

        self.speed = 150

    @abstractmethod
    def flee_from_pos(self, pos: tuple[int, int]) -> bool:
        pass
