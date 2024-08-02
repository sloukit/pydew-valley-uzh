from collections.abc import Callable

import pygame

from src.enums import GameState
from src.gui.menu.general_menu import GeneralMenu


class MainMenu(GeneralMenu):
    def __init__(self, switch_screen: Callable[[GameState], None]):
        options = ["Play", "Quit"]
        title = "Main Menu"
        size = (400, 400)
        super().__init__(title, options, switch_screen, size)

    def button_action(self, text):
        if text == "Play":
            self.switch_screen(GameState.PLAY)
        if text == "Quit":
            self.quit_game()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_game()
                return True

            if event.key == pygame.K_RETURN:
                self.switch_screen(GameState.PLAY)
                return True

        return False
