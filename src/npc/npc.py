from __future__ import annotations

from typing import Callable

from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from src.npc.npc_base import NPCState, NPCBase
from src.npc.npc_behaviour import NPCBehaviourContext, NPCBehaviourMethods
from src.enums import InventoryResource
from src.settings import SCALE_FACTOR, SCALED_TILE_SIZE
from src.settings import Coordinate, AniFrames

import pygame
import random


class NPC(NPCBase):

    def __init__(
            self,
            pos: Coordinate,
            frames: dict[str, AniFrames],
            groups: tuple[pygame.sprite.Group],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable,
            soil_layer,
            pf_matrix: list[list[int]],
            pf_grid: Grid,
            pf_finder: AStarFinder):

        self.soil_layer = soil_layer

        self.pf_matrix = pf_matrix
        self.pf_grid = pf_grid
        self.pf_finder = pf_finder
        self.pf_state = NPCState.IDLE
        self.pf_state_duration = 0
        self.pf_path = []

        self.__on_path_abortion_funcs = []
        self.__on_path_completion_funcs = []

        super().__init__(
            pos,
            frames,
            groups,
            collision_sprites,

            (32 * SCALE_FACTOR, 32 * SCALE_FACTOR),
            # scales the hitbox down to the exact tile size

            apply_tool
        )

        self.speed = 150

        # TODO: Ensure that the NPC always has all needed seeds it needs in its inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 999,
            InventoryResource.TOMATO_SEED: 999,
        }

    def on_path_abortion(self, func: Callable[[], None]):
        self.__on_path_abortion_funcs.append(func)
        return

    def abort_path(self):
        self.pf_state = NPCState.IDLE
        self.direction.update((0, 0))
        self.pf_state_duration = 1

        for func in self.__on_path_abortion_funcs:
            func()

        self.__on_path_abortion_funcs.clear()
        self.__on_path_completion_funcs.clear()
        return

    def on_path_completion(self, func: Callable[[], None]):
        self.__on_path_completion_funcs.append(func)
        return

    def complete_path(self):
        self.pf_state = NPCState.IDLE
        self.direction.update((0, 0))
        self.pf_state_duration = random.randint(2, 5)

        for func in self.__on_path_completion_funcs:
            func()

        self.__on_path_abortion_funcs.clear()
        self.__on_path_completion_funcs.clear()
        return

    def create_path_to_tile(self, coord: tuple[int, int]) -> bool:
        if not self.pf_grid.walkable(coord[0], coord[1]):
            return False

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(self.rect.centerx, self.rect.centery) / SCALED_TILE_SIZE

        self.pf_state = NPCState.MOVING
        self.pf_state_duration = 0

        self.pf_grid.cleanup()

        start = self.pf_grid.node(int(tile_coord.x), int(tile_coord.y))
        end = self.pf_grid.node(*[int(i) for i in coord])

        path_raw = self.pf_finder.find_path(start, end, self.pf_grid)

        # The first position in the path will always be removed as it is the
        # same coordinate the NPC is already standing on. Otherwise, if the
        # NPC is just standing a little bit off the center of its current
        # coordinate, it may turn around quickly once it reaches it, if the
        # second coordinate of the path points in the same direction as where
        # the NPC was just standing.
        self.pf_path = [(i.x + .5, i.y + .5) for i in path_raw[0][1:]]

        if not self.pf_path:
            self.abort_path()
            return False

        return True

    def move(self, dt):
        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(self.rect.centerx, self.rect.centery) / SCALED_TILE_SIZE

        if self.pf_state == NPCState.IDLE:
            self.pf_state_duration -= dt

            if self.pf_state_duration <= 0:
                NPCBehaviourMethods.behaviour.run(NPCBehaviourContext(self))

        if self.pf_state == NPCState.MOVING:
            if not self.pf_path:
                # runs in case the path has been emptied in the meantime
                # (e.g. NPCBehaviourMethods.wander_to_interact created a path
                # to a tile adjacent to the NPC)
                self.complete_path()
                return

            next_position = (tile_coord.x, tile_coord.y)

            # remaining distance the npc moves in the current frame
            remaining_distance = self.speed * dt / SCALED_TILE_SIZE

            while remaining_distance:
                if next_position == self.pf_path[0]:
                    # the NPC reached its current target position
                    self.pf_path.pop(0)

                if not len(self.pf_path):
                    # the NPC has completed its path
                    self.complete_path()
                    break

                # x- and y-distances from the NPCs current position to its target position
                dx = self.pf_path[0][0] - next_position[0]
                dy = self.pf_path[0][1] - next_position[1]

                distance = (dx ** 2 + dy ** 2) ** 0.5

                if remaining_distance >= distance:
                    # the NPC reaches its current target position in the current frame
                    next_position = self.pf_path[0]
                    remaining_distance -= distance
                else:
                    # the NPC does not reach its current target position in the current frame,
                    #  so it continues to move towards it
                    next_position = (
                        next_position[0] + dx * remaining_distance / distance,
                        next_position[1] + dy * remaining_distance / distance
                    )
                    remaining_distance = 0

                    # Rounding the direction leads to smoother animations,
                    # e.g. if the distance vector was (-0.99, -0.01), the NPC
                    # would face upwards, although it moves much more to the
                    # left than upwards, as the animation method favors
                    # vertical movement
                    #
                    # Maybe normalise the vector?
                    # Currently, it is not necessary as the NPC is not moving
                    # diagonally yet, unless it collides with another entity
                    # while it is in-between two coordinates
                    self.direction.update((round(dx / distance), round(dy / distance)))

            self.hitbox_rect.update((
                next_position[0] * SCALED_TILE_SIZE - self.hitbox_rect.width / 2,
                self.hitbox_rect.top,
            ), self.hitbox_rect.size)
            colliding = self.collision('horizontal')

            self.hitbox_rect.update((
                self.hitbox_rect.left,
                next_position[1] * SCALED_TILE_SIZE - self.hitbox_rect.height / 2
            ), self.hitbox_rect.size)
            colliding = colliding or self.collision('vertical')

            if colliding:
                self.abort_path()

        self.rect.update((self.hitbox_rect.centerx - self.rect.width / 2,
                          self.hitbox_rect.centery - self.rect.height / 2), self.rect.size)
        self.plant_collide_rect.center = self.hitbox_rect.center
