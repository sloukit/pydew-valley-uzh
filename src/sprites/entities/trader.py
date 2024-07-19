import pygame
from src.sprites.base import CollideableSprite
from src.settings import LAYERS


class Trader(CollideableSprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups, LAYERS['main'], 'Bed')
        self.hitbox_rect = pygame.Rect(pos, (34, 8))
        self.hitbox_rect.midbottom = self.rect.midbottom 