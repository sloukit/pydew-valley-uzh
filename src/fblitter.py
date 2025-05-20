from typing import Sequence

import pygame
# from pygame.typing import ColorLike, Point, RectLike

from src.colors import SL_ORANGE_BRIGHT, SL_ORANGE_DARK, SL_ORANGE_DARKER
from src.settings import IS_WEB, SCREEN_HEIGHT, SCREEN_WIDTH
from src.support import get_translated_string

# Typing stuff. This needs to be done separately so we don't run in weird shenanigans from the server.
if not IS_WEB:
    from pygame.typing import ColorLike, Point, RectLike
else:
    # Recreate the typing here (code picked from pygame.typing)
    from abc import abstractmethod
    from collections.abc import Callable
    from os import PathLike as _PathProtocol
    from typing import IO, Protocol, TypeVar, Union

    from pygame.color import Color
    from pygame.rect import FRect, Rect

    # For functions that take a file name
    _PathLike = Union[str, bytes, _PathProtocol[str], _PathProtocol[bytes]]
    # Most pygame functions that take a file argument should be able to handle a FileLike type
    FileLike = Union[_PathLike, IO[bytes], IO[str]]

    _T_co = TypeVar("_T_co", covariant=True)

    class SequenceLike(Protocol[_T_co]):
        """
        Variant of the standard `Sequence` ABC that only requires `__getitem__` and `__len__`.
        """

        @abstractmethod
        def __getitem__(self, index: int, /) -> _T_co: ...

        @abstractmethod
        def __len__(self) -> int: ...

    # Modify typehints when it is possible to annotate sizes

    # Pygame handles float without errors in most cases where a point is expected,
    # usually rounding to int. Also, 'Union[int, float] == float'
    Point = SequenceLike[float]
    # This is used where ints are strictly required
    IntPoint = SequenceLike[int]

    ColorLike = Union[Color, SequenceLike[int], str, int]

    class _HasRectAttribute(Protocol):
        # An object that has a rect attribute that is either a rect, or a function
        # that returns a rect conforms to the rect protocol
        @property
        def rect(self) -> Union["RectLike", Callable[[], "RectLike"]]: ...

    RectLike = Union[
        Rect, FRect, SequenceLike[float], SequenceLike[Point], _HasRectAttribute
    ]

    # cleanup namespace
    del (
        abstractmethod,
        Color,
        Rect,
        FRect,
        IO,
        Callable,
        Union,
        TypeVar,
        Protocol,
    )


