import sys
import pygame 


from random import randint
from pathfinding.core.grid import Grid as PF_Grid
from pathfinding.finder.a_star import AStarFinder as PF_AStarFinder

from src.support import map_coords_to_tile, load_data, resource_path
from src.groups import AllSprites
from src.overlay.soil import SoilLayer
from src.overlay.transition import Transition
from src.overlay.sky import Sky, Rain
from src.overlay.overlay import Overlay
from src.screens.shop import ShopMenu
from src.sprites.base import Sprite, AnimatedSprite
from src.sprites.particle import ParticleSprite
from src.sprites.tree import Tree
from src.sprites.player import Player
from src.enums import FarmingTool, GameState
from src.settings import (
    TILE_SIZE,
    SCALE_FACTOR,
    LAYERS,
    MapDict,
)


class Level:
    def __init__(self, game, switch, tmx_maps: MapDict, frames, sounds):
        # main setup
        self.display_surface = pygame.display.get_surface()
        self.game = game
        self.switch_screen = switch

        # pathfinding
        self.pf_matrix = []
        self.pf_grid: PF_Grid
        self.pf_finder = PF_AStarFinder()

        # sprite groups
        self.entities = {}
        self.npcs = {}
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.tree_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()

        # assets
        self.font = pygame.font.Font(resource_path('font/LycheeSoda.ttf'), 30)
        self.frames = frames
        self.sounds = sounds
        self.tmx_maps = tmx_maps

        # soil
        self.soil_layer = SoilLayer(
            self.all_sprites,
            self.collision_sprites,
            tmx_maps['main'],
            frames["level"])

        # weather
        self.sky = Sky()
        self.rain = Rain(self.all_sprites, frames['level'], self.get_map_size())
        self.raining = False

        # setup map
        self.setup()
        self.player = self.entities['Player']

        # day night cycle
        self.transition = Transition(self.reset, self.finish_reset)
        self.day_transition = False
        self.current_day = 0

        # weather
        self.sky = Sky()
        self.rain = Rain(
            self.all_sprites,
            frames["level"],
            (tmx_maps['main'].width *
             TILE_SIZE *
             SCALE_FACTOR,
             tmx_maps['main'].height *
             TILE_SIZE *
             SCALE_FACTOR))

        # overlays
        self.overlay = Overlay(self.player, frames['overlay'])
        self.shop = ShopMenu(self.player, self.toggle_shop, self.font)
        self.shop_active = False


    # setup
    def setup(self):
        self.activate_music()

        self.setup_layer_tiles('Lower ground', self.setup_environment)
        self.setup_layer_tiles('Upper ground', self.setup_environment)
        self.setup_layer_tiles('Water', self.setup_water)

        self.setup_layer_objects('Collidable objects', self.setup_objects)
        self.setup_layer_objects('Collisions', self.setup_collisions)
        self.setup_layer_objects('Interactions', self.setup_interactions)
        self.setup_layer_objects('Entities', self.setup_entities)

    def setup_layer_tiles(self, layer, setup_func):
        for  x, y, surf in self.tmx_maps['main'].get_layer_by_name(layer).tiles():
            x = x * TILE_SIZE * SCALE_FACTOR
            y = y * TILE_SIZE * SCALE_FACTOR
            pos = (x, y)
            setup_func(pos, surf)

    def setup_environment(self, pos, surf):
        image = pygame.transform.scale_by(surf, SCALE_FACTOR)
        Sprite(pos, image, self.all_sprites, LAYERS['lower ground'])

    def setup_water(self, pos, surf):
        image = self.frames['level']['animations']['water']
        AnimatedSprite(pos, image, self.all_sprites, LAYERS['water'])

    def setup_layer_objects(self, layer, setup_func):
        for obj in self.tmx_maps['main'].get_layer_by_name(layer):
            x = obj.x * SCALE_FACTOR
            y = obj.y * SCALE_FACTOR
            pos = (x, y)
            setup_func(pos, obj)

    def setup_objects(self, pos, obj):
        image = pygame.transform.scale_by(obj.image, SCALE_FACTOR)

        if obj.name == 'Tree':
            apple_frames = self.frames['level']['objects']['apple']
            stump_frames = self.frames['level']['objects']['stump']

            Tree(pos, image, (self.all_sprites, self.collision_sprites, self.tree_sprites), obj.name, apple_frames, stump_frames)
        else:
            Sprite(pos, image, (self.all_sprites, self.collision_sprites))

    def setup_collisions(self, pos, obj):
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        Sprite(pos, image, self.collision_sprites)

    def setup_interactions(self, pos, obj):
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        Sprite(pos, image, self.interaction_sprites, LAYERS['main'], obj.name)

    def setup_entities(self, pos, obj):
        self.entities[obj.name] = Player(game=self.game,
            pos=pos,
            frames=self.frames['character']['rabbit'],
            groups=self.all_sprites,
            collision_sprites=self.collision_sprites,
            apply_tool=self.apply_tool,
            interact=self.interact,
            sounds=self.sounds,
            font=self.font
        )

    def get_map_size(self):
        return self.tmx_maps['main'].width * TILE_SIZE * SCALE_FACTOR, self.tmx_maps['main'].height * TILE_SIZE * SCALE_FACTOR

    def activate_music(self):
        volume = 0.1
        try:
            volume = load_data('volume.json') / 1000
        except FileNotFoundError:
            pass
        self.sounds["music"].set_volume(volume)
        self.sounds["music"].play(-1)


    # events
    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            self.echap(event)

    def echap(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PAUSE)
                self.player.direction.xy = (0, 0)


    # plant collision
    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites:

                is_player_near = plant.rect.colliderect(self.player.plant_collide_rect)

                if plant.harvestable and is_player_near:

                    # add resource
                    ressource = plant.seed_type
                    quantity = 3
                    self.player.add_resource(ressource, quantity)

                    # update grid
                    x, y = map_coords_to_tile(plant.rect.center)
                    self.soil_layer.grid[y][x].remove('P')

                    # remove plant
                    plant.kill()
                    self.create_particle(plant)

    def create_particle(self, sprite):
        ParticleSprite(sprite.rect.topleft, sprite.image, self.all_sprites)

    def apply_tool(self, tool: FarmingTool, pos, entity):
        match tool:
            case FarmingTool.AXE:
                for tree in self.tree_sprites:
                    if tree.rect.collidepoint(pos):
                        tree.hit(entity)
                        self.sounds['axe'].play()
            case FarmingTool.HOE:
                self.soil_layer.hoe(pos, hoe_sound=self.sounds['hoe'])
            case FarmingTool.WATERING_CAN:
                self.soil_layer.water(pos)
                self.sounds['water'].play()
            case _:  # All seeds
                self.soil_layer.plant_seed(pos, tool,
                                           entity.inventory, plant_sounds=[self.sounds['plant'],
                                                                           self.sounds['cant_plant']])

    def interact(self):
        collided_interactions = pygame.sprite.spritecollide(self.player, self.interaction_sprites, False)
        if collided_interactions:
            if collided_interactions[0].name == 'Bed':
                self.start_reset()
            if collided_interactions[0].name == 'Trader':
                self.toggle_shop()

    def toggle_shop(self):
        self.shop_active = not self.shop_active

    # reset
    def reset(self):
        self.current_day += 1

        # plants
        self.soil_layer.update_plants()

        self.sky.set_time(6, 0)  # set to 0600 hours upon sleeping

        # soil
        self.soil_layer.remove_water()
        self.raining = randint(0, 10) > 7
        self.soil_layer.raining = self.raining
        if self.raining:
            self.soil_layer.water_all()

        # apples on the trees

        # No need to iterate using explicit sprites() call.
        # Iterating over a sprite group normally will do the same thing
        for tree in self.tree_sprites:
            for apple in tree.apple_sprites:
                apple.kill()
            tree.create_fruit()

        # sky
        self.sky.start_color = [255, 255, 255]

    def finish_reset(self):
        self.day_transition = False
        for entity in self.entities.values():
            entity.blocked = False

    def start_reset(self):
        self.day_transition = True
        for entity in self.entities.values():
            entity.blocked = True
            entity.direction = pygame.Vector2(0, 0)


    # draw
    def draw_overlay(self):
        current_time = self.sky.get_time()
        self.overlay.display(current_time)

    def draw(self, dt):
        self.display_surface.fill('gray')
        self.all_sprites.draw(self.player.rect.center)
        self.draw_overlay()
        self.sky.display(dt)


    # update
    def update_rain(self):
        if self.raining and not self.shop_active:
            self.rain.update()

    def update_day(self):
        if self.day_transition:
            self.transition.play()
            self.sky.set_time(6, 0)   # set to 0600 hours upon sleeping

    def update(self, dt):
        # update
        self.event_loop()
        self.plant_collision()
        self.update_rain()
        self.update_day()
        self.all_sprites.update(dt)

        # draw
        self.draw(dt)
