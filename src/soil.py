import pygame

from random import choice

from .support import tile_to_screen
from .sprites import Sprite, Plant
from .settings import LAYERS, TILE_SIZE, SCALE_FACTOR


class Tile(Sprite):
    def __init__(self, pos, group):
        surf = pygame.Surface((TILE_SIZE * SCALE_FACTOR, TILE_SIZE * SCALE_FACTOR))
        surf.fill("green")
        surf.set_colorkey("green")
        super().__init__(tile_to_screen(pos), surf, group, LAYERS["soil"])
        self.pos = pos
        self.hoed = False
        self.watered = False
        self.planted = False
        self.farmable = False
        self.plant = None


class SoilLayer:
    def __init__(self, all_sprites, tmx_map, frames, sounds):
        self.all_sprites = all_sprites
        self.level_frames = frames

        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        self.map = {}
        self.create_soil_map(tmx_map)
        self.sounds = sounds
        self.neighbor_directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

    def create_soil_map(self, tmx_map):
        farmable_layer = tmx_map.get_layer_by_name("Farmable")
        for x, y, _ in farmable_layer.tiles():
            tile = Tile((x, y), [self.all_sprites, self.soil_sprites])
            tile.farmable = True
            self.map[(x, y)] = tile

    def update_tile_image(self, tile, pos):
        for dx, dy in self.neighbor_directions:
            neighbor = self.map.get((pos[0] + dx, pos[1] + dy))
            if neighbor and neighbor.hoed:
                neighbor_pos = (pos[0] + dx, pos[1] + dy)
                neighbor_type = self.determine_tile_type(neighbor_pos)
                neighbor.image = self.level_frames["soil"][neighbor_type]

        tile_type = self.determine_tile_type(pos)
        tile.image = self.level_frames["soil"][tile_type]

    def hoe(self, pos):
        tile = self.map.get(pos)
        if tile and tile.farmable and not tile.hoed:
            tile.hoed = True
            self.sounds["hoe"].play()
            self.update_tile_image(tile, pos)

    def water(self, pos):
        tile = self.map.get(pos)
        if tile and tile.hoed and not tile.watered:
            tile.watered = True
            self.sounds["water"].play()

            water_frames = list(self.level_frames["soil water"].values())
            water_frame = choice(water_frames)
            Sprite(
                tile_to_screen(pos),
                water_frame,
                [self.all_sprites, self.water_sprites],
                LAYERS["soil water"],
            )

    def plant(self, pos, seed, inventory):
        tile = self.map.get(pos)
        seed_name = seed + " seed"
        seed_amount = inventory.get(seed_name)

        if tile and tile.hoed and not tile.planted and seed_amount > 0:
            tile.planted = True
            frames = self.level_frames[seed]
            groups = [self.all_sprites, self.plant_sprites]
            tile.plant = Plant(seed, groups, tile, frames, self.check_watered)
            inventory[seed_name] -= 1
            self.sounds["plant"].play()
            # self.sounds['cant plant'].play()

    def check_watered(self, pos):
        tile = self.map.get(pos)
        return tile.watered

    def determine_tile_type(self, pos):
        x, y = pos
        tile_above = self.map.get((x, y - 1))
        tile_below = self.map.get((x, y + 1))
        tile_right = self.map.get((x + 1, y))
        tile_left = self.map.get((x - 1, y))

        is_hoed_above = tile_above.hoed if tile_above else False
        is_hoed_below = tile_below.hoed if tile_below else False
        is_hoed_right = tile_right.hoed if tile_right else False
        is_hoed_left = tile_left.hoed if tile_left else False

        if all((is_hoed_above, is_hoed_right, is_hoed_below, is_hoed_left)):
            return "x"
        if is_hoed_left and not any((is_hoed_above, is_hoed_right, is_hoed_below)):
            return "r"
        if is_hoed_right and not any((is_hoed_above, is_hoed_left, is_hoed_below)):
            return "l"
        if is_hoed_right and is_hoed_left and not any((is_hoed_above, is_hoed_below)):
            return "lr"
        if is_hoed_above and not any((is_hoed_right, is_hoed_left, is_hoed_below)):
            return "b"
        if is_hoed_below and not any((is_hoed_right, is_hoed_left, is_hoed_above)):
            return "t"
        if is_hoed_below and is_hoed_above and not any((is_hoed_right, is_hoed_left)):
            return "tb"
        if is_hoed_left and is_hoed_below and not any((is_hoed_above, is_hoed_right)):
            return "tr"
        if is_hoed_right and is_hoed_below and not any((is_hoed_above, is_hoed_left)):
            return "tl"
        if is_hoed_left and is_hoed_above and not any((is_hoed_below, is_hoed_right)):
            return "br"
        if is_hoed_right and is_hoed_above and not any((is_hoed_below, is_hoed_left)):
            return "bl"
        if all((is_hoed_above, is_hoed_below, is_hoed_right)) and not is_hoed_left:
            return "tbr"
        if all((is_hoed_above, is_hoed_below, is_hoed_left)) and not is_hoed_right:
            return "tbl"
        if all((is_hoed_left, is_hoed_right, is_hoed_above)) and not is_hoed_below:
            return "lrb"
        if all((is_hoed_left, is_hoed_right, is_hoed_below)) and not is_hoed_above:
            return "lrt"
        return "o"
