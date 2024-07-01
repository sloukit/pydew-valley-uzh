from .settings import (
    pygame,
    MapDict,
    TILE_SIZE
)
from .sprites import (
    SCALE_FACTOR,
    Sprite,
    LAYERS,
    AnimatedSprite,
    Tree,
    Player,
    ParticleSprite
)
from .groups import AllSprites
from .soil import SoilLayer
from .transition import Transition
from random import randint
from .sky import Sky, Rain
from .overlay import Overlay
from .menu import Menu


class Level:
    def __init__(self, tmx_maps: MapDict, character_frames, level_frames, overlay_frames, font, sounds):
        self.display_surface = pygame.display.get_surface()

        # sprite groups
        self.entities = {}
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.tree_sprites = pygame.sprite.Group()
        self.interaction_sprites = pygame.sprite.Group()
        self.font = font
        # soil 
        self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites, tmx_maps['main'], level_frames)
        self.raining = False

        # sounds
        self.sounds = sounds

        # data 
        self.setup(tmx_maps, character_frames, level_frames)
        self.transition = Transition(self.reset, self.finish_reset)
        self.day_transition = False
        self.current_day = 0

        # weather 
        self.sky = Sky()
        self.rain = Rain(self.all_sprites, level_frames, (
            tmx_maps['main'].width * TILE_SIZE * SCALE_FACTOR, tmx_maps['main'].height * TILE_SIZE * SCALE_FACTOR))

        # overlays
        self.overlay = Overlay(self.entities['Player'], overlay_frames)
        self.menu = Menu(self.entities['Player'], self.toggle_shop, font)
        self.shop_active = False

    def setup(self, tmx_maps: MapDict, character_frames, level_frames):
        self.sounds["music"].set_volume(0.1)
        self.sounds["music"].play(-1)
        # environment
        for layer in ['Lower ground', 'Upper ground']:
            for x, y, surf in tmx_maps['main'].get_layer_by_name(layer).tiles():
                Sprite((x * TILE_SIZE * SCALE_FACTOR, y * TILE_SIZE * SCALE_FACTOR),
                       pygame.transform.scale_by(surf, SCALE_FACTOR), self.all_sprites, LAYERS['lower ground'])

        # water
        for x, y, surf in tmx_maps['main'].get_layer_by_name('Water').tiles():
            AnimatedSprite((x * TILE_SIZE * SCALE_FACTOR, y * TILE_SIZE * SCALE_FACTOR),
                           level_frames['animations']['water'], self.all_sprites, LAYERS['water'])

        # objects 
        for obj in tmx_maps['main'].get_layer_by_name('Collidable objects'):
            if obj.name == 'Tree':
                Tree((obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR), pygame.transform.scale_by(obj.image, SCALE_FACTOR),
                     (self.all_sprites, self.collision_sprites, self.tree_sprites), obj.name,
                     level_frames['objects']['apple'], level_frames['objects']['stump'])
            else:
                Sprite((obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR), pygame.transform.scale_by(obj.image, SCALE_FACTOR),
                       (self.all_sprites, self.collision_sprites))

        # collisions
        for obj in tmx_maps['main'].get_layer_by_name('Collisions'):
            Sprite((obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR),
                   pygame.Surface((obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)), (self.collision_sprites,))

        # interactions 
        for obj in tmx_maps['main'].get_layer_by_name('Interactions'):
            Sprite((obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR),
                   pygame.Surface((obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)), (self.interaction_sprites,),
                   LAYERS['main'], obj.name)

        # playable entities
        self.entities = {}
        for obj in tmx_maps['main'].get_layer_by_name('Entities'):
            self.entities[obj.name] = Player(pos=(obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR),
                                             frames=character_frames['rabbit'],
                                             groups=self.all_sprites,
                                             collision_sprites=self.collision_sprites,
                                             apply_tool=self.apply_tool,
                                             interact=self.interact,
                                             sounds=self.sounds, 
                                             font=self.font)

    def apply_tool(self, tool, pos, entity):
        if tool == 'axe':
            for tree in self.tree_sprites:
                if tree.rect.collidepoint(pos):
                    tree.hit(entity)
                    # self.create_particle(tree)
                    self.sounds['axe'].play()

        if tool == 'hoe':
            self.soil_layer.hoe(pos, hoe_sound=self.sounds['hoe'])

        if tool == 'water':
            self.soil_layer.water(pos)
            self.sounds['water'].play()

        if tool in ('corn', 'tomato'):
            self.soil_layer.plant_seed(pos, tool, entity.inventory,
                                       plant_sounds=[self.sounds['plant'], self.sounds['cant_plant']])

    def create_particle(self, sprite):
        ParticleSprite(sprite.rect.topleft, sprite.image, self.all_sprites)

    def interact(self, pos):
        collided_interaction_sprite = pygame.sprite.spritecollide(self.entities['Player'], self.interaction_sprites,
                                                                  False)
        if collided_interaction_sprite:
            if collided_interaction_sprite[0].name == 'Bed':
                self.start_reset()
            if collided_interaction_sprite[0].name == 'Trader':
                self.toggle_shop()

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
        for tree in self.tree_sprites: # No need to iterate using explicit sprites() call. Iterating over a sprite group normally will do the same thing
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

    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(self.entities['Player'].plant_collide_rect):
                    plant.kill()
                    self.entities['Player'].add_resource(plant.seed_type, 3)
                    self.create_particle(plant)
                    self.soil_layer.grid[int(plant.rect.centery / (TILE_SIZE * SCALE_FACTOR))][
                        int(plant.rect.centerx / (TILE_SIZE * SCALE_FACTOR))].remove('P')

    def toggle_shop(self):
        self.shop_active = not self.shop_active

    def update(self, dt):
        if not self.shop_active:
            self.all_sprites.update(dt)
        self.all_sprites.draw(self.entities['Player'].rect.center)
        self.plant_collision()
        self.overlay.display(self.sky.get_time())
        self.sky.display(dt)

        if self.shop_active:
            self.menu.update()

        if self.raining and not self.shop_active:
            self.rain.update()

        if self.day_transition:
            self.transition.play()
