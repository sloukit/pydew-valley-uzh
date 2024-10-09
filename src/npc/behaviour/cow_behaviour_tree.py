from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pathfinding.core.grid import Grid

from src.npc.bases.cow_base import CowBase
from src.npc.behaviour.ai_behaviour_tree_base import (
    Action,
    Condition,
    Context,
    NodeWrapper,
    Selector,
    Sequence,
)
from src.npc.setup import AIData
from src.npc.utils import pf_wander
from src.settings import SCALED_TILE_SIZE


@dataclass
class CowIndividualContext(Context):
    cow: CowBase
    range_grid: Grid = None


def wander(context: CowIndividualContext) -> bool:
    return pf_wander(context.cow, pf_grid=CowIndividualContext.range_grid)


# region flee behaviour
def player_nearby(context: CowIndividualContext) -> bool:
    distance_threshold = 2.5 * SCALED_TILE_SIZE
    current_distance = (
        (AIData.player.rect.center[0] - context.cow.rect.center[0]) ** 2
        + (AIData.player.rect.center[1] - context.cow.rect.center[1]) ** 2
    ) ** 0.5
    return current_distance < distance_threshold


def flee_from_player(context: CowIndividualContext) -> bool:
    return context.cow.flee_from_pos(
        (
            AIData.player.rect.centerx / SCALED_TILE_SIZE,
            AIData.player.rect.centery / SCALED_TILE_SIZE,
        )
    )


# endregion


class CowConditionalBehaviourTree(NodeWrapper, Enum):
    Wander = Selector(Action(wander))


class CowContinuousBehaviourTree(NodeWrapper, Enum):
    Flee = Selector(Sequence(Condition(player_nearby), Action(flee_from_player)))
