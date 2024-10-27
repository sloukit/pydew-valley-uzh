import random

import pygame

from src import timer
from src.enums import InventoryResource
from src.map_objects import MapObjectType
from src.settings import APPLE_POS
from src.sprites.base import CollideableMapObject, Sprite
from src.support import generate_particle_surf


class BerryBush(CollideableMapObject):
    def __init__(
        self,
        pos: tuple[int, int],
        object_type: MapObjectType,
        groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
        name: str,
        fruit_surf: pygame.Surface | None,
        fruit_type: InventoryResource | None,
    ):
        super().__init__(
            pos,
            object_type,
            groups,
        )
        self.name = name

        self.timer = timer.Timer(300, func=self.unhit)
        self.was_hit = False

        # surfs
        self.particle_surf = generate_particle_surf(self.image)

        # fruits
        self.fruit_sprites = pygame.sprite.Group()
        self.fruit_surf = fruit_surf
        self.fruit_type = fruit_type

        self.create_fruit()

    def unhit(self):
        self.was_hit = False
        self.image = self.surf
        for fruit in self.fruit_sprites:
            fruit.image = fruit.surf

    def create_fruit(self):
        if self.fruit_type:
            for pos in APPLE_POS["bush"]:
                if random.randint(0, 10) < 4:
                    x = pos[0] + self.rect.left
                    y = pos[1] + self.rect.top
                    Sprite((x, y), self.fruit_surf, ()).add(self.fruit_sprites)

    def update(self, dt):
        self.timer.update()

    def hit(self, entity):
        if self.was_hit:
            return
        self.was_hit = True
        # remove a fruit
        if len(self.fruit_sprites.sprites()) > 0:
            random_fruit = random.choice(self.fruit_sprites.sprites())
            random_fruit.kill()
            entity.add_resource(self.fruit_type)

            self.image = generate_particle_surf(self.image)
            for fruit in self.fruit_sprites:
                fruit.image = generate_particle_surf(fruit.image)
        self.timer.activate()

    def draw(self, display_surface: pygame.Surface, rect: pygame.Rect, camera):
        super().draw(display_surface, rect, camera)
        for fruit in self.fruit_sprites:
            fruit.draw(display_surface, camera.apply(fruit), camera)
