import pygame

from src.enums import Layer
from src.npc.bases.chicken_base import ChickenBase
from src.npc.behaviour.chicken_behaviour_tree import ChickenIndividualContext
from src.settings import Coordinate
from src.sprites.chunk_system.collision_chunks import CollisionManager
from src.sprites.setup import EntityAsset


class Chicken(ChickenBase):
    def __init__(
        self,
        pos: Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_manager: CollisionManager,
    ):
        super().__init__(
            pos=pos,
            assets=assets,
            groups=groups,
            collision_manager=collision_manager,
            behaviour_tree_context=ChickenIndividualContext(self),
            z=Layer.MAIN,
        )
