from .settings import LAYERS, GROW_SPEED, APPLE_POS, SCALE_FACTOR, KEYBINDS, SCREEN_WIDTH, SCREEN_HEIGHT
import pygame
from pygame import Vector2 as vector    
from .timer import Timer
from random import randint, choice
from .support import load_data, save_data


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z=LAYERS['main'], name=None):
        super().__init__(groups)
        self.surf = surf
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)
        self.z = z
        self.name = name


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


class Plant(CollideableSprite):
    def __init__(self, seed_type, groups, soil_sprite, frames, check_watered):
        super().__init__(soil_sprite.rect.center, frames[0], groups, (0, 0), LAYERS['plant'])
        self.rect.center = soil_sprite.rect.center + pygame.Vector2(0.5, -3) * SCALE_FACTOR
        self.hitbox_rect = self.rect.copy()
        self.soil = soil_sprite
        self.check_watered = check_watered
        self.frames = frames
        self.hitbox = None

        self.seed_type = seed_type
        self.age = 0
        self.max_age = len(self.frames) - 1
        self.grow_speed = GROW_SPEED[seed_type]
        self.harvestable = False

    def grow(self):
        if self.check_watered(self.rect.center):
            self.age += self.grow_speed

            if int(self.age) > 0:
                self.z = LAYERS['main']
                self.hitbox = self.rect.inflate(-26, -self.rect.height * 0.4)

            if self.age >= self.max_age:
                self.age = self.max_age
                self.harvestable = True

            self.image = self.frames[int(self.age)]
            self.rect = self.image.get_frect(midbottom=self.soil.rect.midbottom + pygame.math.Vector2(0, 2))


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
                Sprite((x, y), self.apple_surf, (self.apple_sprites, self.groups()[0]), LAYERS['fruit'])

    def hit(self, entity):
        self.health -= 1
        # remove an apple
        if len(self.apple_sprites.sprites()) > 0:
            random_apple = choice(self.apple_sprites.sprites())
            random_apple.kill()
            entity.add_resource('apple')
        if self.health <= 0 and self.alive:
            print('x')
            self.image = self.stump_surf
            self.rect = self.image.get_frect(midbottom=self.rect.midbottom)
            self.hitbox = self.rect.inflate(-10, -self.rect.height * 0.6)
            self.alive = False
            entity.add_resource('wood', 5)


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


class Hill(CollideableSprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        self.hitbox_rect = self.rect.inflate(0, -30)
        self.hitbox_rect.midbottom = self.rect.midbottom


class Entity(Sprite):
    def __init__(self, pos, frames, groups, z=LAYERS['main']):
        self.frames, self.frame_index, self.state = frames, 0, 'idle'
        super().__init__(pos, frames[self.state][0], groups, z)



class Player(CollideableSprite):
    def __init__(self, pos, frames, groups, collision_sprites, apply_tool, interact, sounds):
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
        self.keybinds = self.import_controls() 
        self.direction = vector()
        self.speed = 250
        self.collision_sprites = collision_sprites
        self.blocked = False
        self.interact = interact
        self.hitbox_offset = vector(0, -62)

        # tools
        self.available_tools = ['axe', 'hoe', 'water']
        self.tool_index = 0
        self.current_tool = self.available_tools[self.tool_index]
        self.tool_active = False
        self.apply_tool = apply_tool

        # seeds 
        self.available_seeds = ['corn', 'tomato']
        self.seed_index = 0
        self.current_seed = self.available_seeds[self.seed_index]

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
    def get_target_pos(self):
        vectors = {
            'left': vector(-1, 0), 
            'right': vector(1, 0), 
            'down': vector(0, 1),
            'up': vector(0, -1), 
        }
        return self.rect.center + vectors[self.facing_direction] * 40

    def plant_seed(self):
        target_pos = self.get_target_pos()
        player = self
        self.apply_tool(self.current_seed, target_pos, player)
    
    def play_tool_sound(self):
        if self.current_tool in ('hoe', 'axe'):
            self.sounds['swing'].play()

    def use_tool(self):
        target_pos = self.get_target_pos()
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
    def draw_test(self):
        rect = self.rect.copy()
        offset = vector(self.rect.center) - vector(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
        rect.topleft -= offset
        pygame.draw.rect(self.display_surface, 'red', rect, 2)

        pos = self.pos - offset
        pygame.draw.circle(self.display_surface, 'yellow', pos, 5)

        # blocks
        for sprite in self.collision_sprites:
            # if sprite.name is not None:
            rect = sprite.hitbox_rect.copy()
            rect.topleft -= offset
            pygame.draw.rect(self.display_surface, 'blue', rect, 0, 2)
