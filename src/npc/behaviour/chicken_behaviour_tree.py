from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from src.npc.bases.chicken_base import ChickenBase
from src.npc.behaviour.ai_behaviour_tree_base import Context, Selector, Action
from src.settings import SCALED_TILE_SIZE


@dataclass
class ChickenBehaviourTreeContext(Context):
    chicken: ChickenBase


class ChickenBehaviourTree:
    """
    Group of methods used for Chicken behaviour.

    Attributes:
        tree:   Default behaviour tree
    """

    tree = None

    @classmethod
    def init(cls):
        """
        Initialises the behaviour tree.
        """
        cls.tree = Selector([Action(cls.wander)])

    @staticmethod
    def wander(context: ChickenBehaviourTreeContext) -> bool:
        """
        Makes the Chicken wander to a random location in a 5 tile radius.
        :return: True if path has successfully been created, otherwise False
        """
        # current position on the tilemap
        tile_coord = (
            pygame.Vector2(context.chicken.rect.centerx, context.chicken.rect.centery)
            / SCALED_TILE_SIZE
        )

        # To limit the required computing power, Chickens currently only try
        # to navigate to 11 random points in their immediate vicinity
        # (5 tile radius)
        avail_x_coords = list(
            range(
                max(0, int(tile_coord.x) - 5),
                min(int(tile_coord.x) + 5, context.chicken.pf_grid.width - 1) + 1,
            )
        )

        avail_y_coords = list(
            range(
                max(0, int(tile_coord.y) - 5),
                min(int(tile_coord.y) + 5, context.chicken.pf_grid.height - 1) + 1,
            )
        )

        for i in range(min(len(avail_x_coords), len(avail_y_coords))):
            pos = (random.choice(avail_x_coords), random.choice(avail_y_coords))
            avail_x_coords.remove(pos[0])
            avail_y_coords.remove(pos[1])

            if context.chicken.create_path_to_tile(pos):
                break
        else:
            context.chicken.abort_path()
            return False
        return True
