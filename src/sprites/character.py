from abc import ABC
from collections.abc import Callable
from typing import Self

import pygame

from src import settings
from src.enums import (
    FarmingTool, InventoryResource, ItemToUse, EntityState,
    Layer
)
from src.sprites.entities.entity import Entity
from src.sprites.setup import EntityAsset


class Character(Entity, ABC):
    current_tool: FarmingTool
    tool_active: bool
    just_used_tool: bool
    apply_tool: Callable[[FarmingTool, tuple[float, float], Self], None]

    current_seed: FarmingTool

    def __init__(
            self,
            pos: settings.Coordinate,
            assets: EntityAsset,
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable[
                [FarmingTool, tuple[float, float], Self], None
            ],
            z=Layer.MAIN
    ):
        Entity.__init__(
            self,
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,

            z=z
        )

        # tools
        self.current_tool = FarmingTool(FarmingTool.get_first_tool_id())
        self.tool_active = False
        self.just_used_tool = False
        self.apply_tool = apply_tool

        # seeds
        self.current_seed = FarmingTool(FarmingTool.get_first_seed_id())

        # inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 0,
            InventoryResource.TOMATO_SEED: 0,
        }

        # Not all Characters can go to the market,
        # so those that can't should not have money either
        self.money = 0

    def get_state(self):
        if self.tool_active:
            self.state = EntityState(self.current_tool.as_serialised_string())
        else:
            super().get_state()

    def animate(self, dt):
        super().animate(dt)
        if self.tool_active:
            if self.frame_index > len(self._current_ani):
                self.tool_active = False
                self.just_used_tool = False
                # The state has to be changed to prevent the first image from
                # being displayed a second time, because the state updates
                # before the call to Entity.animate
                self.state = EntityState.IDLE
            else:
                if (round(self.frame_index) == len(self._current_ani) - 1
                        and not self.just_used_tool):
                    self.just_used_tool = True
                    self.use_tool(ItemToUse.REGULAR_TOOL)

    def use_tool(self, option: ItemToUse):
        self.apply_tool(
            (self.current_tool, self.current_seed)[option],
            self.get_target_pos(), self
        )

    def add_resource(self, resource, amount=1):
        self.inventory[resource] += amount
