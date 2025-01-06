from collections.abc import Callable
from math import cos, pi, sin

import pygame

from src.enums import ClockVersion
from src.overlay.game_time import GameTime
from src.settings import OVERLAY_POSITIONS, USE_GAME_TIME
from src.support import import_font


class Clock:
    def __init__(
        self,
        game_time: GameTime,
        get_world_time: Callable[[None], tuple[int, int]],
        clock_ver: ClockVersion = ClockVersion.ANALOG,
    ):
        # setup
        self.display_surface = pygame.display.get_surface()
        self.game_time = game_time

        # dimensions
        self.left = 20
        self.top = 20

        if USE_GAME_TIME:
            self.get_time = lambda: self.game_time.get_time()
        else:
            self.get_time = get_world_time

        # analog
        if clock_ver == ClockVersion.ANALOG:
            width, height = 80, 80
            self.center = pygame.math.Vector2(
                self.left + width / 2, self.top + height / 2
            )
            self.hand_length = width / 3

            self.rect = pygame.Rect(self.left, self.top, width, height)
            self.display = self.display_analog

        elif clock_ver == ClockVersion.DIGITAL:
            width, height = 100, 50
            self.font = import_font(40, "font/LycheeSoda.ttf")

            self.rect = pygame.Rect(self.left, self.top, width, height)
            self.display = self.display_digital

        self.rect.topright = OVERLAY_POSITIONS["clock"]

    def display_analog(self):
        # get time
        time = self.get_time()
        hour = time[0] % 12
        minute = time[1]

        # frame
        pygame.draw.rect(self.display_surface, "White", self.rect, 0, 10)
        pygame.draw.rect(self.display_surface, "Black", self.rect, 5, 10)

        # hands position
        hour_hand_angle = 2 * pi * (hour * 60 + minute) / (12 * 60) - pi / 2
        minute_hand_angle = 2 * pi * minute / 60 - pi / 2
        hour_vector = self.center + 0.75 * self.hand_length * pygame.math.Vector2(
            cos(hour_hand_angle), sin(hour_hand_angle)
        )
        minute_vector = self.center + self.hand_length * pygame.math.Vector2(
            cos(minute_hand_angle), sin(minute_hand_angle)
        )

        # draw hands
        pygame.draw.line(self.display_surface, "Black", self.center, minute_vector, 5)
        pygame.draw.line(self.display_surface, "Black", self.center, hour_vector, 5)
        pygame.draw.circle(self.display_surface, "Black", self.center, 4)

    def display_digital(self):
        # get time
        time = self.get_time()

        # if hours are less than 10, add a 0 to stay in the hh:mm format
        hours = str(time[0]).rjust(2, "0")

        # if minutes are less than 10, add a 0 to stay in the hh:mm format
        minutes = str(time[1]).rjust(2, "0")

        # rects and surfs
        pady = 2

        colon_surf = self.font.render(":", False, "Black")
        colon_rect = colon_surf.get_frect(
            center=(self.rect.centerx, self.rect.centery + pady)
        )

        hour_surf = self.font.render(hours, False, "Black")
        hour_rect = hour_surf.get_frect(
            midright=(self.rect.centerx - colon_rect.width, self.rect.centery + pady)
        )

        minute_surf = self.font.render(minutes, False, "Black")
        minute_rect = minute_surf.get_frect(
            midleft=(self.rect.centerx + colon_rect.width, self.rect.centery + pady)
        )

        # display
        pygame.draw.rect(self.display_surface, "White", self.rect, 0, 4)
        pygame.draw.rect(self.display_surface, "Black", self.rect, 4, 4)
        self.display_surface.blit(colon_surf, colon_rect)
        self.display_surface.blit(hour_surf, hour_rect)
        self.display_surface.blit(minute_surf, minute_rect)
