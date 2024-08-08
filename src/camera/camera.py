import warnings

import pygame

from src.exceptions import CameraWarning
from src.gui.scene_animation import SceneAnimation
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.sprites.base import Sprite


class Camera:
    """The in-game camera."""

    def __init__(self, width: int, height: int):
        """The in-game camera.
        NOTE: the area size used by the camera is the
        CURRENT MAP's size, not the screen size!

        :param width: The covered area's width (in pixels).
        :param height: The covered area's height (in pixels)."""
        if width < 0:
            # THIS SHOULD NOT HAPPEN, HENCE THE WARNING
            warnings.warn(
                f"Given width for the camera was {width}, make sure you didn't break something!",
                CameraWarning,
            )
            raise ValueError("the camera's width must be strictly positive")
        if height < 0:
            warnings.warn(
                f"Given height for the camera was {height}, make sure you didn't break something!",
                CameraWarning,
            )
            raise ValueError("the camera's height must be strictly positive")
        self._width, self._height = width, height
        self._quake_vec: pygame.Vector2 | None = None
        self.state = pygame.Rect(0, 0, width, height)

    def change_size(self, width: int, height: int):
        if width <= 0:
            warnings.warn(
                f"Given width for the camera was {width}, make sure you didn't break something!",
                CameraWarning,
            )
            raise ValueError("the camera's width must be strictly positive")
        if height <= 0:
            warnings.warn(
                f"Given height for the camera was {height}, make sure you didn't break something!",
                CameraWarning,
            )
            raise ValueError("the camera's height must be strictly positive")
        self._width, self._height = width, height
        self.state.size = width, height

    def update(self, target: Sprite | SceneAnimation):
        self.state.update(self._complex_camera(target.rect))

    def set_quake_vec(self, vec: pygame.Vector2 | None):
        self._quake_vec = vec

    def apply(self, target: Sprite):
        ret = target.rect.move(self.state.topleft)
        if self._quake_vec is not None:
            ret.move_ip(self._quake_vec)
        return ret

    @property
    def size(self):
        return self._width, self._height

    def _complex_camera(self, target_rect: pygame.Rect):
        left, top = target_rect.topleft
        w, h = self.size
        left, top = (
            (SCREEN_WIDTH / 2) - left,
            (SCREEN_HEIGHT / 2) - top,
        )  # center player

        left = min(0, left - (target_rect.width / 2))  # stop scrolling at the left edge
        left = max(-(w - SCREEN_WIDTH), left)  # stop scrolling at the right edge
        top = max(
            -(h - SCREEN_HEIGHT), top - (target_rect.height / 2)
        )  # stop scrolling at the bottom
        top = min(0, top)  # stop scrolling at the top

        return pygame.Rect(left, top, w, h)
