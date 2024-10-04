import os

import pygame


class fast_forward:
    def __init__(self) -> None:
        self.sprites = []
        for filename in os.listdir("images\\fast_forward"):
            if filename.endswith(".png"):
                img = pygame.image.load(
                    os.path.join("images\\fast_forward", filename)
                ).convert_alpha()
                self.sprites.append(img)
                self.current_frame = 0
                self.total_frame = 10

    def draw_overlay(self, display_surface):
        display_surface.blit(self.sprites[self.current_frame], (0, 0))
        self.current_frame += 1
        if self.current_frame >= self.total_frame:
            self.current_frame = 0
