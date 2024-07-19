from src.sprites.base import CollideableSprite
from src.settings import LAYERS
from pygame.math import Vector2 as vector

class Hill(CollideableSprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups, LAYERS['main'], 'Hill')
        self.hitbox_rect.midbottom = self.rect.midbottom + vector(0, 10)