from .settings import *
from .timer import Timer
from .support import generate_particle_surf
from random import randint, choice
from .pause_menu import PauseMenu
from .settingsmenu import SettingsMenu


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int | float, int | float], surf: pygame.Surface, groups: tuple[pygame.sprite.Group], z: int = LAYERS['main'], name: str | None = None):
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
    def __init__(self, pos, surf, groups, shrink, z=LAYERS['main']):
        super().__init__(pos, surf, groups, z)
        self.hitbox_rect = self.rect.inflate(-shrink[0], -shrink[1])


class Plant(CollideableSprite):
    def __init__(self, seed_type, groups, soil_sprite, frames, check_watered):
        super().__init__(soil_sprite.rect.center, frames[0], groups, (0, 0), LAYERS['plant'])
        self.rect.center = soil_sprite.rect.center + pygame.Vector2(0.5, -3) * SCALE_FACTOR
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
    def __init__(self, pos, surf, groups, name, apple_surf, stump_surf,recover_surf):
        super().__init__(pos, surf, groups, (30 * SCALE_FACTOR, 20 * SCALE_FACTOR))
        self.name = name
        self.part_surf = generate_particle_surf(self.image)
        self.apple_surf = apple_surf
        self.stump_surf = stump_surf
        self.health = 5
        self.timer = Timer(300, func=self.unhit)
        self.hitbox = None
        self.was_hit = False
        self.alive = True
        self.apple_sprites = pygame.sprite.Group()
        self.create_fruit()
        self.position = pos
        self.grow_frame_info = [(12,72,40,56),(76,52,40,76),(128,28,64,100),(196,24,56,104)]
        self.frames = []
        for area in self.grow_frame_info:
            new_frame = recover_surf.subsurface(pygame.Rect(area))
            self.frames.append(new_frame)

    def unhit(self):
        self.was_hit = False
        if self.health < 0:
            if self.health == -4:
                self.image = self.stump_surf
                
            else:
                self.hitbox = self.rect.inflate(-self.rect.width, -self.rect.height)
                self.image = self.frames[self.health+3]
            
            if self.alive:
                self.rect = self.image.get_frect(midbottom=self.rect.midbottom)
                self.hitbox = self.rect.inflate(-10, -self.rect.height * 0.6)
                self.alive = False
                print("x")
            print(self.health)
            print(self.alive)
        elif self.health >= 0 and self.alive:
            self.image = self.surf

    def create_fruit(self):
        if self.alive:
            for pos in APPLE_POS['default']:
                if randint(0, 10) < 6:
                    x = pos[0] + self.rect.left
                    y = pos[1] + self.rect.top
                    Sprite((x, y), self.apple_surf, (self.apple_sprites, self.groups()[0]), LAYERS['fruit'])

    def update(self, dt):
        self.timer.update()

    def hit(self, entity):
        if self.was_hit:
            return
        self.was_hit = True
        
        if self.alive:

            self.health -= 1
        
        # remove an apple
        if len(self.apple_sprites.sprites()) > 0:
            random_apple = choice(self.apple_sprites.sprites())
            random_apple.kill()
            entity.add_resource('apple')
        if self.health < 0 and self.alive:
            
            #adds apples that were on the tree
            entity.add_resource('apple', len(self.apple_sprites.sprites()))
            entity.add_resource('wood', 5)
            self.health = -4
            print("xx")
            #removes all thew apples
            for apple in self.apple_sprites.sprites():
                apple.kill()
        elif not self.alive:
            entity.add_resource('wood', 1)
            self.health = -4
            self.alive = True # this is used to trick the system into reseting the growing cycle in the most scuffed way possible, im very sorry
        self.image = generate_particle_surf(self.image)
        self.timer.activate()
#whenever the tree is chopped, it slowly regrows, this function steps through the regrowing animation
    def recover(self):
        if not self.alive:
            self.health = self.health + 1
            print("recovered")
            if self.health < 1:
                
                self.image = self.frames[self.health+3]
                
                
                self.rect = self.image.get_frect(midbottom=self.rect.midbottom)
                self.hitbox = self.rect.inflate(-self.rect.width, -self.rect.height)
            else:
                self.health = 5
                self.hitbox = None
                self.image = self.surf
                self.rect = self.image.get_frect(topleft=self.position)
                self.alive = True
                self.create_fruit()        


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


class Entity(Sprite):
    def __init__(self, pos, frames, groups, z=LAYERS['main']):
        self.frames, self.frame_index, self.state = frames, 0, 'idle'
        super().__init__(pos, frames[self.state][0], groups, z)


