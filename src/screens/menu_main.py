from collections.abc import Callable

import pygame

from src.enums import GameState
from src.gui.menu.general_menu import GeneralMenu


class MainMenu(GeneralMenu):
    def __init__(
        self,
        switch_screen: Callable[[GameState], None],
    ):
        options = ["Play", "Quit", "Enter a Token to Play"]
        title = "Main Menu"
        size = (400, 400)
        super().__init__(title, options, switch_screen, size)
        self.input_active = False
        self.token_input = ""
        # TODO revert, this only for debug
        self.play_button_enabled = True  # Initialize as False

    def button_action(self, text):
        if text == "Play" and self.play_button_enabled:
            # Only allow playing if the token is valid
            self.switch_screen(GameState.PLAY)
        elif text == "Enter a Token to Play":
            self.input_active = True
            self.token_input = ""
        elif text == "Quit":
            self.quit_game()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_game()
                return True

            if self.input_active and event.key == pygame.K_RETURN:
                if self.validate_token(self.token_input):
                    self.play_button_enabled = True
                    self.input_active = False
                return True

            # Play button is available => start game
            if self.play_button_enabled and event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.switch_screen(GameState.PLAY)

            # Play button is not available => ask for token
            if not self.play_button_enabled and event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.input_active = True
                return True

        return False
