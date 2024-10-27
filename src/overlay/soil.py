from collections.abc import Callable
from random import choice

import pygame
from pytmx import TiledTileLayer

from src.enums import FarmingTool, InventoryResource, Layer, SeedType, StudyGroup
from src.savefile.tile_info import TileInfo
from src.settings import SCALED_TILE_SIZE, Coordinate
from src.sprites.base import Sprite
from src.sprites.chunk_system.render_chunks import AllSprites
from src.sprites.entities.character import Character
from src.sprites.objects.plant import Plant
from src.support import tile_to_screen


class Tile(Sprite):
    pos: tuple[int, int]

    farmable: bool
    hoed: bool
    plant: Plant | None
    planted: bool
    watered: bool

    pf_weight: float

    def __init__(self, pos: tuple[int, int], group: tuple[pygame.sprite.Group, ...]):
        self._callback = None

        surf = pygame.Surface((SCALED_TILE_SIZE, SCALED_TILE_SIZE), pygame.SRCALPHA)

        super().__init__(tile_to_screen(pos), surf, group, Layer.SOIL)

        self.pos = pos

        self._on_farmable_funcs = []
        self._on_hoed_funcs = []
        self._on_plant_funcs = []
        self._on_plant_harvestable_funcs = []
        self._on_watered_funcs = []

        self.farmable = False
        self.hoed = False
        self.plant = None
        self.watered = False
        self.pf_weight = 0

    @property
    def planted(self):
        return self.plant is not None

    @property
    def farmable(self):
        return self._farmable

    @farmable.setter
    def farmable(self, value: bool):
        for func in self._on_farmable_funcs:
            func(value)

        self._farmable = value

    def on_farmable(self, func):
        self._on_farmable_funcs.append(func)

    @property
    def hoed(self):
        return self._hoed

    @hoed.setter
    def hoed(self, value: bool):
        for func in self._on_hoed_funcs:
            func(value)

        self._hoed = value

    def on_hoed(self, func):
        self._on_hoed_funcs.append(func)

    @property
    def plant(self):
        return self._plant

    @plant.setter
    def plant(self, value: Plant | None):
        for func in self._on_plant_funcs:
            func(value)

        try:
            self.plant.harvestable = False
            self.plant.kill()
        except (AttributeError, TypeError):
            pass

        self._plant = value

        if self.plant:

            @self.plant.on_harvestable
            def on_harvestable(inner_value: bool):
                for func_ in self._on_plant_harvestable_funcs:
                    func_(inner_value)

    def on_plant(self, func):
        self._on_plant_funcs.append(func)

    def on_plant_harvestable(self, func):
        self._on_plant_harvestable_funcs.append(func)

    @property
    def watered(self):
        return self._watered

    @watered.setter
    def watered(self, value: bool):
        for func in self._on_watered_funcs:
            func(value)

        self._watered = value

    def on_watered(self, func):
        self._on_watered_funcs.append(func)


