from typing import Any, Callable

import pygame

from src.enums import CustomCursor, GameState  # InventoryResource
from src.events import SET_CURSOR, post_event
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
from src.support import import_font

"""
TODO:
- properly draw active InputField
- save allocations to save_file
- determine_allocation_item() needs error handling if level > len(self.allocation_item_names)
"""


class PlayerTask(AbstractMenu):
    """Run the item allocation task."""

    def __init__(self, send_resource_allocation: Callable[[dict[str, Any]], None]):
        super().__init__(title="Task", size=(SCREEN_WIDTH, SCREEN_HEIGHT))
        self.display_surface: pygame.Surface = pygame.display.get_surface()
        self.title_font: pygame.Font = import_font(38, "font/LycheeSoda.ttf")
        self.text_font: pygame.Font = import_font(32, "font/LycheeSoda.ttf")
        self.input_field_font: pygame.font.Font = import_font(38, "font/LycheeSoda.ttf")
        self.confirm_button_text: str = "Confirm"
        self.allocations_text: str = "Distribute them"
        self.send_resource_allocation = send_resource_allocation
        self.buttons = []
        self.button_setup()
        # self.round = current_round

        # self.allocation_items: list[tuple[str, int]] = [
        #     ("candy bar", 20),
        #     ("blanket", 10),
        #     ("glove", 14),
        #     ("boot", 8),
        #     ("jean", 22),
        #     ("shirt", 18),
        #     ("rain cape", 6),
        #     ("apron", 16),
        #     ("water bottle", 24),
        #     ("flashlight", 12),
        #     ("umbrella", 4),
        #     ("mask", 26),
        # ]
        # self.allocation_item: tuple[str, int] | None = None
        self.allocation_item: str | None = None
        self.arrow_buttons: list[list[ArrowButton]] = []
        self.input_fields: list[InputField] = []
        self.allocations: list[int] = [0, 0]
        self.max_allocation: int | None = None
        self.min_allocation: int = 0
        self.total_items: int | None = None
        self.active_input: int | None = None

    def parse_allocation_items(self, allocation_items: str) -> None:
        elements = allocation_items.split(" ")
        if len(elements) > 1:
            if elements[0].isnumeric():
                self.max_allocation = int(elements[0])
            else:
                self.max_allocation = 2

            self.allocation_item = " ".join(elements[1:])
        else:
            print(f"Error! Could not parse allocation items: '{allocation_items}'")
            self.max_allocation = 2
            self.allocation_item = "<GENERIC_ITEM_NAME>"
        self.total_items = self.max_allocation
        self.allocations = [0, 0]

    def draw_title(self) -> None:
        text = Text(Linebreak((0, 2)), TextChunk("Task", self.title_font))
        _draw_box(
            self.display_surface,
            (SCREEN_WIDTH / 2, 0),
            (text.surface_rect.width, text.surface_rect.height + 24),
        )
        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self.display_surface.blit(
            text_surface,
            (SCREEN_WIDTH / 2 - text.surface_rect.width / 2, 0),
        )

    def draw_allocation_buttons(self) -> None:
        self.input_fields = [
            InputField(self.display_surface, (755, 210), self.input_field_font),
            InputField(self.display_surface, (755, 265), self.input_field_font),
        ]
        self.arrow_buttons = [
            [
                ArrowButton("up", pygame.Rect(805, 210, 30, 20), self.input_field_font),
                ArrowButton(
                    "down", pygame.Rect(805, 230, 30, 20), self.input_field_font
                ),
            ],
            [
                ArrowButton("up", pygame.Rect(805, 265, 30, 20), self.input_field_font),
                ArrowButton(
                    "down", pygame.Rect(805, 285, 30, 20), self.input_field_font
                ),
            ],
        ]

        for i, input_box in enumerate(self.input_fields):
            input_box.input_text = str(self.allocations[i])
            input_box.draw()
            for button in self.arrow_buttons[i]:
                button.draw(self.display_surface)

    def draw_info(self) -> None:
        not_enough_items: str = "You have not allocated all of the items yet!"
        too_many_items: str = "You don't have that many items to distribute."
        missing_items: str = (
            f"Items missing: {self.total_items - sum(self.allocations)}"
        )
        overstock_items: str = f"Take out: {sum(self.allocations) - self.total_items}"

        if sum(self.allocations) < self.total_items:
            text_parts = not_enough_items, missing_items
        elif sum(self.allocations) > self.total_items:
            text_parts = too_many_items, overstock_items
        padding_y = 8
        text = Text(
            Linebreak((0, padding_y)),
            TextChunk(text_parts[0], self.text_font),
            Linebreak(),
            TextChunk(
                text_parts[1],
                self.text_font,
            ),
            Linebreak((0, padding_y)),
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
        if not self.allocation_item:
            self.parse_allocation_items("")
        box_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3)
        button_area_height = self.confirm_button.rect.height

        text = Text(
            Linebreak((0, 12)),
            TextChunk(
                f"You have received {self.max_allocation} {self.allocation_item}!",
                self.text_font,
            ),
            Linebreak(),
            TextChunk(self.allocations_text, self.text_font),
            Linebreak((0, 18)),
            TextChunk("Your group's inventory:", self.text_font),
            Linebreak((0, 18)),
            TextChunk("Other group's inventory:", self.text_font),
            Linebreak((0, 12)),
        )
        box_min_width = 400
        box_width = (
            box_min_width
            if box_min_width > text.surface_rect.width
            else text.surface_rect.width
        )
        box_size = (
            box_width,
            text.surface_rect.height + button_area_height,
        )

        _draw_box(self.display_surface, box_center, box_size)

        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        current_y = box_center[1] - box_size[1] / 2

        self.display_surface.blit(
            text_surface,
            (
                box_center[0] - box_width / 2,
                current_y,
            ),
        )
        current_y += text_surface.get_height()
        self.confirm_button.move(
            (
                box_center[0] - self.confirm_button.rect.width / 2,
                current_y,
            )
        )

    def button_action(self, name: str) -> None:
        if (
            name == self.confirm_button.text
            and sum(self.allocations) == self.total_items
        ):
            resource_allocation = {
                "allocation_item": self.allocation_item,
                "max_allocation": self.max_allocation,
                "allocations": self.allocations
            }
            self.send_resource_allocation(resource_allocation)

    def button_setup(self) -> None:
        self.confirm_button = _ReturnButton(self.confirm_button_text)
        self.buttons.append(self.confirm_button)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

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
                    # self.allocations[i] = max(
                    #     self.allocations[i] - 1, self.min_allocation
                    # )
                    self.allocations[i] = self.allocations[i] - 1
                    if self.allocations[i] < 0:
                        self.allocations[i] = self.total_items - sum(self.allocations) - 1

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
            else:
                return False
            if sum(self.allocations) > self.total_items:
                self.allocations[self.active_input] -= (
                    sum(self.allocations) - self.total_items
                )
            return True

        return False

    def mouse_hover(self) -> None:
        for element in [*self.buttons, *self.input_fields]:
            if element.hover_active:
                post_event(SET_CURSOR, cursor=CustomCursor.POINT)
                return
        post_event(SET_CURSOR, cursor=CustomCursor.ARROW)

    def draw(self) -> None:
        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 64))
        self.display_surface.blit(self._surface, (0, 0))
        self.draw_title()
        self.draw_task_surf()
        self.draw_allocation_buttons()
        self.confirm_button.draw(self.display_surface)
        if (
            sum(self.allocations) < self.total_items
            or sum(self.allocations) > self.total_items
        ):
            self.draw_info()