class Player(CollideableSprite):
    def __init__(self, game, pos: Coordinate, frames, groups, collision_sprites: pygame.sprite.Group, apply_tool: Function, interact: Function, sounds: SoundDict, font):
        self.game = game
        self.frames, self.frame_index, self.state, self.facing_direction = frames, 0, 'idle', 'down'
        super().__init__(pos, self.frames[self.state][self.facing_direction][self.frame_index], groups,
                         (44 * SCALE_FACTOR, 40 * SCALE_FACTOR))

        # movement
        self.direction = pygame.Vector2()
        self.speed = 250
        self.font = font
        self.collision_sprites = collision_sprites
        self.blocked = False
        self.paused = False
        self.interact = interact
        self.sounds = sounds
        self.plant_collide_rect = self.hitbox_rect.inflate(10, 10)

        # tools
        self.available_tools = ['axe', 'hoe', 'water']
        self.tool_index = 0
        self.current_tool = self.available_tools[self.tool_index]
        self.tool_active = False
        self.just_used_tool = False
        self.apply_tool = apply_tool
        self.pause_menu = PauseMenu(self.font)
        self.settings_menu = SettingsMenu(self.font, self.sounds)
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

    def input(self):
        keys = pygame.key.get_pressed()
        recent_keys = pygame.key.get_just_pressed()
        if recent_keys[pygame.K_SPACE] and self.game.dm.showing_dialogue:
            self.game.dm.advance()
            if not self.game.dm.showing_dialogue:
                self.blocked = False
            return
        # movement
        if not self.tool_active and not self.blocked:
            if recent_keys[pygame.K_ESCAPE]:
                self.paused = not self.paused
                self.direction.y = 0
                self.direction.x = 0
                return
            if recent_keys[pygame.K_t]:
                if self.game.dm.showing_dialogue:
                    pass
                else:
                    self.game.dm.open_dialogue("test")
                    self.blocked = True
                return

        if not self.tool_active and not self.blocked and not self.paused:
            self.direction.x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            self.direction.y = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
            self.direction = self.direction.normalize() if self.direction else self.direction

            # tool switch 
            if recent_keys[pygame.K_q]:
                self.tool_index = (self.tool_index + 1) % len(self.available_tools)
                self.current_tool = self.available_tools[self.tool_index]

            # tool use
            if recent_keys[pygame.K_SPACE]:
                self.tool_active = True
                self.frame_index = 0
                self.direction = pygame.Vector2()
                if self.current_tool in {'hoe', 'axe'}:
                    self.sounds['swing'].play()

            # seed switch 
            if recent_keys[pygame.K_e]:
                self.seed_index = (self.seed_index + 1) % len(self.available_seeds)
                self.current_seed = self.available_seeds[self.seed_index]

            # seed used 
            if recent_keys[pygame.K_LCTRL]:
                self.use_tool('seed')

                # interact
            if recent_keys[pygame.K_RETURN]:
                self.interact(self.rect.center)

    def get_state(self):
        self.state = 'walk' if self.direction else 'idle'

    def get_facing_direction(self):
        # prioritizes vertical animations, flip if statements to get horizontal ones
        if self.direction.x:
            self.facing_direction = 'right' if self.direction.x > 0 else 'left'
        if self.direction.y:
            self.facing_direction = 'down' if self.direction.y > 0 else 'up'

    def get_target_pos(self):
        vectors = {'left': pygame.Vector2(-1, 0), 'right': pygame.Vector2(1, 0), 'down': pygame.Vector2(0, 1),
                   'up': pygame.Vector2(0, -1), }
        return self.rect.center + vectors[self.facing_direction] * 40

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.plant_collide_rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y < 0:
                        self.hitbox_rect.top = sprite.rect.bottom
                    if self.direction.y > 0:
                        self.hitbox_rect.bottom = sprite.rect.top

    def animate(self, dt):
        current_animation = self.frames[self.state][self.facing_direction]
        self.frame_index += 4 * dt
        if not self.tool_active:
            self.image = current_animation[int(self.frame_index) % len(current_animation)]
        else:
            tool_animation = self.frames[self.available_tools[self.tool_index]][self.facing_direction]
            if self.frame_index < len(tool_animation):
                self.image = tool_animation[min((round(self.frame_index), len(tool_animation) - 1))]
                if round(self.frame_index) == len(tool_animation) - 1 and not self.just_used_tool:
                    self.just_used_tool = True
                    self.use_tool('tool')
            else:
                # self.use_tool('tool')
                self.state = 'idle'
                self.tool_active = False
                self.just_used_tool = False

    def use_tool(self, option):
        self.apply_tool(self.current_tool if option == 'tool' else self.current_seed, self.get_target_pos(), self)

    def add_resource(self, resource, amount=1):
        self.inventory[resource] += amount
        self.sounds['success'].play()

    def update(self, dt):
        self.input()
        self.get_state()
        self.get_facing_direction()
        self.move(dt)
        self.animate(dt)
