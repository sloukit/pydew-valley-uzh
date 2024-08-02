import pygame

from src.enums import Layer
from src.npc.bases.chicken_base import ChickenBase
from src.npc.behaviour.chicken_behaviour_tree import (
    ChickenBehaviourTree,
    ChickenBehaviourTreeContext,
)
from src.settings import Coordinate
from src.sprites.setup import EntityAsset


class Chicken(ChickenBase):
    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_sprites: pygame.sprite.Group,
    ):
        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,
            z=Layer.MAIN,
        )

    def exit_idle(self):
        ChickenBehaviourTree.tree.run(ChickenBehaviourTreeContext(self))
