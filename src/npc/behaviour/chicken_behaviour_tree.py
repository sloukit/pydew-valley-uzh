from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.npc.bases.chicken_base import ChickenBase
from src.npc.behaviour.ai_behaviour_tree_base import (
    Action,
    Context,
    NodeWrapper,
    Selector,
)
from src.support import near_tiles


@dataclass
class ChickenIndividualContext(Context):
    chicken: ChickenBase


def wander(context: ChickenIndividualContext) -> bool:
    """
    Makes the Chicken wander to a random location in a 5 tile radius.
    :return: True if path has successfully been created, otherwise False
    """
    # current position on the tilemap
    tile_coord = context.chicken.get_tile_pos()

    for pos in near_tiles(tile_coord, 5, shuffle=True):
        if context.chicken.create_path_to_tile(pos):
            if len(context.chicken.pf_path) > 5:
                context.chicken.pf_path = context.chicken.pf_path[:5]
            return True

    return False


class ChickenBehaviourTree(NodeWrapper, Enum):
    Wander = Selector(Action(wander))
