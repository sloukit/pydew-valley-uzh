
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.support import resource_path
from src.gui.general_menu import GeneralMenu
from src.gui.description import KeybindsDescription, VolumeDescription
from src.enums import GameState
from pygame.math import Vector2 as vector




class SettingsMenu(GeneralMenu):
    def __init__(self, switch_screen, sounds, level):
        options = ['Keybinds', 'Volume', 'Back']
        title = 'Settings'
        size = (400, 400)
        switch = switch_screen
        center = vector(SCREEN_WIDTH/2, SCREEN_HEIGHT/2) + vector(-350, 0)
        super().__init__(title, options, switch, size, center)

        # description
        description_pos = self.rect.topright + vector(100, 0)
        self.keybinds_description = KeybindsDescription(description_pos)
        self.volume_description = VolumeDescription(description_pos, sounds)
        self.current_description = self.keybinds_description

        # buttons
        self.buttons.append(self.keybinds_description.reset_button)

        self.level = level

    # setup
    def button_action(self, text):
        if text == 'Keybinds':
            self.current_description = self.keybinds_description
        if text == 'Volume':
            self.current_description = self.volume_description
        if text == 'Back':
            self.keybinds_description.save_data()
            self.volume_description.save_data()
            self.level.player.update_keybinds()
            self.switch_screen(GameState.PAUSE)
        if text == 'Reset':
            self.keybinds_description.reset_keybinds()

    # events
    def handle_events(self, event):
        self.current_description.handle_events(event)
        self.echap(event)

    def echap(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PAUSE)

    # draw
    def draw(self):
        super().draw()
        self.current_description.draw()

    # update
    def update(self, dt):
        self.keybinds_description.update_keybinds(dt)
        super().update(dt)