class _FBlitterType:
    """Singleton type allowing for uniform fast blitting across every other file."""

    _WAS_INSTANTIATED = False

    def __new__(cls, *args, **kwargs):
        if cls._WAS_INSTANTIATED:
            return FBLITTER
        return super().__new__(cls)

    def __init__(self):
        self.current_surf = self._default_surf = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        pygame.display.set_caption(get_translated_string("game_title"))
        self._current_blit_list = []
        self._default_blit_list = []

    @property
    def is_on_display_surf(self):
        return self.current_surf is self._default_surf

    def reset_to_default_surf(self):
        """Reset the current surface to the display surface.

        MAKE SURE YOU'VE DRAWN EVERYTHING YOU WANTED TO DRAW BEFORE CALLING THIS."""
        self.current_surf = self._default_surf

    def set_current_surf(self, surf: pygame.Surface):
        """Allows to override the blitting until the current scheduled blits are all made."""
        if self.is_on_display_surf and surf is self._default_surf:
            return
        self.current_surf = surf
        self._current_blit_list.clear()

    def _blit_all_internal(self):
        if self.is_on_display_surf:
            self.current_surf.fblits(self._default_blit_list)
            self._default_blit_list.clear()
            return True
        self.current_surf.fblits(self._current_blit_list)
        self._current_blit_list.clear()
        return False

    def blit_all(self):
        """Blits everything saved for the current surface and then resets the current surface to the default display surface.

        Blits saved for the display surface are NOT performed if the current surface isn't the display surface."""
        return self._blit_all_internal() or self.reset_to_default_surf()

    def blit_with_special_flags(self, surf: pygame.Surface, pos: RectLike, flags: int):
        self._blit_all_internal()
        self.current_surf.blit(surf, pos, special_flags=flags)

    def schedule_blit(self, surf: pygame.Surface, pos: RectLike):
        if self.is_on_display_surf:
            self._default_blit_list.append((surf, pos))
        else:
            self._current_blit_list.append((surf, pos))

    def schedule_blits(self, blit_seq: Sequence[tuple[pygame.Surface, RectLike]]):
        if self.is_on_display_surf:
            self._default_blit_list.extend(blit_seq)
        else:
            self._current_blit_list.extend(blit_seq)

    def draw_rect(
        self,
        color: ColorLike,
        rect: pygame.Rect,
        width=0,
        border_radius=0,
        border_top_left_radius=-1,
        border_top_right_radius=-1,
        border_bottom_left_radius=-1,
        border_bottom_right_radius=-1,
    ):
        """Allows for pygame.draw.rect to be executed while still performing fast blitting.
        See pygame.draw.rect for documentation.
        (The surface parameter is the current surface set in the fblitter.)"""
        computed_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            computed_surf,
            color,
            pygame.Rect((0, 0), rect.size),
            width,
            border_radius,
            border_top_left_radius,
            border_top_right_radius,
            border_bottom_left_radius,
            border_bottom_right_radius,
        )
        self.schedule_blit(computed_surf, rect)

    def draw_polygon(self, color: ColorLike, points: Sequence[Point], width=0):
        """See pygame.draw.polygon for reference."""
        self._blit_all_internal()
        pygame.draw.polygon(self.current_surf, color, points, width)

    def draw_circle(
        self,
        color: ColorLike,
        center: Point,
        radius: int | float,
        width=0,
        draw_top_right=None,
        draw_top_left=None,
        draw_bottom_left=None,
        draw_bottom_right=None,
    ):
        """See pygame.draw.circle for reference."""
        self._blit_all_internal()
        pygame.draw.circle(
            self.current_surf,
            color,
            center,
            radius,
            width,
            draw_top_right,
            draw_top_left,
            draw_bottom_left,
            draw_bottom_right,
        )

    def draw_aacircle(
        self,
        color: ColorLike,
        center: Point,
        radius: int | float,
        width=0,
        draw_top_right=None,
        draw_top_left=None,
        draw_bottom_left=None,
        draw_bottom_right=None,
    ):
        """See pygame.draw.aacircle for reference."""
        self._blit_all_internal()
        pygame.draw.aacircle(
            self.current_surf,
            color,
            center,
            radius,
            width,
            draw_top_right,
            draw_top_left,
            draw_bottom_left,
            draw_bottom_right,
        )

    def draw_ellipse(self, color: ColorLike, rect: pygame.Rect, width=0):
        """See pygame.draw.ellipse for reference."""
        self._blit_all_internal()
        pygame.draw.ellipse(self.current_surf, color, rect, width)

    def draw_arc(
        self,
        color: ColorLike,
        rect: pygame.Rect,
        start_angle: float,
        stop_angle: float,
        width=1,
    ):
        """See pygame.draw.arc for reference."""
        self._blit_all_internal()
        pygame.draw.arc(self.current_surf, color, rect, start_angle, stop_angle, width)

    def draw_line(self, color: ColorLike, start_pos: Point, end_pos: Point, width=1):
        """See pygame.draw.line for reference."""
        self._blit_all_internal()
        pygame.draw.line(self.current_surf, color, start_pos, end_pos, width)

    def draw_lines(
        self, color: ColorLike, closed: bool, points: Sequence[Point], width=1
    ):
        """See pygame.draw.lines for reference."""
        self._blit_all_internal()
        pygame.draw.lines(self.current_surf, color, closed, points, width)

    def draw_aaline(self, color: ColorLike, start_pos: Point, end_pos: Point, width=1):
        """See pygame.draw.aaline for reference."""
        self._blit_all_internal()
        pygame.draw.aaline(self.current_surf, color, start_pos, end_pos, width)

    def draw_aalines(self, color: ColorLike, closed: bool, points: Sequence[Point]):
        """See pygame.draw.aalines for reference."""
        self._blit_all_internal()
        pygame.draw.aalines(self.current_surf, color, closed, points)

    def draw_box(self, pos: Point, size: Point):
        """Draws a box. Used in the cow herding overlay."""
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
        self.draw_rect(
            SL_ORANGE_DARKER,
            pygame.Rect(
                rect.x - inner_line_width - outer_line_width,
                rect.y - inner_line_width + outer_line_width,
                rect.w + inner_line_width * 2 + outer_line_width * 2,
                rect.h + inner_line_width * 2,
            ),
            border_radius=16,
        )
        # border
        self.draw_rect(
            SL_ORANGE_DARK,
            pygame.Rect(
                rect.x - inner_line_width,
                rect.y - inner_line_width,
                rect.w + inner_line_width * 2,
                rect.h + inner_line_width * 2,
            ),
            border_radius=16,
        )
        # background
        self.draw_rect(SL_ORANGE_BRIGHT, rect, border_radius=12)


FBLITTER = _FBlitterType()  # noqa
"""Fast-blitter allowing to decrease time spent on drawing stuff on the screen and auxiliary surfaces.
Please use this instead of the regular operations."""
