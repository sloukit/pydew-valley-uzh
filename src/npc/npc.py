from __future__ import annotations

import random
from typing import Callable

import pygame

from src.enums import FarmingTool, InventoryResource, Layer, StudyGroup
from src.gui.interface.emotes import NPCEmoteManager
from src.npc.bases.npc_base import NPCBase
from src.npc.behaviour.npc_behaviour_tree import NPCIndividualContext
from src.overlay.soil import SoilManager
from src.settings import Coordinate
from src.sprites.entities.character import Character
from src.sprites.setup import EntityAsset


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

        self.start_tile_pos = self.get_tile_pos()  # capture the NPC start position
        self.soil_area = soil_manager.get_area(self.study_group)
        self.has_necklace = False
        self.has_hat = False
        self.has_horn = False
        self.has_outgroup_skin = False

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
            self.has_horn = True
            self.has_outgroup_skin = True

    def update(self, dt):
        super().update(dt)

        self.emote_manager.update_obj(
            self, (self.rect.centerx - 47, self.rect.centery - 128)
        )
