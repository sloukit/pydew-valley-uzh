from dataclasses import dataclass

from src.npc.bases.cow_base import CowBase
from src.npc.behaviour.ai_behaviour_tree_base import (
    Context,
    Selector,
    Sequence,
    Condition,
    Action,
)
from src.settings import SCALED_TILE_SIZE
from src.sprites.character import Character


@dataclass
class CowFleeBehaviourTreeContext(Context):
    cow: CowBase
    player: Character


class CowFleeBehaviourTree:
    """
    Group of methods used for Cow flee behaviour.
    Contrary to other trees, this behaviour tree will be run every tick.

    Attributes:
        tree:   Default behaviour tree
    """

    tree = None

    @classmethod
    def init(cls):
        """
        Initialises the behaviour tree.
        """
        cls.tree = Selector(
            [Sequence([Condition(cls.player_nearby), Action(cls.flee_from_player)])]
        )

    @staticmethod
    def player_nearby(context: CowFleeBehaviourTreeContext):
        distance_threshold = 2.5 * SCALED_TILE_SIZE
        current_distance = (
            (context.player.rect.center[0] - context.cow.rect.center[0]) ** 2
            + (context.player.rect.center[1] - context.cow.rect.center[1]) ** 2
        ) ** 0.5
        return current_distance < distance_threshold

    @staticmethod
    def flee_from_player(context: CowFleeBehaviourTreeContext) -> bool:
        return context.cow.flee_from_pos(
            (
                context.player.rect.centerx / SCALED_TILE_SIZE,
                context.player.rect.centery / SCALED_TILE_SIZE,
            )
        )
