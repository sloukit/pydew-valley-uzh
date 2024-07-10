from .settings import LAYERS, GROW_SPEED, APPLE_POS, SCALE_FACTOR, KEYBINDS, TILE_SIZE
import pygame
from pygame import Vector2 as vector    
from .timer import Timer
from random import randint, choice
from .support import load_data, save_data, screen_to_tile, tile_to_screen


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z=LAYERS['main'], name=None):
        super().__init__(groups)
        self.surf = surf
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)
        self.z = z
        self.name = name
        self.hitbox_rect = self.rect.copy()
    
    def draw(self, display_surface, offset):
        display_surface.blit(self.image, self.rect.topleft + offset)


class ParticleSprite(Sprite):
    def __init__(self, pos, surf, groups, duration=300):
        white_surf = pygame.mask.from_surface(surf).to_surface()
        white_surf.set_colorkey('black')
        super().__init__(pos, white_surf, groups, LAYERS['particles'])
        self.timer = Timer(duration, autostart=True, func=self.kill)

    def update(self, dt):
        self.timer.update()


class CollideableSprite(Sprite):
    def __init__(self, pos, surf, groups, z=LAYERS['main'], name=None):
        super().__init__(pos, surf, groups, z, name)
        self.hitbox_rect = self.rect.copy()


