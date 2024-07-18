
import pygame
from src.gui.general_menu import GeneralMenu
from src.enums import GameState


class PauseMenu(GeneralMenu):
    def __init__(self, switch_screen):
        options = ['Resume', 'Options', "Save and Resume", 'Quit']
        title = 'Pause Menu'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size)

    def button_action(self, text):
        if text == 'Resume':
            self.switch_screen(GameState.LEVEL)
        if text == 'Options':
            self.switch_screen(GameState.SETTINGS)
        if text == "Save and Resume":
            self.switch_screen(GameState.LEVEL)
        if text == 'Quit':
            self.quit_game()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.LEVEL)
