from collections.abc import Callable

import pygame
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons

from src.enums import GameState
from src.gui.menu.abstract_menu import AbstractMenu
from src.gui.menu.components import Button


class GeneralMenu(AbstractMenu):
    def __init__(
        self,
        title: str,
        options: list[str],
        switch: Callable[[GameState], None],
        size: tuple[int, int],
        center: vector = None,
    ):
        if center is None:
            center = vector()

        super().__init__(title, size, center)

        self.options = options
        self.button_setup()

        # switch
        self.switch_screen = switch

    def draw(self) -> None:
        self.draw_title()
        self.draw_buttons()

    def button_setup(self) -> None:
        # button setup
        button_width = 400
        button_height = 50
        size = (button_width, button_height)
        space = 10
        top_margin = 20

        # generic button rect
        generic_button_rect = pygame.Rect((0, 0), size)
        generic_button_rect.top = self.rect.top + top_margin
        generic_button_rect.centerx = self.rect.centerx

        # create buttons
        for title in self.options:
            rect = generic_button_rect
            button = Button(title, rect, self.font)
            self.buttons.append(button)
            generic_button_rect = rect.move(0, button_height + space)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            self.pressed_button = self.get_hovered_button()

        return False

    def button_action(self, text: str) -> None:
        if text == "Quit":
            self.quit_game()

    def remove_button(self, button_text: str) -> None:
        self.buttons = [button for button in self.buttons if button.text != button_text]

    def draw_description(self):
        pass
