from collections.abc import Callable
from typing import Type

import pygame
from pygame.math import Vector2 as vector

from src import settings
from src.controls import Controls
from src.enums import GameState
from src.gui.menu.description import KeybindsDescription, VolumeDescription
from src.gui.menu.general_menu import GeneralMenu
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH


class SettingsMenu(GeneralMenu):
    def __init__(
        self,
        switch_screen: Callable[[GameState], None],
        sounds: settings.SoundDict,
        controls: Type[Controls],
    ):
        options = ["Keybinds", "Volume", "Back"]
        title = "Settings"
        size = (400, 400)
        switch = switch_screen
        center = vector(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2) + vector(-350, 0)
        super().__init__(title, options, switch, size, center)

        # description
        description_pos = self.rect.topright + vector(100, 0)
        self.keybinds_description = KeybindsDescription(description_pos, controls)
        self.volume_description = VolumeDescription(description_pos, sounds)
        self.current_description = self.keybinds_description

        # buttons
        self.buttons.append(self.keybinds_description.reset_button)

    # setup
    def button_action(self, text: str):
        self.current_description.reset()

        if text == "Keybinds":
            self.current_description = self.keybinds_description
        if text == "Volume":
            self.current_description = self.volume_description
        if text == "Back":
            self.keybinds_description.save_data()
            self.volume_description.save_data()
            self.switch_screen(GameState.PAUSE)
        if text == "Reset":
            self.keybinds_description.reset_keybinds()
            self.volume_description.reset_volumes()

    # events
    def handle_event(self, event: pygame.event.Event) -> bool:
        return (
            super().handle_event(event)
            or self.current_description.handle_event(event)
            or self.echap(event)
        )

    def echap(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PAUSE)
                return True

        return False

    # draw
    def draw(self):
        super().draw()
        self.current_description.draw()

    # update
    def update(self, dt: float):
        self.keybinds_description.update_keybinds(dt)
        super().update(dt)
