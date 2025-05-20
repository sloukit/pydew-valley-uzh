import os

import pygame

from src.settings import SCREEN_WIDTH
from src.support import get_translated_string


class FastForward:
    def __init__(self) -> None:
        self.sprites = []
        for filename in os.listdir("images/fast_forward"):
            if filename.endswith(".png"):
                img = pygame.image.load(
                    os.path.join("images/fast_forward", filename)
                ).convert_alpha()
                self.sprites.append(img)
                self.current_frame = 0
                self.total_frame = 10
                self.font = pygame.font.Font("font/LycheeSoda.ttf", 30)
                self.text_surface = self.font.render(
                    get_translated_string("Right Shift to Fast Forward"),
                    True,
                    (255, 255, 255),
                )
                self.text_rect = self.text_surface.get_frect(
                    midright=((SCREEN_WIDTH - 15, 600))
                )

    def draw_overlay(self, display_surface):
        display_surface.blit(self.sprites[self.current_frame], (0, 0))
        self.current_frame += 1
        if self.current_frame >= self.total_frame:
            self.current_frame = 0

    def draw_option(self, display_surface):
        display_surface.blit(self.text_surface, self.text_rect)
