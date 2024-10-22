from abc import ABC, abstractmethod

import pygame

from src.colors import (
    SL_ORANGE_BRIGHT,
    SL_ORANGE_BRIGHTEST,
    SL_ORANGE_DARK,
    SL_ORANGE_DARKER,
    SL_ORANGE_MEDIUM,
)
from src.gui.menu.components import AbstractButton
from src.support import import_font


def _draw_box(
    surface: pygame.Surface, pos: tuple[float, float], size: tuple[float, float]
):
    padding = 12
    outer_line_width = 3
    inner_line_width = 8
    rect = pygame.Rect(
        pos[0] - size[0] / 2 - padding,
        pos[1] - size[1] / 2 - padding,
        size[0] + padding * 2,
        size[1] + padding * 2,
    )

    # border shadow
    pygame.draw.rect(
        surface,
        SL_ORANGE_DARKER,
        (
            rect.x - inner_line_width - outer_line_width,
            rect.y - inner_line_width + outer_line_width,
            rect.w + inner_line_width * 2 + outer_line_width * 2,
            rect.h + inner_line_width * 2,
        ),
        border_radius=16,
    )
    # border
    pygame.draw.rect(
        surface,
        SL_ORANGE_DARK,
        (
            rect.x - inner_line_width,
            rect.y - inner_line_width,
            rect.w + inner_line_width * 2,
            rect.h + inner_line_width * 2,
        ),
        border_radius=16,
    )
    # background
    pygame.draw.rect(surface, SL_ORANGE_BRIGHT, rect, border_radius=12)


class LayoutRect(pygame.Rect, ABC):
    def __init__(self, dimensions: tuple[int, int]):
        super().__init__((0, 0), dimensions)

    @abstractmethod
    def draw(self):
        pass


class TextChunk(LayoutRect):
    def __init__(
        self,
        text: str,
        font: pygame.Font,
        color: tuple[int, int, int] = SL_ORANGE_BRIGHTEST,
    ):
        self.font = font
        self.text = text
        self.text_rect = pygame.Rect((0, 0), self.font.size(text))

        self.color = color

        dimensions = self.text_rect.size

        super().__init__(dimensions)

        self.height = self.font.get_height()

    def draw(self):
        return self.font.render(text=self.text, antialias=True, color=self.color)


class Linebreak(LayoutRect):
    def __init__(self, dimensions: tuple[int, int] = (0, 0)):
        super().__init__(dimensions)

    def draw(self):
        return pygame.Surface(self.size, pygame.SRCALPHA)


class Text:
    def __init__(self, *text: LayoutRect):
        self.text = text
        self.surface_rect = None
        self._calculate_rect()

    @staticmethod
    def _handle_end_of_line(
        current_line: list[TextChunk],
        current_position: pygame.Vector2,
        max_line_width: int,
    ) -> int:
        if current_line:
            max_baseline_y = max([chunk.font.get_ascent() for chunk in current_line])
            for chunk in current_line:
                chunk.y += max_baseline_y - chunk.font.get_ascent()
            current_line.clear()

        if current_position.x > max_line_width:
            return current_position.x
        return max_line_width

    def _calculate_rect(self):
        current_position = pygame.math.Vector2((0, 0))
        line_height = 0
        max_line_width = 0
        current_line: list[TextChunk] = []
        for text_chunk in self.text:
            text_chunk.topleft += current_position.xy

            if isinstance(text_chunk, TextChunk):
                current_position.x += text_chunk.width
                chunk_line_height = text_chunk.font.get_linesize()
                if line_height < chunk_line_height:
                    line_height = chunk_line_height
                current_line.append(text_chunk)

            elif isinstance(text_chunk, Linebreak):
                max_line_width = self._handle_end_of_line(
                    current_line, current_position, max_line_width
                )

                current_position.x = 0
                current_position.y += line_height + text_chunk.height
                line_height = 0

        max_line_width = self._handle_end_of_line(
            current_line, current_position, max_line_width
        )

        self.surface_rect = pygame.Rect(
            (0, 0, max_line_width, current_position.y + line_height)
        )

    def draw(self, surface: pygame.Surface):
        for text_chunk in self.text:
            surface.blit(text_chunk.draw(), (text_chunk.x, text_chunk.y))


class _ReturnButton(AbstractButton):
    def __init__(self, name: str):
        super().__init__(name, pygame.Rect())
        self.font_button = import_font(28, "font/LycheeSoda.ttf")
        self.color = SL_ORANGE_MEDIUM
        self.content = self.font_button.render(self._content, True, SL_ORANGE_BRIGHTEST)
        self._content_rect = self.content.get_frect()
        self.rect = self._content_rect.copy()

        # padding
        self.rect.width += 24
        self.rect.height += 12

        self.initial_rect = self.rect.copy()
        self._content_rect.center = self.rect.center

    @property
    def text(self):
        return self._content

    def draw_hover(self):
        if self.mouse_hover():
            self.hover_active = True
            pygame.draw.rect(self.display_surface, SL_ORANGE_DARK, self.rect, 4, 4)
        else:
            self.hover_active = False

    def move(self, topleft: tuple[float, float]):
        self.rect.topleft = topleft
        self.initial_rect.center = self.rect.center
        self._content_rect.center = self.rect.center

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, SL_ORANGE_DARKER, self.rect.move(3, 3), 6, 4)
        super().draw(surface)
