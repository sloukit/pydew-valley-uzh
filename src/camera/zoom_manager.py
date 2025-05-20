import warnings
from typing import Iterable

import pygame

from src.enums import ZoomState
from src.exceptions import CameraWarning, InvalidMapError
from src.gui.scene_animation import SceneAnimation
from src.sprites.base import Sprite

from ..fblitter import FBLITTER
from .zoom_area import ZoomArea


class ZoomManager:
    def __init__(self):
        self._zoom_areas: list[ZoomArea] = []
        self.current_zoom_area: ZoomArea | None = None
        self.zoom_state: ZoomState = ZoomState.NOT_ZOOMING
        self.zoom_speed = 1
        self.zoom_factor = 0

    @staticmethod
    def _check_za_not_intersecting(areas: Iterable[ZoomArea]):
        areas_save = list(areas)
        for zoom_area in areas_save:
            intersections = zoom_area.area.collideobjectsall(
                # Ensuring we don't get a false positive due to the area colliding with itself
                list(filter(lambda zarea: zarea is not zoom_area, areas_save)),
                key=lambda obj: obj.area,
            )
            if intersections:
                warnings.warn(
                    f"Zoom area of ID {zoom_area.id} intersects with areas of ID "
                    f"{[area.id for area in intersections]}."
                    f"Move all the conflicting areas away from each other on the "
                    f"involved map before loading the game again!",
                    CameraWarning,
                )
                raise InvalidMapError("zoom areas cannot intersect with each other")
            yield zoom_area

    def clear(self):
        self.current_zoom_area = None
        self.zoom_state = ZoomState.NOT_ZOOMING
        self.zoom_factor = 0
        self.zoom_speed = 1
        self._zoom_areas.clear()

    def set_zoom_areas(self, zoom_areas: Iterable[ZoomArea]):
        self._zoom_areas.extend(self._check_za_not_intersecting(zoom_areas))

    def _prepare_zoom_in(self, area: ZoomArea):
        self.zoom_state = ZoomState.ZOOMING_IN
        self.current_zoom_area = area
        self.zoom_factor = 0
        self.zoom_speed = area.zoom_speed

    def _prepare_zoom_out(self):
        self.zoom_state = ZoomState.ZOOMING_OUT

    def _zoom_progress(self, dt: float, reverse: bool = False):
        self.zoom_factor += self.current_zoom_area.zoom_speed * dt * (1 - 2 * reverse)
        if reverse and self.zoom_factor <= 0:
            self.zoom_factor = 0
            self.zoom_state = ZoomState.NOT_ZOOMING
            self.current_zoom_area = None
        elif self.zoom_factor >= self.current_zoom_area.zoom_factor:
            self.zoom_factor = self.current_zoom_area.zoom_factor
            self.zoom_state = ZoomState.ZOOM

    def update(self, target: Sprite | SceneAnimation, dt: float):
        if self.zoom_state == ZoomState.NOT_ZOOMING:
            entered_zoom_area = target.rect.collideobjects(
                self._zoom_areas, key=lambda obj: obj.area
            )
            if entered_zoom_area is not None and target.zoom_allowed:
                self._prepare_zoom_in(entered_zoom_area)
            return

        if self.zoom_state == ZoomState.ZOOM:
            if not target.rect.colliderect(self.current_zoom_area.area):
                self._prepare_zoom_out()
            return

        self._zoom_progress(dt, (self.zoom_state == ZoomState.ZOOMING_OUT))

    def apply_zoom(self):
        surf = pygame.display.get_surface()
        surf_rect = surf.get_frect()
        zoomed_area = pygame.transform.scale_by(surf, self.zoom_factor + 1)
        zoomed_rect = zoomed_area.get_frect(center=surf_rect.center)
        FBLITTER.schedule_blit(zoomed_area, zoomed_rect)
