
import random
import pygame
from src.sprites.base import CollideableSprite, Sprite
from src import timer
from src.settings import LAYERS, SCALE_FACTOR, APPLE_POS
from src.support import generate_particle_surf
from src.enums import InventoryResource


class Tree(CollideableSprite):
    def __init__(self, pos, surf, groups, name, apple_surf, stump_surf):
        super().__init__(
            pos,
            surf,
            groups,
            (30 * SCALE_FACTOR, 20 * SCALE_FACTOR),
        )
        self.name = name
        self.part_surf = generate_particle_surf(self.image)
        self.apple_surf = apple_surf
        self.stump_surf = stump_surf
        self.health = 5
        self.timer = timer.Timer(300, func=self.unhit)
        self.hitbox = None
        self.was_hit = False
        self.alive = True
        self.apple_sprites = pygame.sprite.Group()
        self.create_fruit()

    def unhit(self):
        self.was_hit = False
        if self.health < 0:
            self.image = self.stump_surf
            if self.alive:
                self.rect = self.image.get_frect(midbottom=self.rect.midbottom)
                self.hitbox = self.rect.inflate(-10, -self.rect.height * 0.6)
                self.alive = False
        elif self.health >= 0 and self.alive:
            self.image = self.surf

    def create_fruit(self):
        for pos in APPLE_POS['default']:
            if random.randint(0, 10) < 6:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                Sprite((x, y), self.apple_surf, (self.apple_sprites,
                       self.groups()[0]), LAYERS['fruit'])

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
