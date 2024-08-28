from typing import Callable

import pygame
import pygame.freetype

from src.gui.menu.abstract_menu import AbstractMenu
from src.gui.menu.components import EntryField
from src.screens.minigames.gui import (
    Linebreak,
    Text,
    TextChunk,
    _draw_box,
    _ReturnButton,
)
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.support import get_outline, import_freetype_font

"""
- add image to task textbox
- add entryfields to task textbox
- add confirm button
"""


class PlayerTask(AbstractMenu):
    def __init__(self, return_func: Callable[[], None]):
        super().__init__(title="Task", size=(SCREEN_WIDTH, SCREEN_HEIGHT))
        self.display_surface = pygame.display.get_surface()
        self.font_title = import_freetype_font(32, "font/LycheeSoda.ttf")
        self.font_text = import_freetype_font(24, "font/LycheeSoda.ttf")
        self.confirm_button_text = "Confirm"
        self.return_func = return_func
        self.buttons = []
        self.button_setup()

    def draw_title(self):
        text = Text(Linebreak(), TextChunk("Task", self.font_title))
        _draw_box(self.display_surface, (SCREEN_WIDTH / 2, 0), text.surface_rect.size)
        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self.display_surface.blit(
            text_surface,
            (0, 0),
        )

    def draw_task(self):
        box_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)

        text = Text(
            TextChunk("You have received 12 blue eggs!", self.font_text),
            Linebreak(),
            TextChunk("Distribute them:", self.font_text),
            Linebreak((0, 18)),
            Linebreak(),
            TextChunk("Your own inventory:", self.font_text),
            Linebreak(),
            TextChunk("Your group's inventory:", self.font_text),
            Linebreak(),
            TextChunk("Other group's inventory:", self.font_text),
        )

        _draw_box(self.display_surface, box_center, text.surface_rect.size)

        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self.display_surface.blit(
            text_surface,
            (
                box_center[0] - text.surface_rect.width / 2,
                box_center[1] - text.surface_rect.height / 2,
            ),
        )

    def button_action(self, name: str):
        if name == self.confirm_button.text:
            self.return_func()

    def button_setup(self):
        self.confirm_button = _ReturnButton(self.confirm_button_text)
        self.buttons.append(self.confirm_button)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
            self.pressed_button = self.get_hovered_button()
            if self.pressed_button:
                self.pressed_button.start_press_animation()
                return True

        if event.type == pygame.MOUSEBUTTONUP:
            if self.pressed_button:
                self.pressed_button.start_release_animation()

                if self.pressed_button.mouse_hover():
                    self.button_action(self.pressed_button.text)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

                self.pressed_button = None
                return True

        return False

    def draw(self):
        pygame.draw.rect(
            self.display_surface, pygame.Color("Black"), pygame.Rect(100, 100, 100, 100)
        )
        self.draw_title()
        self.draw_task()
        print("something")

    def update(self, dt):
        self.mouse_hover()
        self.update_buttons(dt)
