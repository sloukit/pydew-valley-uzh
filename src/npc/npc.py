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

        # The first position in the path will always be removed as it is the same coordinate the NPC is already
        #  standing on. Otherwise, if the NPC is just standing a little bit off the center of its current coordinate, it
        #  may turn around quickly once it reaches it, if the second coordinate of the path points in the same direction
        #  as where the NPC was just standing.
        self.pf_path = [(i.x + .5, i.y + .5) for i in path_raw[0][1:]]

        if not self.pf_path:
            self.abort_path()
            return False

        return True

    def move(self, dt):
        tile_coord = pygame.Vector2(self.rect.centerx, self.rect.centery) / SCALED_TILE_SIZE

        if self.pf_state == NPCState.IDLE:
            self.update_state(dt)
        elif self.pf_state == NPCState.MOVING:
            self.move_along_path(tile_coord, dt)

    def update_state(self, dt):
        self.pf_state_duration -= dt
        if self.pf_state_duration <= 0:
            NPCBehaviourMethods.behaviour.run(NPCBehaviourContext(self))

    def move_along_path(self, tile_coord, dt):
        if not self.pf_path:
            self.complete_path()
            return

        next_position = (tile_coord.x, tile_coord.y)
        remaining_distance = self.speed * dt / SCALED_TILE_SIZE

        while remaining_distance:
            if next_position == self.pf_path[0]:
                self.pf_path.pop(0)
            if not self.pf_path:
                self.complete_path()
                break

            dx, dy = self.pf_path[0][0] - next_position[0], self.pf_path[0][1] - next_position[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if remaining_distance >= distance:
                next_position, remaining_distance = self.update_next_position(next_position, distance)
            else:
                next_position, remaining_distance = self.move_to_next_position(next_position, dx, dy, distance, remaining_distance)

            self.update_direction(dx, dy, distance)

        self.rect.centerx = next_position[0] * SCALED_TILE_SIZE
        self.check_collision('horizontal')

        self.rect.centery = next_position[1] * SCALED_TILE_SIZE
        self.check_collision('vertical')

        if self.is_colliding:
            self.abort_path()

    def update_next_position(self, next_position, distance):
        next_position = self.pf_path[0]
        remaining_distance -= distance
        return next_position, remaining_distance

    def move_to_next_position(self, next_position, dx, dy, distance, remaining_distance):
        next_position = (
            next_position[0] + dx * remaining_distance / distance,
            next_position[1] + dy * remaining_distance / distance
        )
        remaining_distance = 0
        return next_position, remaining_distance

    def update_direction(self, dx, dy, distance):
        self.direction.update((round(dx / distance), round(dy / distance)))