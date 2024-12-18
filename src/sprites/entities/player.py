from __future__ import annotations

import time
from typing import Any, Callable, Type

import pygame  # noqa

from src import support
from src.controls import Controls
from src.enums import FarmingTool, InventoryResource, ItemToUse, StudyGroup
from src.events import OPEN_INVENTORY, START_QUAKE, post_event
from src.gui.interface.emotes import PlayerEmoteManager
from src.npc.bases.npc_base import NPCBase
from src.savefile import SaveFile
from src.settings import BATH_STATUS_TIMEOUT, DEBUG_MODE_VERSION, Coordinate, SoundDict
from src.sprites.entities.character import Character
from src.sprites.entities.entity import Entity
from src.sprites.setup import EntityAsset

_NONSEED_INVENTORY_DEFAULT_AMOUNT = 20
_SEED_INVENTORY_DEFAULT_AMOUNT = 5
_INV_DEFAULT_AMOUNTS = (
    _NONSEED_INVENTORY_DEFAULT_AMOUNT,
    _SEED_INVENTORY_DEFAULT_AMOUNT,
)


class Player(Character):
    keybinds: dict
    controls: Type[Controls]

    blocked: bool
    paused: bool
    interact: Callable[[], None]
    sounds: SoundDict

    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_sprites: pygame.sprite.Group,
        controls: Type[Controls],
        apply_tool: Callable[[FarmingTool, tuple[float, float], Character], None],
        plant_collision: Callable[[Character], None],
        interact: Callable[[], None],
        emote_manager: PlayerEmoteManager,
        sounds: SoundDict,
        hp: int,
        bathstat: bool,
        bath_time: float,
        save_file: SaveFile,
        round_config: dict[str, Any],
        get_game_version: Callable[[], int],
    ) -> None:
        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,
            study_group=StudyGroup.INGROUP,
            apply_tool=apply_tool,
            plant_collision=plant_collision,
        )

        self.round_config = round_config
        self.get_game_version = get_game_version
        # movement
        self.save_file = save_file
        self.controls = controls
        self.load_controls()
        self.original_speed = 250
        self.speed = 250
        self.blocked = False
        self.paused = False
        self.interact = interact
        self.bathstat = bathstat
        self.bath_time = bath_time
        self.has_goggles = save_file.has_goggles
        self.has_necklace = save_file.has_necklace
        self.has_hat = save_file.has_hat
        self.has_horn = save_file.has_horn
        self.has_outgroup_skin = save_file.has_outgroup_skin
        self.study_group: StudyGroup = save_file.study_group

        self.emote_manager = emote_manager
        self.focused_entity: NPCBase | None = None
        # load saved tools
        self.current_tool = save_file.current_tool
        self.current_seed = save_file.current_seed
        # inventory
        self.inventory = save_file.inventory.copy()
        self.money = save_file.money

        # sounds
        self.sounds = sounds

        self.hp = hp
        self.created_time = time.time()
        self.delay_time_speed = 0.25

        # check if the zoom is allowed
        self.zoom_allowed = False

        # watch the player behaviour in achieving tutorial tasks
        self.bought_sold = False
        self.minigame_finished = False
        self.ingroup_member_interacted = False
        self.outgroup_member_interacted = False

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
        self.save_file.inventory = compacted_inv
        self.save_file.save()

    def load_controls(self):
        self.controls.load_default_keybinds()
        try:
            data = support.load_data("keybinds.json")
            self.controls.from_dict(data)
        except FileNotFoundError:
            support.save_data(self.controls.as_dict(), "keybinds.json")

    def assign_seed(self, seed: str):
        computed_value = FarmingTool.from_serialised_string(seed)
        if not computed_value.is_seed():
            raise ValueError("given value is not a seed type")
        self.current_seed = computed_value

    def assign_tool(self, tool: str):
        computed_value = FarmingTool.from_serialised_string(tool)
        if computed_value.is_seed():
            raise ValueError("given value is a seed")
        self.current_tool = computed_value

    def handle_controls(self):
        # the scripted sequence needs the emote_manager to work even when NPC is blocked"""
        if self.emote_manager.emote_wheel.visible:
            if self.controls.RIGHT.click:
                self.emote_manager.emote_wheel.emote_index += 1

            if self.controls.LEFT.click:
                self.emote_manager.emote_wheel.emote_index -= 1

            if self.controls.USE.click or self.controls.INTERACT.click:
                self.emote_manager.show_emote(
                    self, self.emote_manager.emote_wheel._current_emote
                )
                self.emote_manager.toggle_emote_wheel()

        # movement
        if (
            not self.tool_active
            and not self.blocked
            and not self.emote_manager.emote_wheel.visible
        ):
            self.direction.x = int(self.controls.RIGHT.hold) - int(
                self.controls.LEFT.hold
            )

            self.direction.y = int(self.controls.DOWN.hold) - int(self.controls.UP.hold)

            if self.direction:
                self.direction = self.direction.normalize()

            # tool switch
            if self.controls.NEXT_TOOL.click:
                tool_index = (
                    self.current_tool.value - FarmingTool.get_first_tool_id().value + 1
                ) % FarmingTool.get_tool_count()
                self.current_tool = FarmingTool(
                    tool_index + FarmingTool.get_first_tool_id()
                )

            # tool use
            if self.controls.USE.click:
                self.tool_active = True
                self.frame_index = 0
                self.direction = pygame.Vector2()
                if self.current_tool.is_swinging_tool():
                    self.sounds["swing"].play()

            # seed switch
            if self.controls.NEXT_SEED.click:
                seed_index = (
                    self.current_seed.value - FarmingTool.get_first_seed_id().value + 1
                ) % FarmingTool.get_seed_count()
                self.current_seed = FarmingTool(
                    seed_index + FarmingTool.get_first_seed_id()
                )

            # seed used
            if self.controls.PLANT.click:
                self.use_tool(ItemToUse.SEED)

            # interact
            if self.controls.INTERACT.click:
                self.interact()

            if self.controls.INVENTORY.click:
                post_event(OPEN_INVENTORY)

            if (
                self.controls.DEBUG_QUAKE.click
                and self.get_game_version() == DEBUG_MODE_VERSION
            ):
                post_event(START_QUAKE, duration=2.0, debug=True)

                # emotes
        if not self.blocked:
            if self.controls.EMOTE_WHEEL.click and self.round_config.get(
                "emote_wheel", False
            ):
                self.emote_manager.toggle_emote_wheel()
                if self.emote_manager.emote_wheel.visible:
                    self.direction = pygame.Vector2()

    def move(self, dt: float):
        self.hitbox_rect.update(
            (
                self.rect.x + self._current_hitbox.x,
                self.rect.y + self._current_hitbox.y,
            ),
            self._current_hitbox.size,
        )

        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.check_collision()

        self.rect.update(
            (
                self.hitbox_rect.x - self._current_hitbox.x,
                self.hitbox_rect.y - self._current_hitbox.y,
            ),
            self.rect.size,
        )

    # sets the player's transparency and speed according to their health

    def set_speed_asper_health(self):
        current_time = time.time()
        if current_time - self.created_time >= self.delay_time_speed:
            self.speed = self.original_speed * (self.hp / 100)

    def set_transparency_asper_health(self):
        alpha_value = int(255 * (self.hp / 100))
        self.image.set_alpha(alpha_value)

    def check_bath_bool(self):
        if (round(time.time() - self.bath_time)) == BATH_STATUS_TIMEOUT:
            self.bathstat = False

    def teleport(self, pos: tuple[float, float]):
        """
        Moves the Player rect directly to the specified point without checking
        for collision
        """
        self.rect.update(
            (pos[0] - self.rect.width / 2, pos[1] - self.rect.height / 2),
            self.rect.size,
        )

    def get_current_tool_string(self):
        return self.current_tool.as_serialised_string()

    def get_current_seed_string(self):
        return self.current_seed.as_serialised_string()

    def add_resource(
        self, resource: InventoryResource, amount: int = 1, sound: str = "success"
    ):
        super().add_resource(resource, amount)
        if sound:
            self.sounds[sound].play()

    def update(self, dt):
        self.set_speed_asper_health()
        self.set_transparency_asper_health()
        self.check_bath_bool()
        self.handle_controls()
        super().update(dt)
        self.emote_manager.update_obj(
            self, (self.rect.centerx - 47, self.rect.centery - 128)
        )
        self.emote_manager.update_emote_wheel(self.rect.center)

    def update_blocked(self, dt):
        """the scripted sequence needs to display emote box even when Player is blocked"""
        self.handle_controls()
        super().update_blocked(dt)
        self.emote_manager.update_obj(
            self, (self.rect.centerx - 47, self.rect.centery - 128)
        )
        self.emote_manager.update_emote_wheel(self.rect.center)
