from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pathfinding.core.grid import Grid

from src.npc.bases.chicken_base import ChickenBase
from src.npc.behaviour.ai_behaviour_tree_base import (
    Action,
    Context,
    NodeWrapper,
    Selector,
)
from src.npc.utils import pf_wander


@dataclass
class ChickenIndividualContext(Context):
    chicken: ChickenBase
    range_grid: Grid = None


def wander(context: ChickenIndividualContext) -> bool:
    return pf_wander(context.chicken, pf_grid=ChickenIndividualContext.range_grid)


class ChickenBehaviourTree(NodeWrapper, Enum):
    Wander = Selector(Action(wander))
