
from __future__ import annotations
from enum import IntEnum
from typing import Callable
from src.sprites.entity import Entity
from src.enums import InventoryResource, FarmingTool, ItemToUse
from src.settings import SCALE_FACTOR
from pathfinding.core.grid import Grid as PF_Grid
from pathfinding.finder.a_star import AStarFinder as PF_AStarFinder
from src.npc.npc_behaviour import Selector, Sequence, Condition, Action
from src.settings import Coordinate, AniFrames

import pygame
import random



_NONSEED_INVENTORY_DEFAULT_AMOUNT = 20
_SEED_INVENTORY_DEFAULT_AMOUNT = 5
_INV_DEFAULT_AMOUNTS = (
    _NONSEED_INVENTORY_DEFAULT_AMOUNT,
    _SEED_INVENTORY_DEFAULT_AMOUNT
)


# <editor-fold desc="NPC">
# @dataclass
class NPCBehaviourContext:
    npc: "NPC"


# TODO: NPCs can not harvest fully grown crops on their own yet
class NPCBehaviourMethods:
    """
    Group of classes used for NPC behaviour.

    Attributes:
        behaviour:   Default NPC behaviour tree
    """
    behaviour = None

    @staticmethod
    def init():
        """
        Initialises the behaviour tree.
        """
        NPCBehaviourMethods.behaviour = Selector([
            Sequence([
                Condition(NPCBehaviourMethods.will_farm),
                Selector([
                    Sequence([
                        Condition(NPCBehaviourMethods.will_create_new_farmland),
                        Action(NPCBehaviourMethods.create_new_farmland)
                    ]),
                    Sequence([
                        Condition(NPCBehaviourMethods.will_plant_tilled_farmland),
                        Action(NPCBehaviourMethods.plant_random_seed)
                    ]),
                    Action(NPCBehaviourMethods.water_farmland)
                ])
            ]),
            Action(NPCBehaviourMethods.wander)
        ])

    @staticmethod
    def will_farm(context: NPCBehaviourContext) -> bool:
        """
        1 in 3 chance to go farming instead of wandering around
        :return: 1/3 true | 2/3 false
        """
        return random.randint(0, 2) is 0

    @staticmethod
    def will_create_new_farmland(context: NPCBehaviourContext) -> bool:
        """
        :return: True: untilled farmland available AND (all other farmland planted and watered OR 1/3), otherwise False
        """
        empty_farmland_available = 0
        unplanted_farmland_available = 0
        unwatered_farmland_available = 0
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "F" in entry:
                    if "X" not in entry:
                        empty_farmland_available += 1
                    else:
                        if "P" not in entry:
                            unplanted_farmland_available += 1
                        else:
                            if "W" not in entry:
                                unwatered_farmland_available += 1

        if empty_farmland_available <= 0:
            return False

        return (unplanted_farmland_available == 0 and unwatered_farmland_available == 0) or random.randint(0, 2) == 0

    # FIXME: When NPCs till tiles, the axe is displayed as the item used instead of the hoe
    @staticmethod
    def create_new_farmland(context: NPCBehaviourContext) -> bool:
        """
        Finds a random untilled but farmable tile, makes the NPC walk to and till it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "F" in entry and "X" not in entry:
                    possible_coordinates.append((x, y))

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.HOE
            context.npc.frame_index = 0

        return NPCBehaviourMethods.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    @staticmethod
    def will_plant_tilled_farmland(context: NPCBehaviourContext) -> bool:
        """
        :return: True if unplanted farmland available AND (all other farmland watered OR 3/4), otherwise False
        """
        unplanted_farmland_available = 0
        unwatered_farmland_available = 0
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "X" in entry:
                    if "P" not in entry:
                        unplanted_farmland_available += 1
                    else:
                        if "W" not in entry:
                            unwatered_farmland_available += 1

        if unplanted_farmland_available <= 0:
            return False

        return unwatered_farmland_available == 0 or random.randint(0, 3) <= 2

    @staticmethod
    def plant_random_seed(context: NPCBehaviourContext) -> bool:
        """
        Finds a random unplanted but tilled tile, makes the NPC walk to and plant a random seed on it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "X" in entry and "P" not in entry:
                    possible_coordinates.append((x, y))

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.current_seed = FarmingTool.CORN_SEED
            context.npc.use_tool(ItemToUse(1))

        return NPCBehaviourMethods.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    # FIXME: When NPCs water the plants, the hoe is displayed as the item used instead of the watering can
    # FIXME: When NPCs water the plants, the axe is displayed as the item used instead of the watering can
    @staticmethod
    def water_farmland(context: NPCBehaviourContext) -> bool:
        """
        Finds a random unwatered but planted tile, makes the NPC walk to and water it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []
        for y in range(len(context.npc.soil_layer.grid)):
            for x in range(len(context.npc.soil_layer.grid[y])):
                entry = context.npc.soil_layer.grid[y][x]
                if "P" in entry and "W" not in entry:
                    possible_coordinates.append((x, y))

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.WATERING_CAN
            context.npc.frame_index = 0

        return NPCBehaviourMethods.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    @staticmethod
    def wander_to_interact(context: NPCBehaviourContext,
                           target_position: tuple[int, int],
                           on_path_completion: Callable[[], None]):
        """
        :return: True if path has successfully been created, otherwise False
        """

        if context.npc.create_path_to_tile(target_position):
            if len(context.npc.pf_path) > 1:
                facing = (context.npc.pf_path[-1][0] - context.npc.pf_path[-2][0],
                          context.npc.pf_path[-1][1] - context.npc.pf_path[-2][1])
            else:
                facing = (context.npc.pf_path[-1][0] - context.npc.rect.centerx / 64,
                          context.npc.pf_path[-1][1] - context.npc.rect.centery / 64)

            facing = (facing[0], 0) if abs(facing[0]) > abs(facing[1]) else (0, facing[1])

            # Deleting the final step of the path leads to the NPC always standing in reach of the tile they want to
            #  interact with (cf. Entity.get_target_pos)
            context.npc.pf_path.pop(-1)

            def inner():
                context.npc.direction.update(facing)
                context.npc.get_facing_direction()
                context.npc.direction.update((0, 0))

                on_path_completion()

                context.npc.pf_on_path_completion = lambda: None

            context.npc.pf_on_path_completion = inner
            return True
        return False

    @staticmethod
    def wander(context: NPCBehaviourContext) -> bool:
        """
        Makes the NPC wander to a random location in a 5 tile radius.
        :return: True if path has successfully been created, otherwise False
        """
        tile_size = SCALE_FACTOR * 16

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(context.npc.rect.centerx, context.npc.rect.centery) / tile_size

        # To limit the required computing power, the NPC currently only tries to navigate to
        #  11 random points in its immediate vicinity (5 tile radius)
        avail_x_coords = list(range(
            max(0, int(tile_coord.x) - 5),
            min(int(tile_coord.x) + 5, context.npc.pf_grid.width - 1) + 1
        ))

        avail_y_coords = list(range(
            max(0, int(tile_coord.y) - 5),
            min(int(tile_coord.y) + 5, context.npc.pf_grid.height - 1) + 1
        ))

        for i in range(min(len(avail_x_coords), len(avail_y_coords))):
            pos = (
                random.choice(avail_x_coords),
                random.choice(avail_y_coords)
            )
            avail_x_coords.remove(pos[0])
            avail_y_coords.remove(pos[1])

            if context.npc.create_path_to_tile(pos):
                break
        else:
            context.npc.pf_state = NPCState.IDLE
            context.npc.direction.update((0, 0))
            context.npc.pf_state_duration = 1
            return False
        return True


# TODO: Refactor NPCState into Entity.state (maybe override Entity.get_state())
class NPCState(IntEnum):
    IDLE = 0
    MOVING = 1


class NPC(Entity):
    # Pathfinding
    pf_matrix: list[list[int]]
    """A representation of the in-game tilemap,
       where 1 stands for a walkable tile, and 0 stands for a non-walkable tile.
       Each list entry represents one row of the tilemap."""

    pf_grid: PF_Grid
    pf_finder: PF_AStarFinder
    pf_state: NPCState

    pf_path: list[tuple[int, int]]
    """The current path on which the NPC is moving.
       Each tile on which the NPC is moving is represented by its own coordinate tuple,
       while the first one in the list always being the NPCs current target position."""

    pf_on_path_completion: Callable[[], None]

    def __init__(
            self,
            pos: Coordinate,
            frames: dict[str, AniFrames],
            groups: tuple[pygame.sprite.Group],
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable,
            soil_layer,
            pf_matrix: list[list[int]],
            pf_grid: PF_Grid,
            pf_finder: PF_AStarFinder):

        self.soil_layer = soil_layer

        self.pf_matrix = pf_matrix
        self.pf_grid = pf_grid
        self.pf_finder = pf_finder
        self.pf_state = NPCState.IDLE
        self.pf_state_duration = 0
        self.pf_path = []
        self.pf_on_path_completion = lambda: None

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

    def create_path_to_tile(self, coord: tuple[int, int]) -> bool:
        if not self.pf_grid.walkable(coord[0], coord[1]):
            return False

        tile_size = SCALE_FACTOR * 16

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(self.rect.centerx, self.rect.centery) / tile_size

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
            self.pf_state = NPCState.IDLE
            self.direction.update((0, 0))
            self.pf_state_duration = 1
            return False

        return True

    def move(self, dt):
        tile_size = SCALE_FACTOR * 16

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(self.rect.centerx, self.rect.centery) / tile_size

        if self.pf_state == NPCState.IDLE:
            self.pf_state_duration -= dt

            if self.pf_state_duration <= 0:
                NPCBehaviourMethods.behaviour.run(NPCBehaviourContext(self))

        if self.pf_state == NPCState.MOVING:
            if not self.pf_path:
                # runs in case the path has been emptied in the meantime
                #  (e.g. NPCBehaviourMethods.wander_to_interact created a path to a tile adjacent to the NPC)
                self.pf_state = NPCState.IDLE
                self.direction.update((0, 0))
                self.pf_state_duration = random.randint(2, 5)

                self.pf_on_path_completion()
                return

            next_position = (tile_coord.x, tile_coord.y)

            # remaining distance the npc moves in the current frame
            remaining_distance = self.speed * dt / tile_size

            while remaining_distance:
                if next_position == self.pf_path[0]:
                    # the NPC reached its current target position
                    self.pf_path.pop(0)

                if not len(self.pf_path):
                    # the NPC has completed its path
                    self.pf_state = NPCState.IDLE
                    self.direction.update((0, 0))
                    self.pf_state_duration = random.randint(2, 5)

                    self.pf_on_path_completion()
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
                    #  e.g. if the distance vector was (-0.99, -0.01), the NPC would face upwards, although it moves
                    #  much more to the left than upwards, as the animation method favors vertical movement
                    #
                    # Maybe normalise the vector?
                    #  Currently, it is not necessary as the NPC is not moving diagonally yet,
                    #  unless it collides with another entity while it is in-between two coordinates
                    self.direction.update((round(dx / distance), round(dy / distance)))

            self.hitbox_rect.update((
                next_position[0] * tile_size - self.hitbox_rect.width / 2,
                self.hitbox_rect.top,
            ), self.hitbox_rect.size)
            colliding = self.collision('horizontal')

            self.hitbox_rect.update((
                self.hitbox_rect.left,
                next_position[1] * tile_size - self.hitbox_rect.height / 2
            ), self.hitbox_rect.size)
            colliding = colliding or self.collision('vertical')

            if colliding:
                self.pf_state = NPCState.IDLE
                self.direction.update((0, 0))
                self.pf_state_duration = 1

        self.rect.update((self.hitbox_rect.centerx - self.rect.width / 2,
                          self.hitbox_rect.centery - self.rect.height / 2), self.rect.size)
        self.plant_collide_rect.center = self.hitbox_rect.center
# </editor-fold>
