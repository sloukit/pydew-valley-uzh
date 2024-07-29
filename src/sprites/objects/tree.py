import random

import pygame

from src import timer
from src.enums import InventoryResource, Layer
from src.map_objects import MapObjectType
from src.settings import APPLE_POS
from src.sprites.base import Sprite, CollideableMapObject
from src.support import generate_particle_surf


class Tree(CollideableMapObject):
    def __init__(
            self,
            pos: tuple[int, int],
            object_type: MapObjectType,
            groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
            name: str,
            apple_surf: pygame.Surface,
            stump_surf: pygame.Surface
    ):
        super().__init__(
            pos,
            object_type,
            groups,
        )
        self.name = name
        self.health = 5
        self.alive = True

        self.timer = timer.Timer(300, func=self.unhit)
        self.was_hit = False

        # surfs
        self.particle_surf = generate_particle_surf(self.image)
        self.stump_surf = stump_surf

        # apples
        self.apple_sprites = pygame.sprite.Group()
        self.apple_surf = apple_surf
        self.create_fruit()

    def unhit(self):
        self.was_hit = False
        if self.health < 0:
            self.image = self.stump_surf
            if self.alive:
                self.rect = self.image.get_frect(midbottom=self.rect.midbottom)
                self.alive = False
        elif self.health >= 0 and self.alive:
            self.image = self.surf

    def create_fruit(self):
        for pos in APPLE_POS['default']:
            if random.randint(0, 10) < 6:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                Sprite((x, y), self.apple_surf, (self.apple_sprites,),
                       Layer.FRUIT)

    def update(self, dt):
        self.timer.update()

    def hit(self, entity):
        if self.was_hit:
            return
        self.was_hit = True
        self.health -= 1
        # remove an apple
        if len(self.apple_sprites.sprites()) > 0:
            random_apple = random.choice(self.apple_sprites.sprites())
            random_apple.kill()
            entity.add_resource(InventoryResource.APPLE)
        if self.health < 0 and self.alive:
            entity.add_resource(InventoryResource.WOOD, 5)
        self.image = generate_particle_surf(self.image)
        self.timer.activate()

    def draw(self, display_surface, offset):
        super().draw(display_surface, offset)
        for apple in self.apple_sprites:
            apple.draw(display_surface, offset)
