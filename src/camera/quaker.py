"""Implementation of a quake effect."""

from types import MappingProxyType

import pygame

from src.camera import Camera
from src.enums import Direction

_DIRECTIONAL_VECTORS = MappingProxyType(
    {
        Direction.UP: pygame.Vector2(0, -8),
        Direction.DOWN: pygame.Vector2(0, 8),
        Direction.LEFT: pygame.Vector2(-8, 0),
        Direction.RIGHT: pygame.Vector2(8, 0),
        Direction.UPLEFT: pygame.Vector2(-8, -8),
        Direction.UPRIGHT: pygame.Vector2(8, -8),
        Direction.DOWNLEFT: pygame.Vector2(-8, 8),
        Direction.DOWNRIGHT: pygame.Vector2(8, 8),
    }
)


_DIRSWAP_DELAY = 0.03


class Quaker:
    def __init__(self, cam: Camera):
        self.camera = cam
        self.quaking = False
        self.quake_duration: float = 0
        self.quake_elapsed: float = 0
        self.swap_delay: float = 0
        self.direction: Direction | None = None

    def reset(self):
        self.quaking = False
        self.quake_duration: float = 0
        self.quake_elapsed: float = 0
        self.swap_delay: float = 0
        self.direction: Direction | None = None
        self.camera.set_quake_vec(None)

    def start(self, duration: float):
        """Set a quake duration and start the earthquake effect."""
        if self.quaking:
            return
        self.reset()
        self.quaking = True
        self.quake_duration = duration
        self.quake_elapsed = 0
        self.swap_delay = 0
        self.direction = Direction.random()
        self.camera.set_quake_vec(_DIRECTIONAL_VECTORS[self.direction])

    def update_quake(self, dt: float):
        """Update the quake effect."""
        if not self.quaking:
            return
        self.quake_elapsed += dt
        self.swap_delay += dt
        if self.swap_delay >= _DIRSWAP_DELAY:
            self.direction = self.direction.get_opposite()
            self.camera.set_quake_vec(_DIRECTIONAL_VECTORS[self.direction])
            self.swap_delay = 0
        if self.quake_elapsed >= self.quake_duration:
            self.quaking = False
            self.camera.set_quake_vec(None)