class Plant(Sprite):
    def __init__(self, seed, groups, tile, frames):
        super().__init__(tile.rect.center, frames[0], groups, LAYERS['plant'])
        
        # main setup
        self.frames = frames
        self.image = self.frames[0]
        self.rect.center = tile.rect.center + vector(0.5, -3) * SCALE_FACTOR
        self.hitbox_rect = self.rect.copy()
        self.hitbox = None

        # tile
        self.tile = tile

        # plant
        self.seed = seed
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[seed]
        self.harvestable = False

    def grow(self):
        if self.tile.watered:
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.inflate(-26, -self.rect.height * 0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            index = int(self.age)
            self.image = self.frames[index]
            self.rect = self.image.get_frect(midbottom=self.tile.rect.midbottom + vector(0, 2))
    

class Tree(CollideableSprite):
    def __init__(self, pos, surf, groups, name, apple_surf, stump_surf):
        super().__init__(pos, surf, groups)
        self.name = name
        self.apple_surf = apple_surf
        self.stump_surf = stump_surf
        self.health = 5
        self.hitbox = None
        self.hitbox_rect = pygame.Rect(0, 0, 40, 20)
        self.hitbox_rect.midbottom = self.rect.midbottom
        self.alive = True
        self.apple_sprites = pygame.sprite.Group()
        self.create_fruit()

    def create_fruit(self):
        for pos in APPLE_POS['default']:
            if randint(0, 10) < 6:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                Sprite((x, y), self.apple_surf, (self.apple_sprites), LAYERS['fruit'])

    def hit(self, entity):
        self.health -= 1
        # remove an apple
        if len(self.apple_sprites.sprites()) > 0:
            random_apple = choice(self.apple_sprites.sprites())
            random_apple.kill()
            entity.add_resource('apple')
        if self.health <= 0 and self.alive:
            # print('x')
            self.image = self.stump_surf
            self.rect = self.image.get_frect(midbottom=self.rect.midbottom)
            self.hitbox = self.rect.inflate(-10, -self.rect.height * 0.6)
            self.alive = False
            entity.add_resource('wood', 5)
    
    def draw(self, display_surface, offset):
        super().draw(display_surface, offset)
        for apple in self.apple_sprites:
            apple.draw(display_surface, offset)


class AnimatedSprite(Sprite):
    def __init__(self, pos, frames, groups, z=LAYERS['main']):
        self.frames, self.frame_index = frames, 0
        super().__init__(pos, frames[0], groups, z)

    def animate(self, dt):
        self.frame_index += 2 * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def update(self, dt):
        self.animate(dt)


class WaterDrop(Sprite):
    def __init__(self, pos, surf, groups, moving, z):
        super().__init__(pos, surf, groups, z)
        self.timer = Timer(randint(400, 600), autostart=True, func=self.kill)
        self.start_time = pygame.time.get_ticks()
        self.moving = moving

        if moving:
            self.direction = pygame.Vector2(-2, 4)
            self.speed = randint(200, 250)

    def update(self, dt):
        self.timer.update()
        if self.moving:
            self.rect.topleft += self.direction * self.speed * dt

class Bed(CollideableSprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups, LAYERS['main'], 'Bed')
        self.hitbox_rect = self.rect.inflate(40, 0)
        self.hitbox_rect.midbottom = self.rect.midbottom

class Rock(CollideableSprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups, LAYERS['main'], 'Rock')
        self.hitbox_rect = self.rect.inflate(20, -20)
        self.hitbox_rect.midbottom = self.rect.midbottom


class Hill(CollideableSprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups, LAYERS['main'], 'Hill')
        self.hitbox_rect = self.rect.inflate(40, 10)
        # self.hitbox_rect = self.rect.inflate(40, -38)
        self.hitbox_rect.midbottom = self.rect.midbottom + vector(0, 10)


class Entity(Sprite):
    def __init__(self, pos, frames, groups, z=LAYERS['main']):
        self.frames, self.frame_index, self.state = frames, 0, 'idle'
        super().__init__(pos, frames[self.state][0], groups, z)



class Player(CollideableSprite):
    def __init__(self, pos, frames, groups, collision_sprites, apply_tool, interact, sounds):

        self.test_active = False    
        self.allSprites = groups

        # animations
        self.frames = frames
        self.frame_index = 0
        self.state = 'idle'
        self.facing_direction = 'down'
        surface = self.frames[self.state][self.facing_direction][self.frame_index]
        self.animation_speed = 4

        # main setup
        super().__init__(pos, surface, groups)
        self.display_surface = pygame.display.get_surface()

        # movement
        self.pos = vector()
        self.keybinds = self.import_controls() 
        self.direction = vector()
        self.speed = 250
        self.collision_sprites = collision_sprites
        self.blocked = False
        self.interact = interact

        # hitbox
        self.hitbox_offset = vector(0, -65)
        hitbox_midtop = self.rect.midbottom + self.hitbox_offset
        self.hitbox_rect = pygame.Rect(0, 0, 40, 40)
        self.hitbox_rect.midtop = hitbox_midtop

        # tools
        self.available_tools = ['axe', 'hoe', 'water']
        self.tool_index = 0
        self.current_tool = self.available_tools[self.tool_index]
        self.tool_active = False
        self.apply_tool = apply_tool
        self.on_farmable_tile = False

        # seeds 
        self.available_seeds = ['corn', 'tomato']
        self.seed_index = 0
        self.current_seed = self.available_seeds[self.seed_index]
        self.plant_collide_rect = pygame.Rect(0, 0, 40, 40)
        self.on_plantable_tile = False

        # inventory 
        self.inventory = {
            'wood': 20,
            'apple': 20,
            'corn': 20,
            'tomato': 20,
            'tomato seed': 5,
            'corn seed': 5,
        }
        self.money = 200

        # sounds
        self.sounds = sounds
    
    # imports
    def import_controls(self):
        data =  load_data('keybinds.json')
        if len(data) != len(KEYBINDS):
            save_data(KEYBINDS, 'keybinds.json')
            return KEYBINDS   
        return data
    
    # input
    def input(self):

        if self.controls['test']:
            self.test_active = not self.test_active

        # movement
        if not self.tool_active and not self.blocked:
            self.update_direction()

            # tool switch 
            if self.controls['next tool']:
                self.tool_index = (self.tool_index + 1) % len(self.available_tools)
                self.current_tool = self.available_tools[self.tool_index]

            # tool use
            if self.controls['use']:
                self.tool_active = True
                self.frame_index = 0
                self.direction = vector()
                self.play_tool_sound()

            # seed switch 
            if self.controls['next seed']:
                self.seed_index = (self.seed_index + 1) % len(self.available_seeds)
                self.current_seed = self.available_seeds[self.seed_index]

            # seed use
            if self.controls['plant']:
                self.plant_seed()

            # interact
            if self.controls['interact']:
                self.interact()

    # movement
    def move(self, dt):
        # x 
        x_movement = self.direction.x * self.speed * dt
        self.rect.x += int(x_movement)
        self.check_collision('horizontal')
        
        # y
        y_movement = self.direction.y * self.speed * dt
        self.rect.y += int(y_movement)
        self.check_collision('vertical')

        # hitbox
        self.hitbox_rect.midbottom = self.pos

    def check_collision(self, direction):
        self.pos = vector(self.rect.midbottom) + self.hitbox_offset

        if direction == 'vertical':
            for sprite in self.collision_sprites:
                if sprite.hitbox_rect.collidepoint(self.pos) :
                    if self.direction.y < 0:
                        self.pos.y = sprite.hitbox_rect.bottom
                    if self.direction.y > 0:
                        self.pos.y = sprite.hitbox_rect.top - 1

        
        if direction == 'horizontal':
            for sprite in self.collision_sprites:
                if sprite.hitbox_rect.collidepoint(self.pos):
                    if self.direction.x < 0:
                        self.pos.x = sprite.hitbox_rect.right
                    if self.direction.x > 0:
                        self.pos.x = sprite.hitbox_rect.left - 1

        self.rect.midbottom = self.pos - self.hitbox_offset

    # animation
    def get_animation(self):
        state = self.current_tool if self.tool_active else self.state
        direction = self.facing_direction
        current_animation = self.frames[state][direction]
        return current_animation

    def animate(self, dt):
        current_animation = self.get_animation()
        self.frame_index += self.animation_speed * dt

        if int(self.frame_index) == len(current_animation) - 1:
            if self.tool_active:    
                self.use_tool()

        if self.frame_index >= len(current_animation):
            if self.tool_active:    
                self.state = 'idle'
                self.tool_active = False

            self.frame_index %= len(current_animation)

        index = int(self.frame_index)
        self.image = current_animation[index]

    # actions
    def get_target_tile_pos(self):
        # vectors = {
        #     'left': vector(-1, 0), 
        #     'right': vector(1, 0), 
        #     'down': vector(0, 1),
        #     'up': vector(0, -1), 
        # }
        # screen_pos = self.rect.center + vectors[self.facing_direction] * 40
        # return screen_to_tile(screen_pos)
        return screen_to_tile(self.pos)

    def plant_seed(self):
        target_pos = self.get_target_tile_pos()
        player = self
        self.apply_tool(self.current_seed, target_pos, player)
    
    def play_tool_sound(self):
        if self.current_tool in ('hoe', 'axe'):
            self.sounds['swing'].play()

    def use_tool(self):
        target_pos = self.get_target_tile_pos()
        player = self
        self.apply_tool(self.current_tool, target_pos, player)

    def add_resource(self, resource, amount=1):
        self.inventory[resource] += amount
        self.sounds['success'].play()

    # update
    def update_direction(self):
        self.direction = vector()
        if self.controls['right']:
            self.direction.x = 1
        if self.controls['left']:
            self.direction.x = -1
        if self.controls['down']:
            self.direction.y = 1
        if self.controls['up']:
            self.direction.y = -1

    def update_controls(self):
        self.controls = {}

        keys = pygame.key.get_just_pressed()
        linear_keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        for name, control in self.keybinds.items():
            control_type = control['type']
            value = control['value']
            if control_type == 'key':
                self.controls[name] = keys[value]
            if control_type == 'mouse':
                self.controls[name] = mouse_buttons[value]
            if name in ('up', 'down', 'left', 'right'):
                self.controls[name] = linear_keys[value]

    def update_state(self):
        self.state = 'walk' if self.direction else 'idle'

    def update_facing_direction(self):
        # prioritizes vertical animations, flip if statements to get horizontal ones
        if self.direction.x:
            self.facing_direction = 'right' if self.direction.x > 0 else 'left'
        if self.direction.y:
            self.facing_direction = 'down' if self.direction.y > 0 else 'up'

    def update_keybinds(self):
        self.keybinds = self.import_controls()
    
    def update(self, dt):
        # update
        self.update_controls()
        self.update_state()
        self.update_facing_direction()

        # actions
        self.input()
        self.move(dt)
        self.animate(dt)

    # draw
    def draw_farmable_tile_preview(self, offset):
        if self.on_farmable_tile and self.current_tool == 'hoe':
            target_tile_pos = screen_to_tile(self.pos)
            x, y = tile_to_screen(target_tile_pos) - offset
            tile_size = TILE_SIZE * SCALE_FACTOR
            rect = pygame.Rect(x, y, tile_size, tile_size)
            pygame.draw.rect(self.display_surface, 'beige', rect, 4, 8)
    

    def draw_plantable_tile_preview(self, offset):
        if self.on_plantable_tile and self.inventory[self.current_seed + ' seed'] > 0:
            target_tile_pos = screen_to_tile(self.pos)
            x, y = tile_to_screen(target_tile_pos) - offset
            tile_size = TILE_SIZE * SCALE_FACTOR
            rect = pygame.Rect(x, y, tile_size, tile_size)
            color = (150, 166, 88)
            pygame.draw.rect(self.display_surface, color, rect, 4, 8)

    def draw_preview(self, offset):
        self.draw_farmable_tile_preview(offset)
        self.draw_plantable_tile_preview(offset)


    def draw(self, display_surface, offset): 
        self.draw_test(-offset)
        self.draw_preview(-offset)
        display_surface.blit(self.image, self.rect.topleft + offset)

    def draw_test(self, offset):
        if self.test_active:
            # rect
            rect = self.rect.copy()
            rect.topleft -= offset
            pygame.draw.rect(self.display_surface, 'red', rect, 2)

            # hitbox pos
            pos = self.pos - offset
            pygame.draw.circle(self.display_surface, 'yellow', pos, 5)

            # hitbox rect
            rect = self.hitbox_rect.copy()
            rect.topleft -= offset
            pygame.draw.rect(self.display_surface, 'blue', rect, 0, 2)

            # blocks
            for sprite in self.collision_sprites:
                # hitbox
                color = 'yellow' if sprite.name == 'Rock' else 'blue'
                rect = sprite.hitbox_rect.copy()
                rect.topleft -= offset
                pygame.draw.rect(self.display_surface, color, rect, 0, 2)

                # rect
                rect = sprite.rect.copy()
                rect.topleft -= offset
                pygame.draw.rect(self.display_surface, 'red', rect, 2)
            
        
            for sprite in self.allSprites:
                if sprite.z == LAYERS['plant']:
                    rect = sprite.rect.copy()
                    rect.topleft -= offset
                    pygame.draw.rect(self.display_surface, 'green', rect, 2)