class SoilArea:
    all_sprites: pygame.sprite.Group
    level_frames: dict

    soil_sprites: pygame.sprite.Group
    water_sprites: pygame.sprite.Group
    plant_sprites: pygame.sprite.Group

    tiles: dict[tuple[int, int], Tile]
    neighbor_directions: list[tuple[int, int]]

    raining: bool

    def __init__(self, all_sprites: pygame.sprite.Group, frames: dict):
        self.all_sprites = all_sprites
        self.level_frames = frames

        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        self.tiles = {}

        self._untilled_tiles = set(self.tiles)
        self._unplanted_tiles = set()
        self._unwatered_tiles = set()
        self._harvestable_tiles = set()
        self.planted_types = {i: 0 for i in SeedType}

        self.neighbor_directions = [
            (0, -1),
            (1, -1),
            (1, 0),
            (1, 1),
            (0, 1),
            (-1, 1),
            (-1, 0),
            (-1, -1),
        ]

        self.raining = False

    @property
    def raining(self) -> bool:
        return self._raining

    @raining.setter
    def raining(self, value: bool):
        self._raining = value
        if self.raining:
            self.water_all()

    @property
    def untilled_tiles(self):
        return self._untilled_tiles

    @property
    def unplanted_tiles(self):
        return self._unplanted_tiles

    @property
    def unwatered_tiles(self):
        return self._unwatered_tiles

    @property
    def harvestable_tiles(self):
        return self._harvestable_tiles

    def _setup_tile(self, tile: Tile):
        @tile.on_farmable
        def on_farmable(value: bool):
            if value:
                if not tile.hoed:
                    self._untilled_tiles.add(tile.pos)
            else:
                self._untilled_tiles.discard(tile.pos)

        @tile.on_hoed
        def on_hoed(value: bool):
            if value:
                self._untilled_tiles.discard(tile.pos)
                if not tile.planted:
                    self._unplanted_tiles.add(tile.pos)
            else:
                self._unplanted_tiles.discard(tile.pos)
                if tile.farmable:
                    self.untilled_tiles.add(tile.pos)

        @tile.on_plant
        def on_plant(value: Plant | None):
            if value:
                self.planted_types[value.seed_type] += 1

                self._unplanted_tiles.discard(tile.pos)
                if not tile.watered:
                    self._unwatered_tiles.add(tile.pos)
            else:
                if tile.plant:
                    self.planted_types[tile.plant.seed_type] -= 1

                self._unwatered_tiles.discard(tile.pos)
                if tile.hoed:
                    self._unplanted_tiles.add(tile.pos)

        @tile.on_plant_harvestable
        def on_plant_harvestable(value: bool):
            if value:
                self._harvestable_tiles.add(tile.pos)
            else:
                self._harvestable_tiles.discard(tile.pos)

        @tile.on_watered
        def on_watered(value: bool):
            if value:
                self._unwatered_tiles.discard(tile.pos)
            else:
                if tile.planted:
                    self._unwatered_tiles.add(tile.pos)

    # def reset(self):
    #     self.tiles = {}
    #     self.soil_sprites.empty()
    #     self.water_sprites.empty()
    #     self.plant_sprites.empty()

    def create_soil_tiles(
        self, layer: TiledTileLayer, previous_soil_data: dict | None = None
    ):
        if self.tiles:
            self.all_sprites.add(
                self.soil_sprites, self.plant_sprites, self.water_sprites
            )
            return
        for x, y, _ in layer.tiles():
            tile = Tile((x, y), ())
            tile.add(self.all_sprites, self.soil_sprites)

            self._setup_tile(tile)

            tile.farmable = True

            if previous_soil_data is not None and previous_soil_data:
                self._prepare_tile_from_saved_data(tile, (x, y), previous_soil_data)

            self.tiles[(x, y)] = tile

        for pos, tile in self.tiles.items():
            self.update_tile_image(tile, pos)

    def _prepare_tile_from_saved_data(
        self, tile: Tile, pos, prev_data: dict[Coordinate, TileInfo]
    ):
        if pos not in prev_data:
            return
        tile_info = prev_data[pos]
        self._hoe(tile)
        if tile_info.watered:
            self._water(tile)
        if tile_info.plant_info is not None:
            plant_info = tile_info.plant_info
            seed_name = plant_info.plant_type.as_plant_name()
            frames = self.level_frames[seed_name]
            plant = Plant(plant_info.plant_type, (), tile, frames)
            plant.add(self.all_sprites, self.plant_sprites)
            tile.plant = plant
            plant.age = plant_info.age

    def update_tile_image(self, tile, pos):
        for dx, dy in self.neighbor_directions:
            neighbor = self.tiles.get((pos[0] + dx, pos[1] + dy))
            if neighbor is not None:
                neighbor_pos = (pos[0] + dx, pos[1] + dy)
                neighbor_type = self.determine_tile_type(neighbor_pos)
                if neighbor.hoed:
                    neighbor.image = self.level_frames["soil"][neighbor_type]
                    neighbor.pf_weight = 0
                else:
                    neighbor.pf_weight = int(neighbor_type != "o")

        tile_type = self.determine_tile_type(pos)
        if tile.hoed:
            tile.image = self.level_frames["soil"][tile_type]
            tile.pf_weight = 0
        else:
            tile.pf_weight = int(tile_type != "o")

    def _hoe(self, tile):
        """Hoe a tile.

        WARNING: this method is for internal usage.
        Use SoilLayer.hoe instead."""
        if tile is not None and tile.farmable and not tile.hoed:
            tile.hoed = True
            self.update_tile_image(tile, tile.pos)
            return True
        return False

    def hoe(self, pos) -> bool:
        """:return: Whether the tile was successfully hoed or not"""
        tile = self.tiles.get(pos)
        return self._hoe(tile)

    def _water(self, tile):
        """Water a tile.

        WARNING: this method is for internal usage.
        Use SoilLayer.water instead."""
        if tile is not None and tile.hoed and not tile.watered:
            tile.watered = True

            water_frames = list(self.level_frames["soil water"].values())
            water_frame = choice(water_frames)
            water = Sprite(
                tile_to_screen(tile.pos),
                water_frame,
                (),
                Layer.SOIL_WATER,
            )
            water.add(self.all_sprites, self.water_sprites)
            return True

        return False

    def water(self, pos):
        """:return: Whether the tile was successfully watered or not"""
        tile = self.tiles.get(pos)
        return self._water(tile)

    def water_all(self):
        for pos, tile in self.tiles.items():
            if tile.hoed:
                self.water(pos)
                self.update_tile_image(tile, pos)

    def _plant(self, pos, seed, check=lambda s, t: True):
        """Plant a seed.

        WARNING: this method is for internal usage. Consider using
        SoilLayer.plant instead."""
        tile = self.tiles.get(pos)
        seed_resource = FarmingTool.as_inventory_resource(seed)
        seed_type = SeedType.from_farming_tool(seed)
        if tile and tile.hoed and not tile.planted:
            if not check(seed_resource, 1):
                return False

            seed_name = seed_type.as_plant_name()
            frames = self.level_frames[seed_name]
            groups = (self.plant_sprites,)
            tile.plant = Plant(seed_type, groups, tile, frames)
            self.all_sprites.add(tile.plant)
            return True

        return False

    def plant(
        self, pos, seed, remove_resource: Callable[[InventoryResource, int], bool]
    ):
        """:return: Whether the tile was successfully planted or not"""
        return self._plant(pos, seed, remove_resource)

    def harvest(
        self,
        pos,
        add_resource: Callable[[InventoryResource, int], None],
        create_particle: Callable[[pygame.sprite.Sprite], None],
    ) -> bool:
        """:return: Whether the tile was successfully harvested or not"""

        tile = self.tiles.get(pos)
        if tile and getattr(tile.plant, "harvestable", False):
            # add resource
            resource = SeedType.as_nonseed_ir(tile.plant.seed_type)
            quantity = 3

            add_resource(resource, quantity)

            # remove plant
            create_particle(tile.plant)
            tile.plant.kill()
            tile.plant = None
            return True

        return False

    def update(self):
        self.raining = False
        for tile in self.tiles.values():
            if tile.watered:
                if tile.plant:
                    tile.plant.grow()
                tile.watered = False
            for sprite in self.water_sprites:
                sprite.kill()

    def determine_tile_type(self, pos):
        x, y = pos
        tile_above = self.tiles.get((x, y - 1))
        tile_below = self.tiles.get((x, y + 1))
        tile_right = self.tiles.get((x + 1, y))
        tile_left = self.tiles.get((x - 1, y))

        hoed_above = getattr(tile_above, "hoed", False)
        hoed_below = getattr(tile_below, "hoed", False)
        hoed_right = getattr(tile_right, "hoed", False)
        hoed_left = getattr(tile_left, "hoed", False)

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


