import math
from typing import Callable

import pygame
import pygame.freetype

from src.colors import SL_ORANGE_BRIGHT, SL_ORANGE_BRIGHTEST
from src.gui.menu.abstract_menu import AbstractMenu
from src.screens.minigames.gui import (
    Linebreak,
    Text,
    TextChunk,
    _draw_box,
    _ReturnButton,
)
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.support import get_outline, import_font, import_freetype_font


class _CowHerdingScoreboard(AbstractMenu):
    def __init__(self, return_func: Callable[[], None]):
        super().__init__(title="Cow Herding", size=(SCREEN_WIDTH, SCREEN_HEIGHT))

        self._return_func = return_func
        self.return_button: _ReturnButton | None = None

        self._surface = pygame.Surface((0, 0))

        self.font_title = import_freetype_font(48, "font/LycheeSoda.ttf")
        self.font_number = import_freetype_font(36, "font/LycheeSoda.ttf")
        self.font_description = import_freetype_font(24, "font/LycheeSoda.ttf")
        self.font_button = import_freetype_font(32, "font/LycheeSoda.ttf")

    def setup(self, time_needed, cows_herded_in):
        box_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        padding = (16, 24)

        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 64))

        self.button_setup()
        button_top_margin = 32
        button_area_height = self.return_button.rect.height + button_top_margin

        text = Text(
            TextChunk("Success!", self.font_title),
            Linebreak(),
            TextChunk(f"{time_needed:.2f}", self.font_number),
            TextChunk(" seconds needed", self.font_description),
            Linebreak(),
            TextChunk(f"{cows_herded_in}", self.font_number),
            TextChunk(" cows herded in", self.font_description),
        )

        box_size = (
            text.surface_rect.width + padding[0] * 2,
            text.surface_rect.height + padding[1] * 2 + button_area_height,
        )

        _draw_box(self._surface, box_center, box_size)

        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self._surface.blit(
            text_surface,
            (
                box_center[0] - text.surface_rect.width / 2,
                box_center[1] - text.surface_rect.height / 2 - button_area_height / 2,
            ),
        )

        self.return_button.move(
            (
                box_center[0] - self.return_button.rect.width / 2,
                box_center[1]
                - self.return_button.rect.height
                + box_size[1] / 2
                - padding[1],
            )
        )

    def button_action(self, name: str):
        if name == "Return to Town":
            self._return_func()

    def button_setup(self):
        self.return_button = _ReturnButton("Return to Town")
        self.buttons.append(self.return_button)

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

    def draw_title(self):
        self.display_surface.blit(self._surface, (0, 0))

    def update(self, dt):
        self.mouse_hover()

        self.update_buttons(dt)


class _CowHerdingOverlay:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()

        self.font_countdown = import_font(128, "font/LycheeSoda.ttf")
        self.font_timer = import_font(48, "font/LycheeSoda.ttf")

        self.font_description = import_freetype_font(32, "font/LycheeSoda.ttf")
        self.font_objective = import_freetype_font(24, "font/LycheeSoda.ttf")

        self.timer_chars = {
            char: self.font_timer.render(char, True, SL_ORANGE_BRIGHTEST)
            for char in "0123456789.:"
        }
        # ensures that the timer numbers maintain their position by using equal spacing
        self.timer_char_width = max(char.width for char in self.timer_chars.values())
        self.timer_char_height = max(char.height for char in self.timer_chars.values())

    def _render_countdown_text(self, text: str):
        rendered_text = self.font_countdown.render(text, False, SL_ORANGE_BRIGHTEST)
        rendered_text = get_outline(rendered_text, SL_ORANGE_BRIGHT, resize=True)
        return rendered_text

    def draw_countdown(self, current_time: float):
        """
        Displays ceil(abs(current_time)) if current_time < 0, else "GO!"
        """
        current_time_int = math.floor(current_time)
        current_fraction = current_time - current_time_int

        if current_time_int < 0:
            rendered_text = self._render_countdown_text(f"{abs(current_time_int)}")

            if current_fraction <= 0.25:
                rendered_text = pygame.transform.scale_by(
                    rendered_text, current_fraction * 4.5
                )
                alpha = current_fraction * 4 * 1.5 - 0.5
                rendered_text.set_alpha(max(0, int(alpha * 255)))
        else:
            rendered_text = self._render_countdown_text("GO!")

            if current_fraction <= 1 / 6:
                rendered_text = pygame.transform.scale_by(
                    rendered_text,
                    math.sin(current_fraction * 2 * math.pi * 4.5 + 0.5 * math.pi) / 8
                    + 1,
                )

        self.display_surface.blit(
            rendered_text,
            (
                SCREEN_WIDTH / 2 - rendered_text.width / 2,
                SCREEN_HEIGHT / 3 - rendered_text.height / 2,
            ),
        )

    def draw_description(self):
        box_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)

        text = Text(
            Linebreak((0, 18)),
            TextChunk("Cow Herding Minigame", self.font_description),
            Linebreak(),
            Linebreak((0, 24)),
            TextChunk("Herd the cows into the barn", self.font_description),
            Linebreak(),
            TextChunk("as fast as possible!", self.font_description),
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

    def draw_objective(self, cows_total: int, cows_herded_in: int):
        box_top_right = (SCREEN_WIDTH, 0)
        padding = 12

        text = Text(
            TextChunk("Objective:", self.font_description),
            Linebreak(),
            TextChunk("Herd the cows into the barn!", self.font_objective),
            Linebreak(),
            Linebreak((0, 32)),
            TextChunk("Progress:", self.font_objective),
            Linebreak(),
            TextChunk(
                f"({cows_herded_in}/{cows_total}) Cows in the barn",
                self.font_objective,
            ),
        )

        _draw_box(
            self.display_surface,
            (
                box_top_right[0] - text.surface_rect.width / 2,
                box_top_right[1] + text.surface_rect.height / 2 - padding,
            ),
            (
                text.surface_rect.width + padding * 2,
                text.surface_rect.height + padding * 2,
            ),
        )

        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self.display_surface.blit(
            text_surface,
            (
                box_top_right[0] - text.surface_rect.width - padding,
                box_top_right[1] + padding,
            ),
        )

    def draw_timer(self, current_time: float):
        t = max(0.0, current_time)
        timer_string = (
            f"{int(t / 60):02}"
            + ":"
            + f"{(int(t) - int(t / 60) * 60):02}"
            + "."
            + f"{t - int(t):.2f}"[2:]
        )

        total_length = 0

        for i in range(len(timer_string)):
            if timer_string[i].isdigit():
                total_length += self.timer_char_width
            else:
                total_length += self.timer_chars[timer_string[i]].width

        _draw_box(
            self.display_surface,
            (SCREEN_WIDTH / 2, 0),
            (total_length, self.timer_char_height + 32),
        )

        current_length = 0

        offset_y = 3

        for i in range(len(timer_string)):
            self.display_surface.blit(
                self.timer_chars[timer_string[i]],
                (SCREEN_WIDTH / 2 - total_length / 2 + current_length, offset_y),
            )
            if timer_string[i].isdigit():
                current_length += self.timer_char_width
            else:
                current_length += self.timer_chars[timer_string[i]].width
