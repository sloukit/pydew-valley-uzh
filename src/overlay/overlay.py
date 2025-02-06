from collections.abc import Callable
from typing import Any

import pygame

from src.enums import ClockVersion
from src.gui.health_bar import HealthProgressBar
from src.overlay.clock import Clock
from src.overlay.fps import FPS
from src.overlay.game_time import GameTime
from src.overlay.money import Money
from src.overlay.box_keybindings import BoxKeybindingsLabel
from src.settings import OVERLAY_POSITIONS


class Overlay:
    def __init__(
        self,
        entity,
        item_frames,
        game_time: GameTime,
        get_world_time: Callable[[None], tuple[int, int]],
        clock: pygame.time.Clock,
        round_config: dict[str, Any],
    ) -> None:
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.player = entity

        # imports
        self.item_frames = item_frames

        self.visible = True

        # ui objects
        self.health_bar = HealthProgressBar(100)

        self.clock = Clock(game_time, get_world_time, ClockVersion.DIGITAL)
        self.FPS = FPS(clock)
        self.box_keybindings_label = BoxKeybindingsLabel(entity)
        self.money = Money(entity)

        self.round_config = round_config
        self.is_debug_mode_version: bool = False

    def display(self):
        if not self.visible:
            return

        # seeds
        seed_surf = self.item_frames[self.player.get_current_seed_string()]
        seed_rect = seed_surf.get_frect(midbottom=OVERLAY_POSITIONS["seed"])
        self.display_surface.blit(seed_surf, seed_rect)

        # Money amount display
        self.money.display()

        # Box keybindings label display
        self.box_keybindings_label.display()

        # tool
        tool_surf = self.item_frames[self.player.get_current_tool_string()]
        tool_rect = tool_surf.get_frect(midbottom=OVERLAY_POSITIONS["tool"])
        self.display_surface.blit(tool_surf, tool_rect)

        self.clock.display()
        if self.is_debug_mode_version:
            self.FPS.display()

        # health bar
        if self.round_config.get("healthbar", False):
            self.health_bar.draw(self.display_surface)