class SoilManager:
    all_sprites: AllSprites
    frames: dict

    _areas: dict[StudyGroup, SoilArea | None]

    def __init__(self, all_sprites: AllSprites, frames: dict):
        self.all_sprites = all_sprites
        self.frames = frames

        self._areas = {i: SoilArea(self.all_sprites, self.frames) for i in StudyGroup}

        self.raining = False

    @property
    def raining(self) -> bool:
        return self._raining

    @raining.setter
    def raining(self, value: bool):
        self._raining = value
        if self.raining:
            for area in self.all_areas():
                area.raining = True

    def all_areas(self):
        for area in self._areas.values():
            yield area

    def get_area(self, study_group: StudyGroup) -> SoilArea:
        area = self._areas[study_group]
        return area

    def load_area(
        self,
        study_group: StudyGroup,
        layer: TiledTileLayer,
        previous_soil_data: dict | None = None,
    ):
        self.get_area(study_group).create_soil_tiles(
            layer, previous_soil_data=previous_soil_data
        )

    def all_soil_sprites(self):
        for area in self.all_areas():
            yield area.soil_sprites

    def hoe(self, character: Character, pos):
        return self.get_area(character.study_group).hoe(pos)

    def water(self, character: Character, pos):
        return self.get_area(character.study_group).water(pos)

    def plant(
        self,
        character: Character,
        pos,
        seed,
        remove_resource: Callable[[InventoryResource, int], bool],
    ):
        return self.get_area(character.study_group).plant(pos, seed, remove_resource)

    def update(self):
        for area in self.all_areas():
            area.update()
