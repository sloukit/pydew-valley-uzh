from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from typing import ClassVar

import pygame
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.enums import FarmingTool, StudyGroup
from src.gui.interface.emotes import NPCEmoteManager
from src.npc.bases.ai_behaviour import AIBehaviour
from src.npc.behaviour.ai_behaviour_tree_base import ContextType
from src.overlay.soil import SoilArea
from src.settings import Coordinate
from src.sprites.entities.character import Character
from src.sprites.setup import EntityAsset


class NPCBase(Character, AIBehaviour, ABC):
    pf_matrix: ClassVar[list[list[int]] | None] = None
    pf_grid: ClassVar[Grid | None] = None
    pf_finder: ClassVar[AStarFinder | None] = None

    soil_area: SoilArea
    tree_sprites: pygame.sprite.Group

    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_sprites: pygame.sprite.Group,
        study_group: StudyGroup,
        apply_tool: Callable[[FarmingTool, tuple[float, float], Character], None],
        plant_collision: Callable[[Character], None],
        behaviour_tree_context: ContextType,
        z: int,
        emote_manager: NPCEmoteManager,
        npc_id: int,
    ):
        Character.__init__(
            self,
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,
            study_group=study_group,
            apply_tool=apply_tool,
            plant_collision=plant_collision,
            z=z,
        )
        AIBehaviour.__init__(self, behaviour_tree_context=behaviour_tree_context)
        self.emote_manager = emote_manager
        self.npc_id = npc_id
        self.speed = 250
