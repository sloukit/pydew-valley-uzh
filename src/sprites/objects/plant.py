from collections.abc import Callable

import pygame
from pygame.math import Vector2 as vector

from src.enums import Layer
from src.settings import GROW_SPEED, SCALE_FACTOR
from src.sprites.base import Sprite


class Plant(Sprite):
    def __init__(self, seed_type, groups, tile, frames):
        super().__init__(tile.rect.center, frames[0], groups, Layer.MAIN)
        self.tile = tile
        self.frames = frames

        self.seed_type = seed_type
        self.max_age = len(self.frames) - 1
        self.age = 0
        self.grow_speed = GROW_SPEED[seed_type.as_plant_name()]

        self._on_harvestable_funcs = []
        self.harvestable = False

    @property
    def harvestable(self):
        return self._harvestable

    @harvestable.setter
    def harvestable(self, value):
        for func in self._on_harvestable_funcs:
            func(value)

        self._harvestable = value

    def on_harvestable(self, func: Callable[[bool], None]):
        self._on_harvestable_funcs.append(func)

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, value: float):
        self._age = value

        if self.age >= self.max_age:
            self._age = self.max_age
            self.harvestable = True

        self.image = self.frames[int(self.age)]
        self.rect = self.image.get_frect(
            midbottom=self.tile.rect.midbottom + vector(0, 2)
        )

        hitbox_height = 8 * SCALE_FACTOR
        self.hitbox_rect = pygame.Rect(
            self.rect.bottomleft, (self.rect.width, hitbox_height)
        ).move(0, -hitbox_height)
        # makes the Plant get render as if it was 3px higher, so that the small dirt
        # patch around its root does not overlap any other Sprites
        self.hitbox_rect.move_ip(0, -3 * SCALE_FACTOR)

    def grow(self):
        if self.tile.watered:
            self.age += self.grow_speed
