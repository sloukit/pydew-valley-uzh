from __future__ import annotations

import random
import pygame

from dataclasses import dataclass
from typing import Callable

from src.enums import FarmingTool, ItemToUse
from src.npc.behaviour_base import Context, Selector, Sequence
from src.npc.behaviour_base import Condition, Action
from src.npc.npc_base import NPCBase
from src.settings import SCALED_TILE_SIZE


@dataclass
class NPCBehaviourContext(Context):
    npc: NPCBase


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
        create_farmland_sequence = Sequence([
            Condition(NPCBehaviourMethods.will_create_new_farmland),
            Action(NPCBehaviourMethods.create_new_farmland)
        ])

        plant_seed_sequence = Sequence([
            Condition(NPCBehaviourMethods.will_plant_tilled_farmland),
            Action(NPCBehaviourMethods.plant_random_seed)
        ])

        farm_selector = Selector([
            create_farmland_sequence,
            plant_seed_sequence,
            Action(NPCBehaviourMethods.water_farmland)
        ])

        # Define the main behaviour tree
        behaviour_tree = Selector([
            Sequence([
                Condition(NPCBehaviourMethods.will_farm),
                farm_selector
            ]),
            Action(NPCBehaviourMethods.wander)
        ])

        NPCBehaviourMethods.behaviour = behaviour_tree

    @staticmethod
    def will_farm(context: NPCBehaviourContext) -> bool:
        """
        1 in 3 chance to go farming instead of wandering around
        :return: 1/3 true | 2/3 false
        """
        return random.randint(0, 2) == 0

    @staticmethod
    def will_create_new_farmland(ctx: NPCBehaviourContext) -> bool:
        """
        :return: True if there is tillable farmland available and
        (all other farmland is planted and watered OR random chance),
        otherwise False
        """
        empty_farmland = 0
        unplanted_farmland = 0
        unwatered_farmland = 0

        for tile in ctx.npc.soil_layer.map.values():
            if tile.farmable and not tile.hoed:
                empty_farmland += 1
            if tile.hoed and not tile.planted:
                unplanted_farmland += 1
            if tile.planted and not tile.watered:
                unwatered_farmland += 1

        if empty_farmland <= 0:
            return False

        all_farmed = (unplanted_farmland == 0 and unwatered_farmland == 0)
        return all_farmed or random.randint(0, 2) == 0

    @staticmethod
    def create_new_farmland(context: NPCBehaviourContext) -> bool:
        """
        Finds a random untilled but farmable tile,
        makes the NPC walk to and till it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []
        for pos, tile in context.npc.soil_layer.map.items():
            if tile.farmable and not tile.hoed:
                possible_coordinates.append(pos)

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.HOE
            context.npc.tool_index = context.npc.current_tool.value - 1
            context.npc.frame_index = 0

        return NPCBehaviourMethods.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    @staticmethod
    def will_plant_tilled_farmland(context: NPCBehaviourContext) -> bool:
        """
        :return: True if unplanted farmland available AND
        (all other farmland watered OR 3/4), otherwise False
        """
        unplanted_farmland_available = 0
        unwatered_farmland_available = 0

        for tile in context.npc.soil_layer.map.values():
            if tile.hoed and not tile.planted:
                unplanted_farmland_available += 1
            if tile.planted and not tile.watered:
                unwatered_farmland_available += 1

        if unplanted_farmland_available <= 0:
            return False

        return unwatered_farmland_available == 0 or random.randint(0, 3) <= 2

    @staticmethod
    def plant_random_seed(context: NPCBehaviourContext) -> bool:
        """
        Finds a random unplanted but tilled tile, makes the NPC walk to
        and plant a random seed on it.
        :return: True if path has successfully been created, otherwise False
        """
        # Collect possible positions for planting
        coords = [
            pos for pos, tile in context.npc.soil_layer.map.items()
            if tile.hoed and not tile.planted
        ]

        if not coords:
            return False

        def on_path_completion():
            context.npc.current_seed = FarmingTool.CORN_SEED
            context.npc.seed_index = (context.npc.current_seed.value -
                                      FarmingTool.get_first_seed_id().value)
            context.npc.use_tool(ItemToUse(1))

        return NPCBehaviourMethods.wander_to_interact(
            context, random.choice(coords), on_path_completion
        )

    @staticmethod
    def water_farmland(context: NPCBehaviourContext) -> bool:
        """
        Finds a random unwatered but planted tile, makes the NPC walk to
        and water it.
        :return: True if path has successfully been created, otherwise False
        """
        possible_coordinates = []
        for pos, tile in context.npc.soil_layer.map.items():
            if tile.planted and not tile.watered:
                possible_coordinates.append(pos)

        if not possible_coordinates:
            return False

        def on_path_completion():
            context.npc.tool_active = True
            context.npc.current_tool = FarmingTool.WATERING_CAN
            context.npc.tool_index = context.npc.current_tool.value - 1
            context.npc.frame_index = 0

        return NPCBehaviourMethods.wander_to_interact(
            context, random.choice(possible_coordinates), on_path_completion
        )

    @staticmethod
    def wander_to_interact(ctx: NPCBehaviourContext,
                           target_pos: tuple[int, int],
                           on_complete: Callable[[], None]) -> bool:
        """
        :return: True if path has been successfully created, otherwise False
        """
        if ctx.npc.create_path_to_tile(target_pos):
            path = ctx.npc.pf_path
            if len(path) > 1:
                dx, dy = path[-1][0] - path[-2][0], path[-1][1] - path[-2][1]
            else:
                dx, dy = path[-1][0] - ctx.npc.rect.centerx / 64, \
                        path[-1][1] - ctx.npc.rect.centery / 64

            facing = (dx, 0) if abs(dx) > abs(dy) else (0, dy)

            # Remove the final step to ensure the NPC
            # stands in reach of the target tile
            path.pop()

            def on_path_finish():
                ctx.npc.direction.update(facing)
                ctx.npc.get_facing_direction()
                ctx.npc.direction.update((0, 0))
                on_complete()

            ctx.npc.on_path_completion = on_path_finish
            return True

        return False

    def wander(context: NPCBehaviourContext) -> bool:
        """
        Makes the NPC wander to a random location in a 5 tile radius.
        :return: True if path has successfully been created, otherwise False
        """

        # current NPC position on the tilemap
        tile_coord = pygame.Vector2(context.npc.rect.center) / SCALED_TILE_SIZE

        # To limit the required computing power, the NPC currently only tries
        # to navigate to 11 random points
        # in its immediate vicinity (5 tile radius)

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
