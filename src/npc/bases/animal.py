from abc import ABC

from src.enums import Direction
from src.sprites.entities.entity import Entity


class Animal(Entity, ABC):
    def animate(self, dt):
        super().animate(dt)

    def get_facing_direction(self):
        # Animals can only face left and right
        if self.direction.x > 0:
            self.facing_direction = Direction.RIGHT
        elif self.direction.x < 0:
            self.facing_direction = Direction.LEFT
