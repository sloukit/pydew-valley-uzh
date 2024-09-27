from __future__ import annotations

import random
from typing import Callable

import pygame

from src.enums import FarmingTool, InventoryResource, Layer, StudyGroup
from src.gui.interface.emotes import NPCEmoteManager
from src.npc.bases.npc_base import NPCBase
from src.npc.behaviour.npc_behaviour_tree import NPCIndividualContext
from src.overlay.soil import SoilManager
from src.settings import Coordinate, HEALTH_DECAY_VALUE
from src.sprites.entities.character import Character
from src.sprites.setup import EntityAsset

from src.timer import Timer
import time


class NPC(NPCBase):
    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_sprites: pygame.sprite.Group,
        study_group: StudyGroup,
        apply_tool: Callable[[FarmingTool, tuple[float, float], Character], None],
        plant_collision: Callable[[Character], None],
        soil_manager: SoilManager,
        emote_manager: NPCEmoteManager,
        tree_sprites: pygame.sprite.Group,
    ):
        self.emote_manager = emote_manager

        self.tree_sprites = tree_sprites

        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,
            study_group=study_group,
            apply_tool=apply_tool,
            plant_collision=plant_collision,
            behaviour_tree_context=NPCIndividualContext(self),
            z=Layer.MAIN,
        )

        self.soil_area = soil_manager.get_area(self.study_group)
        self.has_necklace = False
        self.has_hat = False

        self.speed = 250
        self.original_speed = 250
        self.created_time = time.time()
        self.delay_time_speed = 0.25

        # TODO: Ensure that the NPC always has all needed seeds it needs
        #  in its inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.ORANGE: 0,
            InventoryResource.PEACH: 0,
            InventoryResource.PEAR: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 999,
            InventoryResource.TOMATO_SEED: 999,
        }

        self.assign_outfit_ingroup()

    def assign_outfit_ingroup(self):
        # 40% of the ingroup NPCs should wear a hat and a necklace, and 60% of the ingroup NPCs should only wear the hat
        if self.study_group == StudyGroup.INGROUP:
            if random.random() <= 0.4:
                self.has_necklace = True
                self.has_hat = True
            else:
                self.has_necklace = False
                self.has_hat = True
        else:
            self.has_necklace = False
            self.has_hat = False

    def update(self, dt):
        self.set_transparency_asper_sick()
        self.set_speed_asper_sick()
        super().update(dt)

        self.emote_manager.update_obj(
            self, (self.rect.centerx - 47, self.rect.centery - 128)
        )

    def set_transparency_asper_sick(self):
        currTime = time.time()
        elapsed_t = currTime - self.created_time
        #print("elasped: ",elapsed_t)
        alpha_v = 255 - (elapsed_t * HEALTH_DECAY_VALUE*100)
        self.image.set_alpha(alpha_v)
        print("npc t: ",alpha_v)##debug
        #print(elapsed_t*HEALTH_DECAY_VALUE)##debug

    def set_speed_asper_sick(self):
        cTime = time.time()
        elapsedTime = cTime- self.created_time
        if elapsedTime >= self.delay_time_speed:
            self.speed = self.original_speed - (elapsedTime * HEALTH_DECAY_VALUE*100)
            print("npc speed: ",self.speed)##debug