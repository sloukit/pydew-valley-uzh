from src.sprites.base import CollideableSprite
from src.settings import LAYERS


class Bed(CollideableSprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups, LAYERS['main'], 'Bed')
        self.hitbox_rect = self.rect.inflate(0, -20)
        self.hitbox_rect.midbottom = self.rect.midbottom