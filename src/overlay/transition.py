from collections.abc import Callable

import pygame

from src import settings
from src.fblitter import FBLITTER
from src.support import oscilating_lerp
from src.timer import Timer


class Transition:
    def __init__(
        self, reset: Callable[[], None], finish_reset: Callable[[], None], dur: int
    ):
        # setup
        self.display_surface = pygame.display.get_surface()
        self.reset = reset
        self.peaked = True
        self.timer = Timer(dur, func=finish_reset)
        self.finish_reset = finish_reset

        # overlay image
        self.image = pygame.Surface(
            (
                settings.SCREEN_WIDTH,
                settings.SCREEN_HEIGHT,
            )
        )

        # color
        self.start_color = pygame.Color(255, 255, 255)
        self.target_color = pygame.Color(0, 0, 0)
        self.curr_color = self.start_color

    def __bool__(self):
        return bool(self.timer)

    def activate(self):
        self.timer.activate()
        self.peaked = False

    def update(self):
        self.timer.update()
        if self.timer:
            t = self.timer.get_progress()
            # call reset
            if not self.peaked and t > 0.5:
                self.reset()
                self.peaked = True
            # interpolate colors
            t = oscilating_lerp(0, 1, pygame.math.smoothstep(0, 1, t))
            self.curr_color = self.start_color.lerp(self.target_color, t)

    def draw(self):
        if self.timer:
            self.image.fill(self.curr_color)
            FBLITTER.blit_with_special_flags(self.image, (0, 0), pygame.BLEND_RGBA_MULT)
