from __future__ import annotations

from typing import Callable, Type

import pygame  # noqa

from src import savefile, support
from src.controls import Controls
from src.enums import InventoryResource, FarmingTool, ItemToUse
from src.gui.interface.emotes import PlayerEmoteManager
from src.npc.bases.npc_base import NPCBase
from src.settings import Coordinate, SoundDict
from src.sprites.character import Character
from src.sprites.entities.entity import Entity
from src.sprites.setup import EntityAsset

_NONSEED_INVENTORY_DEFAULT_AMOUNT = 20
_SEED_INVENTORY_DEFAULT_AMOUNT = 5
_INV_DEFAULT_AMOUNTS = (
    _NONSEED_INVENTORY_DEFAULT_AMOUNT,
    _SEED_INVENTORY_DEFAULT_AMOUNT
)


class Player(Character):
    keybinds: dict
    controls: Type[Controls]

    blocked: bool
    paused: bool
    font: pygame.font.Font
    interact: Callable[[], None]
    sounds: SoundDict

    def __init__(
            self,
            pos: Coordinate,
            assets: EntityAsset,
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable[
                [FarmingTool, tuple[int, int], Character], None
            ],
            interact: Callable[[], None],
            emote_manager: PlayerEmoteManager,
            sounds: SoundDict,
            font: pygame.font.Font
    ):

        save_data = savefile.load_savefile()

        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,
            apply_tool=apply_tool
        )

        # movement
        self.controls = Controls
        self.load_controls()
        self.speed = 250
        self.blocked = False
        self.paused = False
        self.font = font
        self.interact = interact

        self.emote_manager = emote_manager
        self.focused_entity: NPCBase | None = None

        # load saved tools
        self.current_tool = save_data.get(
            "current_tool", FarmingTool.get_first_tool_id()
        )
        self.current_seed = save_data.get(
            "current_seed", FarmingTool.get_first_seed_id()
        )

        # inventory
        self.inventory = {
            res: save_data["inventory"].get(
                res.as_serialised_string(),
                _SEED_INVENTORY_DEFAULT_AMOUNT
                if res >= InventoryResource.CORN_SEED else
                _NONSEED_INVENTORY_DEFAULT_AMOUNT
            )
            for res in InventoryResource.__members__.values()
        }
        self.money = save_data.get("money", 200)

        # sounds
        self.sounds = sounds

    def focus_entity(self, entity: Entity):
        if self.focused_entity:
            self.focused_entity.unfocus()
        self.focused_entity = entity
        self.focused_entity.focus()

    def unfocus_entity(self):
        if self.focused_entity:
            self.focused_entity.unfocus()
        self.focused_entity = None

    def save(self):
        # We compact the inventory first,
        # i.e. remove any default values if they didn't change.
        # This is to save space in the save file.
        compacted_inv = self.inventory.copy()
        key_set = list(compacted_inv.keys())
        for k in key_set:
            # The default amount for each resource differs
            # according to whether said resource is a seed or not
            # (5 units for seeds, 20 units for everything else).
            if self.inventory[k] == _INV_DEFAULT_AMOUNTS[k.is_seed()]:
                del compacted_inv[k]
        savefile.save(
            self.current_tool, self.current_seed, self.money, compacted_inv
        )

    def load_controls(self):
        self.controls.load_default_keybinds()
        try:
            data = support.load_data('keybinds.json')
            self.controls.from_dict(data)
        except FileNotFoundError:
            support.save_data(self.controls.as_dict(), 'keybinds.json')

    # controls
    def update_controls(self):
        keys_just_pressed = pygame.key.get_just_pressed()
        keys_pressed = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()

        for control in self.controls.all_controls():
            is_mouse_event = control.control_value in (1, 2, 3)

            if is_mouse_event:
                is_event_active = mouse_pressed[control.control_value - 1]
                control.click = is_event_active
                control.hold = is_event_active
            else:
                control.click = keys_just_pressed[control.control_value]
                control.hold = keys_pressed[control.control_value]

    def handle_controls(self):
        self.update_controls()

        # movement
        if (not self.tool_active
                and not self.blocked
                and not self.emote_manager.emote_wheel.visible):

            self.direction.x = (int(self.controls.RIGHT.hold)
                                - int(self.controls.LEFT.hold))

            self.direction.y = (int(self.controls.DOWN.hold)
                                - int(self.controls.UP.hold))

            if self.direction:
                self.direction = self.direction.normalize()

            # tool switch
            if self.controls.NEXT_TOOL.click:
                tool_index = (
                        (self.current_tool.value
                         - FarmingTool.get_first_tool_id().value + 1)
                        % FarmingTool.get_tool_count()
                )
                self.current_tool = FarmingTool(
                    tool_index + FarmingTool.get_first_tool_id()
                )

            # tool use
            if self.controls.USE.click:
                self.tool_active = True
                self.frame_index = 0
                self.direction = pygame.Vector2()
                if self.current_tool.is_swinging_tool():
                    self.sounds['swing'].play()

            # seed switch
            if self.controls.NEXT_SEED.click:
                seed_index = (
                        (self.current_seed.value
                         - FarmingTool.get_first_seed_id().value + 1)
                        % FarmingTool.get_seed_count()
                )
                self.current_seed = FarmingTool(
                    seed_index + FarmingTool.get_first_seed_id()
                )

            # seed used
            if self.controls.PLANT.click:
                self.use_tool(ItemToUse.SEED)

            # interact
            if self.controls.INTERACT.click:
                self.interact()

        # emotes
        if not self.blocked:
            if self.controls.EMOTE_WHEEL.click:
                self.emote_manager.toggle_emote_wheel()
                if self.emote_manager.emote_wheel.visible:
                    self.direction = pygame.Vector2()

            if self.emote_manager.emote_wheel.visible:
                if self.controls.RIGHT.click:
                    self.emote_manager.emote_wheel.emote_index += 1

                if self.controls.LEFT.click:
                    self.emote_manager.emote_wheel.emote_index -= 1

                if self.controls.USE.click:
                    self.emote_manager.show_emote(
                        self, self.emote_manager.emote_wheel._current_emote
                    )
                    self.emote_manager.toggle_emote_wheel()

    def move(self, dt: float):
        self.hitbox_rect.update(
            (self.rect.x + self._current_hitbox.x,
             self.rect.y + self._current_hitbox.y),
            self._current_hitbox.size
        )

        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.check_collision()

        self.rect.update(
            (self.hitbox_rect.x - self._current_hitbox.x,
             self.hitbox_rect.y - self._current_hitbox.y),
            self.rect.size
        )

    def get_current_tool_string(self):
        return self.current_tool.as_serialised_string()

    def get_current_seed_string(self):
        return self.current_seed.as_serialised_string()

    def add_resource(self, resource: InventoryResource, amount: int = 1):
        super().add_resource(resource, amount)
        self.sounds['success'].play()

    def update(self, dt):
        self.handle_controls()
        super().update(dt)

        self.emote_manager.update_obj(self, (self.rect.centerx - 47, self.rect.centery - 128))
        self.emote_manager.update_emote_wheel(self.rect.center)
