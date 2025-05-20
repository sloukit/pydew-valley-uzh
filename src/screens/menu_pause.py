from collections.abc import Callable

import pygame

from src.enums import GameState
from src.gui.menu.general_menu import GeneralMenu
from src.support import get_translated_string


class PauseMenu(GeneralMenu):
    def __init__(
        self,
        switch_screen: Callable[[GameState], None],
    ):
        options = [get_translated_string("Resume"), get_translated_string("Options")]
        title = get_translated_string("Pause Menu")
        size = (400, 400)
        super().__init__(title, options, switch_screen, size)

    def button_action(self, text: str):
        if text == get_translated_string("Resume"):
            self.switch_screen(GameState.PLAY)
        if text == get_translated_string("Options"):
            self.switch_screen(GameState.SETTINGS)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PLAY)
                return True

        return False
