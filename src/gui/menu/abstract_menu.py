from abc import ABC, abstractmethod

import pygame
from pygame.math import Vector2 as vector
from pygame.mouse import get_pressed as mouse_buttons

from src.enums import CustomCursor
from src.events import SET_CURSOR, post_event
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.support import resource_path

_SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


class AbstractMenu(ABC):
    """Abstract base class for all menus in the game.

    Most of the time, you will override GeneralMenu instead
    (which is a subclass of this) when making new menus and screens here."""

    def __init__(self, title, size, center=vector()):
        self.title = title
        self.size = size
        self.center = center
        self.buttons_surface = pygame.Surface(size, flags=pygame.SRCALPHA)
        self.font = pygame.font.Font(resource_path("font/LycheeSoda.ttf"), 30)
        self.display_surface = pygame.display.get_surface()

        self.buttons = []
        self.pressed_button = None

        # rect
        self.rect = pygame.Rect()
        self.rect_setup()

    @abstractmethod
    def button_action(self, *args, **kwargs):
        """What should be done when a button is pressed goes here."""
        pass

    def get_hovered_button(self):
        for button in self.buttons:
            if button.mouse_hover():
                return button
        return None

    def mouse_hover(self):
        for button in self.buttons:
            if button.hover_active:
                post_event(SET_CURSOR, cursor=CustomCursor.POINT)
                return
        post_event(SET_CURSOR, cursor=CustomCursor.ARROW)

    @abstractmethod
    def button_setup(self, *args, **kwargs):
        pass

    # events
    def handle_event(self, event: pygame.event.Event):
        return self.click(event)

    # setup
    def rect_setup(self):
        self.rect = pygame.Rect((0, 0), self.size)
        self.rect.center = self.center or _SCREEN_CENTER

    def click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            self.pressed_button = self.get_hovered_button()
            if self.pressed_button:
                self.pressed_button.start_press_animation()
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.pressed_button:
                self.pressed_button.start_release_animation()

                if self.pressed_button.mouse_hover():
                    self.button_action(self.pressed_button.text)
                    post_event(SET_CURSOR, cursor=CustomCursor.ARROW)

                self.pressed_button = None
                return True

        return False

    def quit_game(self):
        post_event(pygame.QUIT)

    def update_buttons(self, dt):
        for button in self.buttons:
            button.update(dt)

    # draw
    def draw_title(self):
        text_surf = self.font.render(self.title, False, "Black")
        midtop = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20)
        text_rect = text_surf.get_frect(midtop=midtop)

        bg_rect = pygame.Rect((0, 0), (200, 50))
        bg_rect.center = text_rect.center

        pygame.draw.rect(self.display_surface, "White", bg_rect, 0, 4)
        self.display_surface.blit(text_surf, text_rect)

    def draw_buttons(self):
        self.buttons_surface.fill(pygame.Color(0, 0, 0, 0))
        for button in self.buttons:
            if button.text == "Play" and not self.play_button_enabled:
                button.draw_disabled(self.display_surface)
            else:
                button.draw(self.display_surface)
        self.display_surface.blit(self.buttons_surface, self.rect.topleft)

    def draw(self):
        self.draw_title()
        self.draw_buttons()

    def update(self, dt):
        self.mouse_hover()
        self.update_buttons(dt)
        self.draw()
