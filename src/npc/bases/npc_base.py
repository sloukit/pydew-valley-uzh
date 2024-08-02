from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from typing import ClassVar

import pygame
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.enums import FarmingTool
from src.npc.behaviour.ai_behaviour import AIBehaviour
from src.overlay.soil import SoilLayer
from src.settings import Coordinate
from src.sprites.character import Character
from src.sprites.setup import EntityAsset


class NPCBase(Character, AIBehaviour, ABC):
    pf_matrix: ClassVar[list[list[int]] | None] = None
    pf_grid: ClassVar[Grid | None] = None
    pf_finder: ClassVar[AStarFinder | None] = None

    soil_layer: SoilLayer

    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_sprites: pygame.sprite.Group,
        apply_tool: Callable[[FarmingTool, tuple[float, float], Character], None],
        z: int,
    ):
        Character.__init__(
            self,
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,
            apply_tool=apply_tool,
            z=z,
        )
        AIBehaviour.__init__(self)

        self.speed = 250
