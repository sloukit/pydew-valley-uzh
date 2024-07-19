from __future__ import annotations

import pygame  # noqa
from typing import Callable
from pygame.math import Vector2 as vector
from src import settings, savefile, support
from src.sprites.entities.entity import Entity
from src.enums import InventoryResource, FarmingTool, ItemToUse
from src.settings import SCALE_FACTOR

_NONSEED_INVENTORY_DEFAULT_AMOUNT = 20
_SEED_INVENTORY_DEFAULT_AMOUNT = 5
_INV_DEFAULT_AMOUNTS = (
    _NONSEED_INVENTORY_DEFAULT_AMOUNT,
    _SEED_INVENTORY_DEFAULT_AMOUNT
)


class Player(Entity):
    def __init__(
            self,
            game,
            pos: settings.Coordinate,
            frames,
            groups,
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable,
            interact: Callable,
            sounds: settings.SoundDict,
            font: pygame.font.Font):

        save_data = savefile.load_savefile()
        self.game = game

        super().__init__(
            pos,
            frames,
            groups,
            collision_sprites,
            (44 * SCALE_FACTOR, 40 * SCALE_FACTOR),
            apply_tool
        )

        # movement
        self.keybinds = self.import_controls()
        self.controls = {}
        self.speed = 250
        self.blocked = False
        self.paused = False
        self.font = font
        self.interact = interact

        # menus

        self.current_tool = save_data.get("current_tool", FarmingTool.get_first_tool_id())
        self.tool_index = self.current_tool.value - 1

        self.current_seed = save_data.get("current_seed", FarmingTool.get_first_seed_id())
        self.seed_index = self.current_seed.value - FarmingTool.get_first_seed_id().value

        # inventory
        self.inventory = {
            res: save_data["inventory"].get(
                res.as_serialised_string(),
                _SEED_INVENTORY_DEFAULT_AMOUNT if res >= InventoryResource.CORN_SEED else
                _NONSEED_INVENTORY_DEFAULT_AMOUNT
            )
            for res in InventoryResource.__members__.values()
        }
        self.money = save_data.get("money", 200)

        # sounds
        self.sounds = sounds

    def save(self):
        # We compact the inventory first, i.e. remove any default values if they didn't change.
        # This is to save space in the save file.
        compacted_inv = self.inventory.copy()
        key_set = list(compacted_inv.keys())
        for k in key_set:
            # The default amount for each resource differs
            # according to whether said resource is a seed or not
            # (5 units for seeds, 20 units for everything else).
            if self.inventory[k] == _INV_DEFAULT_AMOUNTS[k.is_seed()]:
                del compacted_inv[k]
        savefile.save(self.current_tool, self.current_seed, self.money, compacted_inv)

    @staticmethod
    def import_controls():
        try:
            data = support.load_data('keybinds.json')
            if len(data) == len(settings.KEYBINDS):
                return data
        except FileNotFoundError:
            pass
        support.save_data(settings.KEYBINDS, 'keybinds.json')
        return settings.KEYBINDS

        # controls

    def update_controls(self):
        controls = {}
        keys = pygame.key.get_just_pressed()
        linear_keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        for control_name, control in self.keybinds.items():
            control_type = control['type']
            value = control['value']
            if control_type == 'key':
                controls[control_name] = keys[value]
            if control_type == 'mouse':
                controls[control_name] = mouse_buttons[value]
            if control_name in ('up', 'down', 'left', 'right'):
                controls[control_name] = linear_keys[value]
        return controls

    def input(self):
        self.controls = self.update_controls()

        # movement
        if not self.tool_active and not self.blocked:
            self.direction.x = int(self.controls['right']) - int(self.controls['left'])
            self.direction.y = int(self.controls['down']) - int(self.controls['up'])
            # self.direction = self.direction.normalize() if self.direction else self.direction

            # tool switch
            if self.controls['next tool']:
                self.tool_index = (self.tool_index + 1) % len(self.available_tools)
                self.current_tool = FarmingTool(self.tool_index + FarmingTool.get_first_tool_id())

            # tool use
            if self.controls['use']:
                self.tool_active = True
                self.frame_index = 0
                self.direction = vector()
                if self.current_tool.is_swinging_tool():
                    self.sounds['swing'].play()

            # seed switch
            if self.controls['next seed']:
                self.seed_index = (self.seed_index + 1) % len(self.available_seeds)
                self.current_seed = FarmingTool(self.seed_index + FarmingTool.get_first_seed_id())

            # seed used
            if self.controls['plant']:
                self.use_tool(ItemToUse.SEED)

            # interact
            if self.controls['interact']:
                self.interact()

    def get_current_tool_string(self):
        return self.available_tools[self.tool_index]

    def get_current_seed_string(self):
        return self.available_seeds[self.seed_index]

    def add_resource(self, resource, amount=1):
        super().add_resource(resource, amount)
        self.sounds['success'].play()
    
    def update_keybinds(self):
        self.keybinds = self.import_controls()

    def update(self, dt):
        self.input()
        super().update(dt)
