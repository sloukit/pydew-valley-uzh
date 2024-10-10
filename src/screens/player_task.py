from typing import Callable

import pygame
import pygame.freetype

from src.enums import GameState
from src.gui.menu.abstract_menu import AbstractMenu
from src.gui.menu.components import ArrowButton, InputField
from src.screens.minigames.gui import (
    Linebreak,
    Text,
    TextChunk,
    _draw_box,
    _ReturnButton,
)
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.support import import_font, import_freetype_font

"""
TODO:
- add image of allocated item somewhere
- properly draw active InputField
- save allocations to save_file
- integrate into level system
BUGS:
- confirm button doesn't work anymore after merging with origin
- during one test, health droped when using normal number keys, didn't happen when the num-block
"""


class PlayerTask(AbstractMenu):
    """Run the item allocation task."""

    def __init__(self, switch_screen: Callable[[], None], clock: pygame.time.Clock):
        super().__init__(title="Task", size=(SCREEN_WIDTH, SCREEN_HEIGHT))
        self.display_surface: pygame.Surface = pygame.display.get_surface()
        self.title_font: pygame.freetype.Font = import_freetype_font(
            38, "font/LycheeSoda.ttf"
        )
        self.text_font: pygame.freetype.Font = import_freetype_font(
            32, "font/LycheeSoda.ttf"
        )
        self.input_field_font: pygame.font.Font = import_font(38, "font/LycheeSoda.ttf")
        self.confirm_button_text: str = "Confirm"
        self.switch_screen = switch_screen
        self.buttons = []
        self.button_setup()

        self.arrow_buttons: list[list[ArrowButton]] = []
        self.input_fields: list[InputField] = []
        self.allocations: list[int] = [0, 0, 0]
        self.max_allocation: int = 15
        self.min_allocation: int = 0
        self.total_items: int = 15
        self.active_input: int | None = None

    def draw_title(self) -> None:
        text = Text(
            Linebreak((0, 12)), TextChunk("Task", self.title_font), Linebreak((0, 12))
        )
        _draw_box(self.display_surface, (SCREEN_WIDTH / 2, 0), text.surface_rect.size)
        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self.display_surface.blit(
            text_surface,
            (SCREEN_WIDTH / 2 - text.surface_rect.width / 2, 0),
        )

    def draw_allocation_buttons(self) -> None:
        self.input_fields = [
            InputField(self.display_surface, (745, 200), self.input_field_font),
            InputField(self.display_surface, (745, 250), self.input_field_font),
            InputField(self.display_surface, (745, 300), self.input_field_font),
        ]
        self.arrow_buttons = [
            [
                ArrowButton("up", pygame.Rect(800, 200, 30, 20), self.input_field_font),
                ArrowButton(
                    "down", pygame.Rect(800, 220, 30, 20), self.input_field_font
                ),
            ],
            [
                ArrowButton("up", pygame.Rect(800, 250, 30, 20), self.input_field_font),
                ArrowButton(
                    "down", pygame.Rect(800, 270, 30, 20), self.input_field_font
                ),
            ],
            [
                ArrowButton("up", pygame.Rect(800, 300, 30, 20), self.input_field_font),
                ArrowButton(
                    "down", pygame.Rect(800, 320, 30, 20), self.input_field_font
                ),
            ],
        ]

        for i, input_box in enumerate(self.input_fields):
            input_box.input_text = str(self.allocations[i])
            input_box.draw()
            for button in self.arrow_buttons[i]:
                button.draw(self.display_surface)

    def draw_info(self) -> None:
        text = Text(
            Linebreak((0, 18)),
            TextChunk("You have not allocated all of the items yet!", self.text_font),
            Linebreak(),
            TextChunk(
                f"Items missing: {self.total_items - sum(self.allocations)}",
                self.text_font,
            ),
        )
        _draw_box(
            self.display_surface,
            (SCREEN_WIDTH / 2, (SCREEN_HEIGHT / 2) * 1.5),
            text.surface_rect.size,
        )
        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self.display_surface.blit(
            text_surface,
            (
                SCREEN_WIDTH / 2 - text.surface_rect.width / 2,
                (SCREEN_HEIGHT / 2) * 1.5 - text.surface_rect.height / 2,
            ),
        )

    def draw_task_surf(self) -> None:
        box_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3)
        button_top_margin = 32
        button_area_height = self.confirm_button.rect.height + button_top_margin

        text = Text(
            TextChunk(
                f"You have received {self.max_allocation} candy bars!", self.text_font
            ),
            Linebreak(),
            TextChunk("Distribute them:", self.text_font),
            Linebreak((0, 18)),
            TextChunk("Your own inventory:", self.text_font),
            Linebreak((0, 18)),
            TextChunk("Your group's inventory:", self.text_font),
            Linebreak((0, 18)),
            TextChunk("Other group's inventory:", self.text_font),
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
        self.confirm_button.move(
            (
                box_center[0] - self.confirm_button.rect.width / 2,
                box_center[1] - self.confirm_button.rect.height + box_size[1] / 2,
            )
        )

    def button_action(self, name: str) -> None:
        if (
            name == self.confirm_button.text
            and sum(self.allocations) == self.total_items
        ):
            self.switch_screen(GameState.PLAY)

    def button_setup(self) -> None:
        self.confirm_button = _ReturnButton(self.confirm_button_text)
        self.buttons.append(self.confirm_button)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, entry_field in enumerate(self.input_fields):
                if entry_field.mouse_hover():
                    self.active_input = i
                    for field in self.input_fields:
                        field.active = False
                    entry_field.active = True

            for i, (up, down) in enumerate(self.arrow_buttons):
                if up.mouse_hover():
                    if sum(self.allocations) < self.total_items:
                        self.allocations[i] = min(
                            self.allocations[i] + 1, self.max_allocation
                        )
                elif down.mouse_hover():
                    self.allocations[i] = max(
                        self.allocations[i] - 1, self.min_allocation
                    )

        if event.type == pygame.KEYDOWN and self.active_input is not None:
            if event.key == pygame.K_BACKSPACE:
                self.allocations[self.active_input] = (
                    self.allocations[self.active_input] // 10
                )
            elif event.unicode.isdigit():
                new_value = int(
                    str(self.allocations[self.active_input]) + event.unicode
                )
                self.allocations[self.active_input] = min(
                    new_value, self.max_allocation
                )
            if sum(self.allocations) > self.total_items:
                self.allocations[self.active_input] -= (
                    sum(self.allocations) - self.total_items
                )
            return True

        return False

    def mouse_hover(self) -> None:
        for element in [*self.buttons, *self.input_fields]:
            if element.hover_active:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                return
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def draw(self) -> None:
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 64))
        self.display_surface.blit(self._surface, (0, 0))
        self.draw_title()
        self.draw_task_surf()
        self.draw_allocation_buttons()
        self.confirm_button.draw(self.display_surface)
        if sum(self.allocations) < self.total_items:
            self.draw_info()

    def update(self, dt: float):
        super().update(dt)
