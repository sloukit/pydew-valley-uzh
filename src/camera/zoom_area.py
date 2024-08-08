import warnings
from dataclasses import dataclass, field
from typing import ClassVar

import pygame

from src.exceptions import CameraWarning


@dataclass
class ZoomArea:
    _id: int
    _area: pygame.FRect
    _zoom_factor: float = field(default=1)
    _zoom_speed: float = field(default=1)
    _registered_ids: ClassVar[set[int]] = set()

    def __new__(cls, *args, **kwargs):
        area_id = args[0]
        if area_id in cls._registered_ids:
            raise ValueError(
                f"given area ID ({area_id}) is already used for another area"
            )
        cls._registered_ids.add(area_id)
        return super().__new__(cls)

    def __del__(self):
        cls = type(self)
        cls._registered_ids.remove(self._id)

    def __post_init__(self):
        if self._zoom_factor <= 0:
            warnings.warn(
                f"given zoom factor for zoom area {self._id} was {self._zoom_factor}, check "
                f"the value you passed for this area in Tiled",
                CameraWarning,
            )
            raise ValueError("zoom factor must be strictly positive")
        if self._zoom_factor <= 0:
            warnings.warn(
                f"given zoom speed for zoom area {self._id} was {self._zoom_speed}, check "
                f"the value you set in Tiled",
                CameraWarning,
            )
        if any(1 > dim for dim in self._area) or not self._area:
            warnings.warn(
                f"rect given for the zoom area of ID {self._id} was {self._area}, "
                f"check the dimensions you set in Tiled",
                CameraWarning,
            )
            raise ValueError("invalid zoom area")

    @property
    def id(self):
        return self._id

    @property
    def area(self):
        return self._area

    @property
    def zoom_factor(self):
        return self._zoom_factor

    @property
    def zoom_speed(self):
        return self._zoom_speed
