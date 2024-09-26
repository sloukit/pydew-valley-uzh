from typing import Callable

import pygame
import pygame.freetype

from src.gui.menu.abstract_menu import AbstractMenu
from src.enums import GameState
from src.gui.menu.components import Slider, EntryField
from src.screens.minigames.gui import (
    Linebreak,
    Text,
    TextChunk,
    _draw_box,
    _ReturnButton,
)
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH, SoundDict
from src.support import get_outline, import_freetype_font
from src.colors import SL_ORANGE_BRIGHTEST


class TaskMenu(AbstractMenu):
    def __init__(self, switch_screen: Callable[[], None]):
        super().__init__(title="Task", size=(SCREEN_WIDTH, SCREEN_HEIGHT))
        self.display_surface = pygame.display.get_surface()
        self.font_title = import_freetype_font(38, "font/LycheeSoda.ttf")
        self.font_text = import_freetype_font(32, "font/LycheeSoda.ttf")
        self.confirm_button_text = "Confirm"
        self.switch_screen = switch_screen
        self.sounds = SoundDict
        self.buttons = []
        self.button_setup()
        self.entry_boxes: list[EntryField] = []
        self.active_entry = None

    def draw_title(self):
        text = Text(
            Linebreak((0, 12)), TextChunk("Task", self.font_title), Linebreak((0, 12))
        )
        _draw_box(self.display_surface, (SCREEN_WIDTH / 2, 0), text.surface_rect.size)
        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self.display_surface.blit(
            text_surface,
            (SCREEN_WIDTH / 2 - text.surface_rect.width / 2, 0),
        )

    def draw_entry_fields(self, surface):
        # magic numbers should go -> add offset from topleft of taskbox?
        entry1 = EntryField(surface, (755, 223))
        entry2 = EntryField(surface, (755, 257))
        entry3 = EntryField(surface, (755, 291))
        self.entry_boxes.extend((entry1, entry2, entry3))
        for entry_box in self.entry_boxes:
            entry_box.draw()

    def draw_task(self):
        box_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3)
        button_top_margin = 32
        button_area_height = self.confirm_button.rect.height + button_top_margin

        text = Text(
            TextChunk("You have received 12 candy bars!", self.font_text),
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
        box_size = (
            text.surface_rect.width,
            text.surface_rect.height + button_area_height,
        )

        _draw_box(self.display_surface, box_center, box_size)

        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self.display_surface.blit(
            text_surface,
            (
                box_center[0] - text.surface_rect.width / 2,
                box_center[1] - text.surface_rect.height / 2,
            ),
        )
        self.draw_entry_fields(self.display_surface)
        self.confirm_button.move(
            (
                box_center[0] - self.confirm_button.rect.width / 2,
                box_center[1] - self.confirm_button.rect.height + box_size[1] / 2,
            )
        )

    def button_action(self, name: str):
        if name == self.confirm_button.text:
            self.switch_screen(GameState.PLAY)

    def button_setup(self):
        self.confirm_button = _ReturnButton(self.confirm_button_text)
        self.buttons.append(self.confirm_button)

    def get_hovered_entry(self):
        for entry_box in self.entry_boxes:
            if entry_box.mouse_hover():
                return entry_box
        return None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
            self.active_entry = self.get_hovered_entry()
            if self.active_entry:
                self.active_entry.active = True
                return self.active_entry.handle_event(event)
            return super().handle_event(event)
            print(self.active_entry.active)
            # return (super().click(event) or self.handle_event(event))
            #     self.active_entry.handle_event(event)
            #     return True

        return False

    def mouse_hover(self):
        for element in [*self.buttons, *self.entry_boxes]:
            if element.hover_active:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                return
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def draw(self):
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 64))
        self.display_surface.blit(self._surface, (0, 0))
        self.draw_title()
        self.draw_task()
        self.confirm_button.draw(self.display_surface)

    def update(self, dt):
        super().update(dt)

        # for entry_box in self.entry_boxes:
        #     entry_box.update()
