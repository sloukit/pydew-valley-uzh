from .settings import *
from .sprites import Sprite, Plant
from random import choice

class SoilLayer:
    def __init__(self, all_sprites, collision_sprites, tmx_map, level_frames):
        # sprite groups
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.soil_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.plant_sprites = pygame.sprite.Group()

        self.level_frames = level_frames
        self.create_soil_grid(tmx_map)
    
    def create_soil_grid(self, tmx_map):
        self.grid = [[[] for col in range(tmx_map.width)] for row in range(tmx_map.height)]
        for x, y, _ in tmx_map.get_layer_by_name('Farmable').tiles():
            self.grid[y][x].append('F')
    
    def hoe(self, pos, hoe_sound):
        x, y = int(pos[0] / (TILE_SIZE * SCALE_FACTOR)), int(pos[1] / (TILE_SIZE * SCALE_FACTOR))        
        if 'F' in self.grid[y][x]:
            self.grid[y][x].append('X')
            self.create_soil_tiles()
            hoe_sound.play()

    def water(self, pos):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(pos):

                x = int(soil_sprite.rect.x / (TILE_SIZE * SCALE_FACTOR))
                y = int(soil_sprite.rect.y / (TILE_SIZE * SCALE_FACTOR))
                self.grid[y][x].append('W')

                pos = soil_sprite.rect.topleft
                surf = choice(list(self.level_frames['soil water'].values()))
                Sprite(pos, surf, [self.all_sprites, self.water_sprites], LAYERS['soil water'])

    def water_all(self):
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell and 'W' not in cell:
                    cell.append('W')
                    x = index_col * TILE_SIZE * SCALE_FACTOR
                    y = index_row * TILE_SIZE * SCALE_FACTOR
                    surf = choice(list(self.level_frames['soil water'].values()))
                    Sprite((x,y), surf, [self.all_sprites, self.water_sprites], LAYERS['soil water'])

    def check_watered(self, pos):
        x = int(pos[0] / (TILE_SIZE * SCALE_FACTOR))
        y = int(pos[1] / (TILE_SIZE * SCALE_FACTOR))
        cell = self.grid[y][x]
        return 'W' in cell

    def remove_water(self):
        # destroy all water sprites
        for sprite in self.water_sprites.sprites():
            sprite.kill()

        # clean up the grid
        for row in self.grid:
            for cell in row:
                if 'W' in cell:
                    cell.remove('W')

    def plant_seed(self, pos, seed, inventory, plant_sounds):
        for soil_sprite in self.soil_sprites.sprites():
            if soil_sprite.rect.collidepoint(pos):

                x = int(soil_sprite.rect.x / (TILE_SIZE * SCALE_FACTOR))
                y = int(soil_sprite.rect.y / (TILE_SIZE * SCALE_FACTOR))

                if 'P' not in self.grid[y][x] and inventory[seed+" seed"] > 0:
                    self.grid[y][x].append('P')
                    Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite, self.level_frames[seed], self.check_watered)
                    inventory[seed+" seed"] -= 1
                    plant_sounds[0].play()
                else:
                    # play a sound that indecates u cant plant a seed
                    plant_sounds[1].play()

    def update_plants(self):
        for plant in self.plant_sprites.sprites():
            plant.grow()

    def create_soil_tiles(self):
        self.soil_sprites.empty()
        for index_row, row in enumerate(self.grid):
            for index_col, cell in enumerate(row):
                if 'X' in cell:
                        
                        # tile options 
                        t = 'X' in self.grid[index_row - 1][index_col]
                        b = 'X' in self.grid[index_row + 1][index_col]
                        r = 'X' in row[index_col + 1]
                        l = 'X' in row[index_col - 1]

                        tile_type = 'o'

                        # all sides
                        if all((t,r,b,l)): tile_type = 'x'

                        # horizontal tiles only
                        if l and not any((t,r,b)): tile_type = 'r'
                        if r and not any((t,l,b)): tile_type = 'l'
                        if r and l and not any((t,b)): tile_type = 'lr'

                        # vertical only 
                        if t and not any((r,l,b)): tile_type = 'b'
                        if b and not any((r,l,t)): tile_type = 't'
                        if b and t and not any((r,l)): tile_type = 'tb'

                        # corners 
                        if l and b and not any((t,r)): tile_type = 'tr'
                        if r and b and not any((t,l)): tile_type = 'tl'
                        if l and t and not any((b,r)): tile_type = 'br'
                        if r and t and not any((b,l)): tile_type = 'bl'

                        # T shapes
                        if all((t,b,r)) and not l: tile_type = 'tbr'
                        if all((t,b,l)) and not r: tile_type = 'tbl'
                        if all((l,r,t)) and not b: tile_type = 'lrb'
                        if all((l,r,b)) and not t: tile_type = 'lrt'

                        Sprite(
                            pos = (index_col * TILE_SIZE * SCALE_FACTOR,index_row * TILE_SIZE * SCALE_FACTOR),
                            surf = self.level_frames['soil'][tile_type],
                            groups = (self.all_sprites, self.soil_sprites),
                            z = LAYERS['soil']
                            )
