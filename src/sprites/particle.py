import pygame

from src.enums import Layer
from src.sprites.base import Sprite
from src.timer import Timer


class ParticleSprite(Sprite):
    def __init__(self, pos, surf, groups, duration=300):
        white_surf = pygame.mask.from_surface(surf).to_surface()
        white_surf.set_colorkey("black")
        super().__init__(pos, white_surf, groups, Layer.PARTICLES)
        self.timer = Timer(duration, autostart=True, func=self.kill)

    def update(self, dt):
        self.timer.update()
