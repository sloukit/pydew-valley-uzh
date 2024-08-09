from enum import Enum

from pathfinding.core.grid import Grid

from src.npc.behaviour.ai_behaviour import AIBehaviour
from src.npc.behaviour.ai_behaviour_tree_base import (
    Action,
    Condition,
    NodeWrapper,
    Selector,
    Sequence,
)
from src.npc.behaviour.cow_behaviour_tree import CowIndividualContext, player_nearby
from src.npc.setup import AIData
from src.settings import SCALED_TILE_SIZE
from src.support import near_tiles


class CowHerdingContext:
    barn_grid: Grid = None
    default_grid: Grid = None
    range_grid: Grid = None


def wander(ai: AIBehaviour, radius: int = 5, pf_grid: Grid = None) -> bool:
    """
    Makes the Entity wander to a random location in the given radius.
    :param ai: Entity that should wander
    :param radius: (Optional) radius in which the Entity should wander
    :param pf_grid: (Optional) pathfinding grid to use. Defaults to self.pf_grid
    :return: True if path has successfully been created, otherwise False
    """
    # current position on the tilemap
    tile_coord = ai.get_tile_pos()

    for pos in near_tiles(tile_coord, radius, shuffle=True):
        if ai.create_path_to_tile(pos, pf_grid=pf_grid):
            if len(ai.pf_path) > radius:
                ai.pf_path = ai.pf_path[:radius]
            return True

    return False


def wander_barn(context: CowIndividualContext) -> bool:
    return wander(context.cow, pf_grid=CowHerdingContext.barn_grid)


def wander_range(context: CowIndividualContext) -> bool:
    return wander(context.cow, pf_grid=CowHerdingContext.range_grid)


def flee_from_player(context: CowIndividualContext) -> bool:
    return context.cow.flee_from_pos(
        (
            AIData.player.rect.centerx / SCALED_TILE_SIZE,
            AIData.player.rect.centery / SCALED_TILE_SIZE,
        ),
        pf_grid=CowHerdingContext.default_grid,
    )


class CowHerdingBehaviourTree(NodeWrapper, Enum):
    WanderBarn = Selector(Action(wander_barn))
    WanderRange = Selector(Action(wander_range))
    Flee = Selector(Sequence(Condition(player_nearby), Action(flee_from_player)))
