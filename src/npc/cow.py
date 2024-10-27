import pygame
from pathfinding.core.grid import Grid

from src.enums import Layer
from src.npc.bases.cow_base import CowBase
from src.npc.behaviour.cow_behaviour_tree import CowIndividualContext
from src.npc.utils import pf_move_to
from src.settings import Coordinate
from src.sprites.chunk_system.collision_chunks import CollisionManager
from src.sprites.setup import EntityAsset
from src.support import get_sorted_flight_vectors


class Cow(CowBase):
    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_manager: CollisionManager,
    ):
        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_manager=collision_manager,
            behaviour_tree_context=CowIndividualContext(self),
            z=Layer.MAIN,
        )

        self.fleeing = False

    def stop_moving(self):
        super().stop_moving()

        self.speed = 150
        self.fleeing = False

    def flee_from_pos(self, pos: tuple[int, int], pf_grid: Grid = None) -> bool:
        """
        Aborts the current path of the cow and makes it flee into the opposite
        direction of the given position.
        FIXME: When a Cow is locked in a position they can't flee from, they'll still
         check every path if it is possible, decreasing the frame rate by quite a bit
        :param pos: Position on the Tilemap that should be fled from
        :param pf_grid: (Optional) pathfinding grid to use. Defaults to self.pf_grid
        :return: Whether the path has successfully been created.
        """
        if not self.fleeing:
            self.abort_path()

            self.speed = 350
            self.fleeing = True

            # current NPC position on the tilemap
            tile_coord = self.get_tile_pos()

            flight_vectors = get_sorted_flight_vectors(
                pos=(tile_coord[0] - pos[0], tile_coord[1] - pos[1]),
                radius=5,
            )

            for coordinate in flight_vectors:
                x_coord = tile_coord[0] + coordinate.x - 5
                y_coord = tile_coord[1] + coordinate.y - 5
                if pf_move_to(self, (x_coord, y_coord), 5, pf_grid=pf_grid):
                    return True
        return False
