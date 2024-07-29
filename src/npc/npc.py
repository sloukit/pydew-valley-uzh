from __future__ import annotations

from typing import Callable

import pygame

from src.enums import FarmingTool, InventoryResource, Layer
from src.gui.interface.emotes import NPCEmoteManager
from src.npc.bases.npc_base import NPCBase
from src.npc.behaviour.npc_behaviour_tree import (
    NPCBehaviourTree,
    NPCBehaviourTreeContext
)
from src.npc.setup import AIData
from src.overlay.soil import SoilLayer
from src.settings import Coordinate
from src.sprites.character import Character
from src.sprites.setup import EntityAsset


class NPC(NPCBase):
    def __init__(
            self,
            pos: Coordinate,
            assets: EntityAsset,
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable[
                [FarmingTool, tuple[int, int], Character], None
            ],
            soil_layer: SoilLayer,
            emote_manager: NPCEmoteManager
    ):
        self.soil_layer = soil_layer

        self.emote_manager = emote_manager

        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,

            apply_tool=apply_tool,

            pf_matrix=AIData.Matrix,
            pf_grid=AIData.Grid,
            pf_finder=AIData.ChickenPathFinder,

            z=Layer.MAIN
        )

        # TODO: Ensure that the NPC always has all needed seeds it needs
        #  in its inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 999,
            InventoryResource.TOMATO_SEED: 999,
        }

    def exit_idle(self):
        NPCBehaviourTree.tree.run(NPCBehaviourTreeContext(self))

    def update(self, dt):
        super().update(dt)

        self.emote_manager.update_obj(self, (self.rect.centerx - 47, self.rect.centery - 128))
