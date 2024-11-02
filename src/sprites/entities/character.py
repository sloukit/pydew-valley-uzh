from abc import ABC
from collections.abc import Callable
from typing import Self

import pygame

from src import settings
from src.enums import (
    Direction,
    EntityState,
    FarmingTool,
    InventoryResource,
    ItemToUse,
    Layer,
    StudyGroup,
)
from src.sprites.entities.entity import Entity
from src.sprites.setup import EntityAsset


class Character(Entity, ABC):
    current_tool: FarmingTool
    tool_active: bool
    just_used_tool: bool
    apply_tool: Callable[[FarmingTool, tuple[float, float], Self], None]
    study_group: StudyGroup
    has_goggles: settings.GogglesStatus

    current_seed: FarmingTool

    def __init__(
        self,
        pos: settings.Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_sprites: pygame.sprite.Group,
        study_group: StudyGroup,
        apply_tool: Callable[[FarmingTool, tuple[float, float], Self], None],
        plant_collision: Callable[[Self], None],
        z=Layer.MAIN,
    ):
        Entity.__init__(
            self,
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,
            z=z,
        )

        # TODO: implement compatibility with this, e.g. NPCs reacting differently to
        #  emotes depending on the group they belong to and the player's
        self.study_group = study_group
        self.has_goggles = None

        self.facing_direction = Direction.DOWN
        self.image_alpha = 255

        # tools
        self.current_tool = FarmingTool(FarmingTool.get_first_tool_id())
        self.tool_active = False
        self.just_used_tool = False
        self.apply_tool = apply_tool

        # seeds
        self.current_seed = FarmingTool(FarmingTool.get_first_seed_id())

        self.plant_collision = plant_collision

        # inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.BLACKBERRY: 0,
            InventoryResource.BLUEBERRY: 0,
            InventoryResource.RASPBERRY: 0,
            InventoryResource.ORANGE: 0,
            InventoryResource.PEACH: 0,
            InventoryResource.PEAR: 0,
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
                if (
                    round(self.frame_index) == len(self._current_ani) - 1
                    and not self.just_used_tool
                ):
                    self.just_used_tool = True
                    self.use_tool(ItemToUse.REGULAR_TOOL)

    def use_tool(self, option: ItemToUse):
        self.apply_tool(
            (self.current_tool, self.current_seed)[option], self.get_target_pos(), self
        )

    def add_resource(self, resource, amount=1):
        self.inventory[resource] += amount

    def remove_resource(self, resource, amount=1) -> bool:
        if self.inventory[resource] >= amount:
            self.inventory[resource] -= amount
            return True
        return False

    def draw(self, display_surface: pygame.Surface, rect: pygame.Rect, camera):
        # super().draw(display_surface, rect, camera)
        blit_list = []

        # Render the necklace if the character has it and is in the ingroup
        is_in_ingroup = self.study_group == StudyGroup.INGROUP

        if is_in_ingroup:
            super().draw(display_surface, rect, camera)
            if self.has_necklace:
                necklace_state = EntityState(f"necklace_{self.state.value}")
                necklace_ani = self.assets[necklace_state][self.facing_direction]
                necklace_frame = necklace_ani.get_frame(self.frame_index)
                necklace_frame.set_alpha(self.image_alpha)
                blit_list.append((necklace_frame, rect))

        # Render the goggles
        if self.has_goggles:
            goggles_state = EntityState(f"goggles_{self.state.value}")
            goggles_ani = self.assets[goggles_state][self.facing_direction]
            goggles_frame = goggles_ani.get_frame(self.frame_index)
            goggles_frame.set_alpha(self.image_alpha)
            blit_list.append((goggles_frame, rect))

        # Render the hat/horn (depending on the group)
        if is_in_ingroup:
            if self.has_hat:
                hat_state = EntityState(f"hat_{self.state.value}")
                hat_ani = self.assets[hat_state][self.facing_direction]
                hat_frame = hat_ani.get_frame(self.frame_index)
                # hat_frame.set_alpha(self.image_alpha)  # hat is always visible, looks silly otherwise
                blit_list.append((hat_frame, rect))

        elif self.study_group == StudyGroup.OUTGROUP:
            if self.has_outgroup_skin:
                skin_state = EntityState(f"outgroup_{self.state.value}")
                skin_ani = self.assets[skin_state][self.facing_direction]
                skin_frame = skin_ani.get_frame(self.frame_index)
                skin_frame.set_alpha(self.image_alpha)
                blit_list.append((skin_frame, rect))

            if self.has_horn:
                horn_state = EntityState(f"horn_{self.state.value}")
                horn_ani = self.assets[horn_state][self.facing_direction]
                horn_frame = horn_ani.get_frame(self.frame_index)
                horn_frame.set_alpha(self.image_alpha)
                blit_list.append((horn_frame, rect))

        display_surface.fblits(blit_list)

    def update(self, dt: float):
        super().update(dt)
        self.plant_collision(self)
