from collections.abc import Callable

from pygame.math import Vector2 as vector

from src.enums import Layer
from src.settings import GROW_SPEED, SCALE_FACTOR
from src.sprites.base import Sprite


class Plant(Sprite):
    def __init__(self, seed_type, groups, tile, frames):
        super().__init__(tile.rect.center, frames[0], groups, Layer.PLANT)
        self.rect.center = tile.rect.center + vector(0.5, -3) * SCALE_FACTOR
        self.tile = tile
        self.frames = frames
        self.hitbox = None

        self.seed_type = seed_type
        self.age = 0
        self.max_age = len(self.frames) - 1
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

    def grow(self):
        if self.tile.watered:
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = Layer.MAIN
                self.hitbox = self.rect.inflate(-26, -self.rect.height * 0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_frect(
                midbottom=self.tile.rect.midbottom + vector(0, 2)
            )
