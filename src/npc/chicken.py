import pygame

from src.enums import Layer
from src.npc.bases.chicken_base import ChickenBase
from src.npc.behaviour.chicken_behaviour_tree import (
    ChickenBehaviourTree,
    ChickenBehaviourTreeContext
)
from src.npc.setup import AIData
from src.settings import Coordinate, AniFrames
from src.sprites.setup import EntityAsset


class Chicken(ChickenBase):
    def __init__(
            self,
            pos: Coordinate,
            assets: EntityAsset,
            groups: tuple[pygame.sprite.Group, ...],
            collision_sprites: pygame.sprite.Group
    ):
        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_sprites=collision_sprites,

            pf_matrix=AIData.Matrix,
            pf_grid=AIData.Grid,
            pf_finder=AIData.ChickenPathFinder,

            z=Layer.MAIN
        )

    def exit_idle(self):
        ChickenBehaviourTree.tree.run(ChickenBehaviourTreeContext(self))
