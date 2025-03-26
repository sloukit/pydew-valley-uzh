from collections.abc import Callable

import pygame

from src.enums import GameState
from src.gui.menu.general_menu import GeneralMenu
from src.support import get_translated_string as _


class PauseMenu(GeneralMenu):
    def __init__(
        self,
        switch_screen: Callable[[GameState], None],
    ):
        options = [_("Resume"), _("Options")]
        title = _("Pause Menu")
        size = (400, 400)
        super().__init__(title, options, switch_screen, size)

    def button_action(self, text: str):
        if text == _("Resume"):
            self.switch_screen(GameState.PLAY)
        if text == _("Options"):
            self.switch_screen(GameState.SETTINGS)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PLAY)
                return True
            if event.key == pygame.K_q:
                self.quit_game()

        return False
