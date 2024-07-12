
import random
import pygame
from src.sprites.base import Sprite
from src import timer

class WaterDrop(Sprite):
    def __init__(self, pos, surf, groups, moving, z):
        super().__init__(pos, surf, groups, z)
        self.timer = timer.Timer(
            random.randint(400, 600),
            autostart=True,
            func=self.kill,
        )
        self.start_time = pygame.time.get_ticks()
        self.moving = moving

        if moving:
            self.direction = pygame.Vector2(-2, 4)
            self.speed = random.randint(200, 250)

    def update(self, dt):
        self.timer.update()
        if self.moving:
            self.rect.topleft += self.direction * self.speed * dt
