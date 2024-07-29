import pygame
from random import choice

from pytmx import TiledMap

from src.enums import SeedType, Layer
from src.support import tile_to_screen
from src.sprites.base import Sprite
from src.sprites.objects.plant import Plant
from src.settings import TILE_SIZE, SCALE_FACTOR, SoundDict


class Tile(Sprite):
    pos: tuple[int, int]

    farmable: bool
    hoed: bool
    planted: bool
    watered: bool

    plant: Plant | None

    def __init__(self, pos: tuple[int, int], group: tuple[pygame.sprite.Group, ...]):
        size = TILE_SIZE * SCALE_FACTOR
        surf = pygame.Surface((size, size))
        surf.fill("green")
        surf.set_colorkey("green")
        super().__init__(tile_to_screen(pos), surf, group, Layer.SOIL)

        self.pos = pos
        self.hoed = False
        self.watered = False
        self.planted = False
        self.farmable = False
        self.plant = None


class SoilLayer:
    all_sprites: pygame.sprite.Group
    level_frames: dict

    soil_sprites: pygame.sprite.Group
    water_sprites: pygame.sprite.Group
    plant_sprites: pygame.sprite.Group

    tiles: dict[tuple[int, int], Tile]
    sounds: SoundDict
    neighbor_directions: list[tuple[int, int]]

    def __init__(self, all_sprites: pygame.sprite.Group, tmx_map: TiledMap, frames: dict, sounds: SoundDict):
        self.all_sprites = all_sprites
        self.level_frames = frames

        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        self.tiles = {}
        self.create_soil_tiles(tmx_map)
        self.sounds = sounds
        self.neighbor_directions = [
            (0, -1), (1, -1), (1, 0), (1, 1),
            (0, 1), (-1, 1), (-1, 0), (-1, -1)
        ]

    def create_soil_tiles(self, tmx_map):
        try:
            farmable_layer = tmx_map.get_layer_by_name("Farmable")
        except ValueError:
            return
        for x, y, _ in farmable_layer.tiles():
            tile = Tile((x, y), (self.all_sprites, self.soil_sprites))
            tile.farmable = True
            self.tiles[(x, y)] = tile

    def update_tile_image(self, tile, pos):
        for dx, dy in self.neighbor_directions:
            neighbor = self.tiles.get((pos[0] + dx, pos[1] + dy))
            if neighbor and neighbor.hoed:
                neighbor_pos = (pos[0] + dx, pos[1] + dy)
                neighbor_type = self.determine_tile_type(neighbor_pos)
                neighbor.image = self.level_frames["soil"][neighbor_type]

        tile_type = self.determine_tile_type(pos)
        tile.image = self.level_frames["soil"][tile_type]

    def hoe(self, pos):
        tile = self.tiles.get(pos)
        if tile and tile.farmable and not tile.hoed:
            tile.hoed = True
            self.sounds["hoe"].play()
            self.update_tile_image(tile, pos)

    def water(self, pos, play_sound: bool = True):
        tile = self.tiles.get(pos)
        if tile and tile.hoed and not tile.watered:
            tile.watered = True
            if play_sound:
                self.sounds["water"].play()

            water_frames = list(self.level_frames["soil water"].values())
            water_frame = choice(water_frames)
            Sprite(
                tile_to_screen(pos),
                water_frame,
                (self.all_sprites, self.water_sprites),
                Layer.SOIL_WATER,
            )

    def plant(self, pos, seed, inventory):
        tile = self.tiles.get(pos)
        seed_amount = inventory.get(seed)
        seed_type = SeedType.from_farming_tool(seed)

        if tile and tile.hoed and not tile.planted and seed_amount > 0:
            tile.planted = True
            seed_name = seed_type.as_plant_name()
            frames = self.level_frames[seed_name]
            groups = (self.all_sprites, self.plant_sprites)
            tile.plant = Plant(seed_type, groups, tile, frames)
            inventory[seed] -= 1
            self.sounds["plant"].play()
            # self.sounds['cant plant'].play()

    def determine_tile_type(self, pos):
        x, y = pos
        tile_above = self.tiles.get((x, y - 1))
        tile_below = self.tiles.get((x, y + 1))
        tile_right = self.tiles.get((x + 1, y))
        tile_left = self.tiles.get((x - 1, y))

        hoed_above = tile_above.hoed if tile_above else False
        hoed_below = tile_below.hoed if tile_below else False
        hoed_right = tile_right.hoed if tile_right else False
        hoed_left = tile_left.hoed if tile_left else False

        if all((hoed_above, hoed_right, hoed_below, hoed_left)):
            return "x"
        if hoed_left and not any((hoed_above, hoed_right, hoed_below)):
            return "r"
        if hoed_right and not any((hoed_above, hoed_left, hoed_below)):
            return "l"
        if hoed_right and hoed_left and not any((hoed_above, hoed_below)):
            return "lr"
        if hoed_above and not any((hoed_right, hoed_left, hoed_below)):
            return "b"
        if hoed_below and not any((hoed_right, hoed_left, hoed_above)):
            return "t"
        if hoed_below and hoed_above and not any((hoed_right, hoed_left)):
            return "tb"
        if hoed_left and hoed_below and not any((hoed_above, hoed_right)):
            return "tr"
        if hoed_right and hoed_below and not any((hoed_above, hoed_left)):
            return "tl"
        if hoed_left and hoed_above and not any((hoed_below, hoed_right)):
            return "br"
        if hoed_right and hoed_above and not any((hoed_below, hoed_left)):
            return "bl"
        if all((hoed_above, hoed_below, hoed_right)) and not hoed_left:
            return "tbr"
        if all((hoed_above, hoed_below, hoed_left)) and not hoed_right:
            return "tbl"
        if all((hoed_left, hoed_right, hoed_above)) and not hoed_below:
            return "lrb"
        if all((hoed_left, hoed_right, hoed_below)) and not hoed_above:
            return "lrt"
        return "o"
