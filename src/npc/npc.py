from __future__ import annotations

import random
from typing import Callable

import pygame

from src.enums import (
    EntityState,
    FarmingTool,
    InventoryResource,
    Layer,
    SeedType,
    StudyGroup,
)
from src.gui.interface.emotes import NPCEmoteManager
from src.npc.bases.npc_base import NPCBase
from src.npc.behaviour.npc_behaviour_tree import NPCIndividualContext
from src.overlay.soil import SoilManager
from src.settings import Coordinate
from src.sprites.entities.character import Character
from src.sprites.setup import EntityAsset
from src.timer import Timer


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
        sickness_allowed: bool,
    ):
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
            emote_manager=emote_manager,
        )
        self.start_tile_pos = self.get_tile_pos()  # capture the NPC start position
        self.soil_area = soil_manager.get_area(self.study_group)
        self.has_necklace = False
        self.has_hat = False
        self.has_horn = False
        self.has_outgroup_skin = False
        self.sickness_allowed = sickness_allowed

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
            InventoryResource.BEETROOT: 0,
            InventoryResource.CARROT: 0,
            InventoryResource.EGGPLANT: 0,
            InventoryResource.PUMPKIN: 0,
            InventoryResource.PARSNIP: 0,
            InventoryResource.CORN_SEED: 999,
            InventoryResource.TOMATO_SEED: 999,
            InventoryResource.BEETROOT_SEED: 999,
            InventoryResource.CARROT_SEED: 999,
            InventoryResource.EGGPLANT_SEED: 999,
            InventoryResource.PUMPKIN_SEED: 999,
            InventoryResource.PARSNIP_SEED: 999,
        }

        self.assign_outfit_ingroup()

        # NPC health / sickness / death

        self.probability_to_get_sick = (
            0.3 if self.has_goggles else 0.6
        ) < random.random()
        # set a timer to get the NPC sick after a random time
        self.sick_timer = Timer(
            random.randint(5, 20) * 1000,
            autostart=self.sickness_allowed,
            func=self.get_sick,
        )

        self.is_sick = False
        self.is_dead = False
        self.hp = 100
        # how fast the NPC dies after getting sick
        self.die_rate = random.randint(35, 75)

    def set_allowed_seeds(self, allowed_seeds: dict[str]) -> None:
        seed_types = []
        for seed_type in SeedType:
            if SeedType._AS_IRS[seed_type].as_serialised_string() in allowed_seeds:
                seed_types.append(seed_type)
        # using NPCIndividualContext, however it would make more sense to use NPCSharedContext,
        # but not sure how to set it :-(
        self.behaviour_tree_context.allowed_seeds = seed_types

    def set_sickness_allowed(self, sickness_allowed: bool) -> None:
        self.sickness_allowed = sickness_allowed
        if sickness_allowed:
            if not self.sick_timer.active:
                self.sick_timer.activate()
        else:
            if self.sick_timer.active:
                self.sick_timer.deactivate()
            self.is_sick = False
            self.hp = 100

    def get_personal_soil_area_tiles(self, tile_type: str) -> list[tuple[int, int]]:
        """
        Get the soil area that the NPC is responsible for (row of farmable tiles)
        :param tile_type: "untilled", "unplanted", "harvestable", "unwatered"
        :return: list of tiles that the NPC is responsible for, e.g. a ROW of untilled soil
        """
        if tile_type == "untilled":
            tiles = self.soil_area.untilled_tiles
        elif tile_type == "unplanted":
            tiles = self.soil_area.unplanted_tiles
        elif tile_type == "harvestable":
            tiles = self.soil_area.harvestable_tiles
        elif tile_type == "unwatered":
            tiles = self.soil_area.unwatered_tiles
        else:
            raise ValueError("Invalid tile type")
        # include only tiles that are in the same row as the NPC's start position
        return [
            # 1 is the y-coordinate of tile position to pick the row
            tile
            for tile in tiles
            if tile[1] == self.start_tile_pos[1]
        ]

    def get_personal_adjacent_untilled_tiles(self) -> list[tuple[int, int]]:
        """
        Get all adjacent untilled tiles to the NPC's personal soil area that has been farmed
        :return:
            list of adjacent untilled tiles to the NPC's personal soil area that has been farmed
            if there are no personal untilled tiles, return an empty list
            if there are no personal farmed tiles, return list all untilled tiles
        """
        # If no personal untilled tiles, return an empty list
        untilled_tiles = self.get_personal_soil_area_tiles("untilled")
        if not untilled_tiles:
            return []

        # Retrieve all personal tiles that have been farmed
        farmed_tiles = []
        for tile_type in ["unplanted", "harvestable", "unwatered"]:
            farmed_tiles.extend(self.get_personal_soil_area_tiles(tile_type))

        # If there are no personal farmed tiles, return all untilled tiles
        if not farmed_tiles:
            return untilled_tiles

        # check left from leftmost farmed tile and right from rightmost farmed tile
        farmed_tiles.sort(key=lambda x: x[0])
        left_from_leftmost_farmed_tile = (farmed_tiles[0][0] - 1, farmed_tiles[0][1])
        right_from_rightmost_farmed_tile = (
            farmed_tiles[-1][0] + 1,
            farmed_tiles[-1][1],
        )
        adjacent_tiles = [
            left_from_leftmost_farmed_tile,
            right_from_rightmost_farmed_tile,
        ]

        # Pick untilled tiles that are adjacent to the farmed tiles
        adjacent_untilled_tiles = [
            tile for tile in untilled_tiles if tile in adjacent_tiles
        ]
        return adjacent_untilled_tiles

    def assign_outfit_ingroup(self, ingroup_40p_hat_necklace_appearance: bool = False):
        # 40% of the ingroup NPCs should wear a hat and a necklace, and 60% of the ingroup NPCs should only wear the hat
        if self.study_group == StudyGroup.INGROUP:
            if ingroup_40p_hat_necklace_appearance:
                if random.random() <= 0.4:
                    self.has_necklace = True
                    self.has_hat = True
                else:
                    self.has_necklace = False
                    self.has_hat = True
            else:
                self.has_necklace = False
                self.has_hat = False
        else:
            self.has_necklace = False
            self.has_hat = False
            self.has_horn = True
            self.has_outgroup_skin = True

    # NPC sickness
    def get_sick(self):
        # if wearing goggles, the probability of getting sick is halved
        self.is_sick = self.probability_to_get_sick < random.random()

    def die(self):
        self.is_dead = True
        self.has_necklace = False
        self.has_hat = False
        self.has_horn = False

        # set "dead" image, this could be a tombstone or a dead body, for example
        if self.study_group == StudyGroup.OUTGROUP:
            skin_state = EntityState(f"outgroup_{self.state.value}")
            self.image = self.assets[skin_state][self.facing_direction].get_frame(0)
        else:
            self.image = self.assets[self.state][self.facing_direction].get_frame(0)
        self.image.set_alpha(130)
        self.image = pygame.transform.rotate(self.image, 90)

        # remove from collision sprites so doesn't prevent farming or block other characters
        self.remove(self.collision_sprites)

    def manage_sickness(self, dt):
        # if NPC is not sick yet, check if it gets sick
        if self.sick_timer.active:
            self.sick_timer.update()
        elif self.is_sick and not self.is_dead:
            # if NPC is sick, decrease health, speed and alpha
            self.hp -= int(self.die_rate * dt)
            self.speed = self.hp
            self.image_alpha = 30 + int(150 * (self.hp / 100))
            self.image.set_alpha(self.image_alpha)
            if self.hp <= 0:
                self.die()

    def update(self, dt):
        if self.sickness_allowed:
            self.manage_sickness(dt)
        if self.is_dead:
            return
        super().update(dt)

        self.emote_manager.update_obj(
            self, (self.rect.centerx - 47, self.rect.centery - 128)
        )

    def update_blocked(self, dt):
        """the scripted sequence needs to display emote box even when NPC is blocked"""
        if self.is_dead:
            return
        super().update_blocked(dt)

        self.emote_manager.update_obj(
            self, (self.rect.centerx - 47, self.rect.centery - 128)
        )

    def draw(self, display_surface: pygame.Surface, rect: pygame.Rect, camera):
        if self.is_dead:
            # display only the dead NPC image if dead
            display_surface.blit(self.image, rect)
            return

        super().draw(display_surface, rect, camera)
