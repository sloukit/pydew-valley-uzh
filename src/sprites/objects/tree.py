import random

import pygame

from src import timer
from src.enums import InventoryResource, Layer
from src.map_objects import MapObjectType
from src.settings import APPLE_POS
from src.sprites.base import CollideableMapObject, Sprite
from src.sprites.drops import DropsManager
from src.support import generate_particle_surf


class Tree(CollideableMapObject):
    def __init__(
        self,
        pos: tuple[int, int],
        object_type: MapObjectType,
        groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
        name: str,
        fruit_surf: pygame.Surface | None,
        fruit_type: InventoryResource | None,
        stump_surf: pygame.Surface,
        drops_manager: DropsManager,
    ):
        super().__init__(
            pos,
            object_type,
            groups,
        )
        self.name = name
        self.health = 5
        self.alive = True
        self.drops_manager = drops_manager

        self.timer = timer.Timer(300, func=self.unhit)
        self.was_hit = False

        # surfs
        self.particle_surf = generate_particle_surf(self.image)
        self.stump_surf = stump_surf

        # fruits
        self.fruit_sprites = pygame.sprite.Group()
        self.fruit_surf = fruit_surf
        self.fruit_type = fruit_type

        self.create_fruit()

    def unhit(self):
        self.was_hit = False
        if self.health < 0:
            self.image = self.stump_surf
            if self.alive:
                self.rect = self.image.get_frect(midbottom=self.rect.midbottom)
                self.alive = False
                for fruit in self.fruit_sprites:
                    fruit.kill()
        elif self.health >= 0 and self.alive:
            self.image = self.surf
            for fruit in self.fruit_sprites:
                fruit.image = fruit.surf

    def create_fruit(self):
        if self.fruit_type:
            for pos in APPLE_POS["default"]:
                if random.randint(0, 10) < 6:
                    x = pos[0] + self.rect.left
                    y = pos[1] + self.rect.top
                    Sprite((x, y), self.fruit_surf, (self.fruit_sprites,), Layer.FRUIT)

    def update(self, dt):
        self.timer.update()

    def hit(self, entity):
        if self.was_hit:
            return
        self.was_hit = True
        self.health -= 1
        # remove an fruit
        # if len(self.fruit_sprites.sprites()) > 0:
        # random_fruit = random.choice(self.fruit_sprites.sprites())
        # random_fruit.kill()
        # entity.add_resource(self.fruit_type)
        if self.health < 0 and self.alive:
            # entity.add_resource(InventoryResource.WOOD, 5)
            pos = self.rect.center
            self.drops_manager.drop(pos, InventoryResource.WOOD, amount=5)
            if self.fruit_type:
                self.drops_manager.drop(
                    pos, self.fruit_type, amount=len(self.fruit_sprites)
                )

        self.image = generate_particle_surf(self.image)
        for fruit in self.fruit_sprites:
            fruit.image = generate_particle_surf(fruit.image)
        self.timer.activate()

    def draw(self, display_surface: pygame.Surface, rect: pygame.Rect, camera):
        super().draw(display_surface, rect, camera)
        for fruit in self.fruit_sprites:
            fruit.draw(display_surface, camera.apply(fruit), camera)
