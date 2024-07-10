import pygame

from random import choice

from .support import screen_to_tile, tile_to_screen
from .sprites import Sprite, Plant
from .settings import LAYERS, TILE_SIZE
from pygame.math import Vector2 as vector


# TODO : REFACTOR THIS CLASS


class Tile(Sprite):
    def __init__(self, pos, frames, group):
        surf = frames['soil']['o']
        super().__init__(pos, surf, group, LAYERS['soil'])
        self.hoed = False
        self.watered = False
        self.planted = False
        self.farmable = False
        self.plant = None
        self.neighbors = 'X'


class SoilLayer:
    def __init__(self, all_sprites, collision_sprites, tmx_map, level_frames, sounds):
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.level_frames = level_frames
        
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()
        
        self.map = {}
        self.create_soil_map(tmx_map)
        self.sounds = sounds
        
        self.NEIGHBOR_DIRECTIONS = {
            'A': (0, -1),
            'B': (1, -1),
            'C': (1, 0),
            'D': (1, 1),
            'E': (0, 1),
            'F': (-1, 1),
            'G': (-1, 0),
            'H': (-1, -1)
        }
    
    def create_soil_map(self, tmx_map):
        farmable_layer = tmx_map.get_layer_by_name('Farmable')
        for x, y, _ in farmable_layer.tiles():
            pos = tile_to_screen((x, y))
            tile = Tile(pos, self.level_frames, [self.all_sprites, self.soil_sprites])
            tile.farmable = True
            self.map[(x, y)] = tile
    
    def update_tile_cluster(self, pos, tile):
        neighbors = ""
        tile_pos = vector(pos)
        for direction, (dx, dy) in self.NEIGHBOR_DIRECTIONS.items():
            neighbor_pos = (tile_pos.x + dx, tile_pos.y + dy)
            neighbor_tile = self.map.get(neighbor_pos)
            if neighbor_tile and neighbor_tile.hoed:
                neighbors += direction
        tile.neighbors = neighbors if neighbors else 'X'
    
    def update_tile_image(self, tile):
        tile.image = self.level_frames['soil']['o']


    def hoe(self, pos):
        tile = self.map.get(pos)
        if tile.farmable and not tile.hoed:
            tile.hoed = True
            self.sounds['hoe'].play()
            self.update_tile_cluster(pos, tile)
            self.update_tile_image(tile)

    def water(self, pos):
        tile = self.map.get(pos)
        if tile.hoed and not tile.watered:
            tile.watered = True
            self.sounds['water'].play()

            water_frames = list(self.level_frames["soil water"].values())
            water_frame = choice(water_frames)
            Sprite(tile_to_screen(pos), water_frame, [self.all_sprites, self.water_sprites], LAYERS["soil water"])
        
    def plant(self, pos, seed, inventory):
        tile = self.map.get(pos)
        seed_name = seed + ' seed'
        
        if tile.hoed and not tile.planted and inventory[seed_name] > 0:
            tile.planted = True
            frames = self.level_frames[seed]
            tile.plant = Plant(seed, [self.all_sprites, self.plant_sprites], tile, frames, self.check_watered)   # TODO: rm check_watered and tile
            inventory[seed_name] -= 1
            self.sounds['plant'].play()
            # self.sounds['cant plant'].play()
    
    def check_watered(self, pos):
        tile = self.map.get(pos)
        return tile.watered




