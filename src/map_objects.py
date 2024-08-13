from dataclasses import dataclass

import pygame
import logging
LOG = logging.getLogger(__name__)
LOG.info('Importing pytmx...')
from pytmx import TiledMap
LOG.info('pytmx imported.')

from src.settings import SCALE_FACTOR


@dataclass
class MapObjectType:
    gid: int = None

    image: pygame.Surface = None
    hitbox: pygame.FRect = None


class MapObjects:
    _objects: dict[int, MapObjectType]

    _tilemap: TiledMap

    def __init__(self, tilemap: TiledMap):
        self._tilemap = tilemap

        self._objects = {}
        for gid, hitbox_list in self._tilemap.get_tile_colliders():
            map_object = MapObjectType(gid=gid)

            map_object.image = self._tilemap.get_tile_image_by_gid(gid)
            if len(hitbox_list) > 0:
                hitbox = hitbox_list[0]
                map_object.hitbox = pygame.FRect(
                    hitbox.x * SCALE_FACTOR,  # noqa
                    hitbox.y * SCALE_FACTOR,  # noqa
                    hitbox.width * SCALE_FACTOR,  # noqa
                    hitbox.height * SCALE_FACTOR,  # noqa
                )
            else:
                map_object.hitbox = map_object.image.get_frect()
            self._objects[gid] = map_object

    def __getitem__(self, gid):
        try:
            return self._objects[gid]
        except KeyError as e:
            raise KeyError(
                f"No object with gid {gid}.\nCheck if you "
                f"defined a valid hitbox on the object you "
                f"tried to access."
            ) from e

    def get(self, gid):
        return self._objects.get(
            gid, MapObjectType(gid=gid, image=self._tilemap.get_tile_image_by_gid(gid))
        )
