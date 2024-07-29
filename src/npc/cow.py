import math
import random

import pygame

from src.enums import Layer
from src.npc.bases.cow_base import CowBase
from src.npc.behaviour.cow_behaviour_tree import (
    CowBehaviourTree,
    CowBehaviourTreeContext
)
from src.npc.behaviour.cow_flee_behaviour_tree import (
    CowFleeBehaviourTree,
    CowFleeBehaviourTreeContext
)
from src.npc.setup import AIData
from src.settings import Coordinate, AniFrames, SCALED_TILE_SIZE
from src.sprites.character import Character
from src.sprites.setup import EntityAsset
from src.support import get_flight_matrix


class Cow(CowBase):
    def __init__(
            self,
            pos: Coordinate,
            assets: EntityAsset,
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group,

            player: Character
    ):
        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,

            pf_matrix=AIData.Matrix,
            pf_grid=AIData.Grid,
            pf_finder=AIData.CowPathFinder,

            z=Layer.MAIN
        )

        self.player = player

        self.fleeing = False

    def exit_idle(self):
        CowBehaviourTree.tree.run(CowBehaviourTreeContext(self))

    def exit_moving(self):
        self.speed = 150
        self.fleeing = False

    def update(self, dt: float):
        CowFleeBehaviourTree.tree.run(
            CowFleeBehaviourTreeContext(self, self.player)
        )
        super().update(dt)

    def flee_from_pos(self, pos: tuple[int, int]) -> bool:
        """
        Aborts the current path of the cow and makes it flee into the opposite
        direction of the given position.
        :param pos: Position on the Tilemap that should be fled from
        """
        if not self.fleeing:
            self.abort_path()

            self.speed = 350
            self.fleeing = True

            # current NPC position on the tilemap
            tile_coord = (int(self.rect.centerx / SCALED_TILE_SIZE),
                          int(self.rect.centery / SCALED_TILE_SIZE))

            flight_radius = 5

            flight_matrix = get_flight_matrix(
                pos=(tile_coord[0] - pos[0], tile_coord[1] - pos[1]),
                radius=5,

                # Further decreasing the angle value might make the cow's
                #  behaviour more predictable, but puts it at a higher risk of
                #  not finding any walkable area in the given angle, and thus
                #  leading to the cow fleeing in a random direction instead
                angle=math.pi / 4
            )

            avail_coords = []

            for y in range(flight_radius * 2 + 1):
                for x in range(flight_radius * 2 + 1):
                    y_pos = y - flight_radius
                    x_pos = x - flight_radius
                    if not flight_matrix[y_pos][x_pos]:
                        continue
                    if ((0 <= tile_coord[0] + x_pos < self.pf_grid.width)
                        and
                       (0 <= tile_coord[1] + y_pos < self.pf_grid.height)):
                        avail_coords.append((tile_coord[0] + x_pos,
                                             tile_coord[1] + y_pos))

            random.shuffle(avail_coords)

            for coord in avail_coords:
                if self.create_path_to_tile(coord):
                    break
            else:
                avail_x_coords = list(range(
                    max(0, tile_coord[0] - flight_radius),
                    min(tile_coord[0] + flight_radius,
                        self.pf_grid.width - 1) + 1
                ))

                avail_y_coords = list(range(
                    max(0, tile_coord[1] - flight_radius),
                    min(tile_coord[1] + flight_radius,
                        self.pf_grid.height - 1) + 1
                ))

                for i in range(min(len(avail_x_coords), len(avail_y_coords))):
                    pos = (
                        random.choice(avail_x_coords),
                        random.choice(avail_y_coords)
                    )
                    avail_x_coords.remove(pos[0])
                    avail_y_coords.remove(pos[1])

                    if self.create_path_to_tile(pos):
                        break
                else:
                    self.abort_path()
                    return False
            return True
        return False
