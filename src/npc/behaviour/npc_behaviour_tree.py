from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

import pygame

from src.enums import FarmingTool, ItemToUse
from src.npc.behaviour.ai_behaviour_tree_base import (
    Context, Selector, Sequence, Condition, Action
)
from src.npc.bases.npc_base import NPCBase
from src.settings import SCALED_TILE_SIZE


@dataclass
class NPCBehaviourTreeContext(Context):
    npc: NPCBase


# TODO: NPCs can not harvest fully grown crops on their own yet
class NPCBehaviourTree:
    """
    Group of methods used for NPC behaviour.

    Attributes:
        tree:   Default NPC behaviour tree
    """
    tree = None

    @classmethod
    def init(cls):
        """
        Initialises the behaviour tree.
        """
        cls.tree = Selector([
            Sequence([
                Condition(cls.will_farm),
                Selector([
                    Sequence([
                        Condition(cls.will_create_new_farmland),
                        Action(cls.create_new_farmland)
                    ]),
                    Sequence([
                        Condition(cls.will_plant_tilled_farmland),
                        Action(cls.plant_random_seed)
                    ]),
                    Action(cls.water_farmland)
                ])
            ]),
            Action(cls.wander)
        ])

    @staticmethod
    def will_farm(context: NPCBehaviourTreeContext) -> bool:
        """
        1 in 3 chance to go farming instead of wandering around
        :return: 1/3 true | 2/3 false
        """
        return random.randint(0, 2) == 0

    @staticmethod
    def will_create_new_farmland(context: NPCBehaviourTreeContext) -> bool:
        """
        :return: True: untilled farmland available AND
        (all other farmland planted and watered OR 1/3), otherwise False
        """
        empty_farmland_available = 0
        unplanted_farmland_available = 0
        unwatered_farmland_available = 0

        for tile in context.npc.soil_layer.tiles.values():
            if tile.farmable and not tile.hoed:
                empty_farmland_available += 1
            if tile.hoed and not tile.planted:
                unplanted_farmland_available += 1
            if tile.planted and not tile.watered:
                unwatered_farmland_available += 1

        if empty_farmland_available <= 0:
            return False

        return (
                unplanted_farmland_available == 0
                and unwatered_farmland_available == 0
        ) or random.randint(0, 2) == 0

    @staticmethod
    def create_new_farmland(context: NPCBehaviourTreeContext) -> bool:
        """
        Finds a random untilled but farmable tile,
        makes the NPC walk to and till it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []
        for pos, tile in context.npc.soil_layer.tiles.items():
            if tile.farmable and not tile.hoed:
                possible_coordinates.append(pos)

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.HOE
            context.npc.tool_index = context.npc.current_tool.value - 1
            context.npc.frame_index = 0

        return NPCBehaviourTree.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    @staticmethod
    def will_plant_tilled_farmland(context: NPCBehaviourTreeContext) -> bool:
        """
        :return: True if unplanted farmland available AND
        (all other farmland watered OR 3/4), otherwise False
        """
        unplanted_farmland_available = 0
        unwatered_farmland_available = 0

        for tile in context.npc.soil_layer.tiles.values():
            if tile.hoed and not tile.planted:
                unplanted_farmland_available += 1
            if tile.planted and not tile.watered:
                unwatered_farmland_available += 1

        if unplanted_farmland_available <= 0:
            return False

        return unwatered_farmland_available == 0 or random.randint(0, 3) <= 2

    @staticmethod
    def plant_random_seed(context: NPCBehaviourTreeContext) -> bool:
        """
        Finds a random unplanted but tilled tile,
        makes the NPC walk to and plant a random seed on it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []

        for pos, tile in context.npc.soil_layer.tiles.items():
            if tile.hoed and not tile.planted:
                possible_coordinates.append(pos)

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.current_seed = FarmingTool.CORN_SEED
            context.npc.seed_index = (context.npc.current_seed.value
                                      - FarmingTool.get_first_seed_id().value)
            context.npc.use_tool(ItemToUse(1))

        return NPCBehaviourTree.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    @staticmethod
    def water_farmland(context: NPCBehaviourTreeContext) -> bool:
        """
        Finds a random unwatered but planted tile,
        makes the NPC walk to and water it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []

        for pos, tile in context.npc.soil_layer.tiles.items():
            if tile.planted and not tile.watered:
                possible_coordinates.append(pos)

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.WATERING_CAN
            context.npc.tool_index = context.npc.current_tool.value - 1
            context.npc.frame_index = 0

        return NPCBehaviourTree.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    @staticmethod
    def wander_to_interact(context: NPCBehaviourTreeContext,
                           target_position: tuple[int, int],
                           on_path_completion: Callable[[], None]):
        """
        :return: True if path has successfully been created, otherwise False
        """

        if context.npc.create_path_to_tile(target_position):
            if len(context.npc.pf_path) > 1:
                facing = (
                    context.npc.pf_path[-1][0] - context.npc.pf_path[-2][0],
                    context.npc.pf_path[-1][1] - context.npc.pf_path[-2][1]
                )
            else:
                facing = (
                    context.npc.pf_path[-1][0]
                    - context.npc.rect.centerx / SCALED_TILE_SIZE,
                    context.npc.pf_path[-1][1]
                    - context.npc.rect.centery / SCALED_TILE_SIZE
                )

            facing = (facing[0], 0)\
                if abs(facing[0]) > abs(facing[1])\
                else (0, facing[1])

            @context.npc.on_path_completion
            def inner():
                context.npc.direction.update(facing)
                context.npc.get_facing_direction()
                context.npc.direction.update((0, 0))

                on_path_completion()

            return True
        return False

    @staticmethod
    def wander(context: NPCBehaviourTreeContext) -> bool:
        """
        Makes the NPC wander to a random location in a 5 tile radius.
        :return: True if path has successfully been created, otherwise False
        """

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(
            context.npc.rect.centerx,
            context.npc.rect.centery
        ) / SCALED_TILE_SIZE

        # To limit the required computing power, NPCs currently only try to
        # navigate to 11 random points in their immediate vicinity
        # (5 tile radius)
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
            context.npc.abort_path()
            return False
        return True
