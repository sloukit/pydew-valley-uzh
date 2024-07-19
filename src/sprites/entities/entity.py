

from abc import ABC, abstractmethod
from typing import Callable
import pygame
from src import settings
from src.sprites.base import CollideableSprite, LAYERS
from src.enums import InventoryResource, FarmingTool, ItemToUse
from src.support import screen_to_tile


class Entity(CollideableSprite, ABC):
    def __init__(
            self,
            pos: settings.Coordinate,
            frames: dict[str, settings.AniFrames],
            groups: tuple[pygame.sprite.Group],
            collision_sprites: pygame.sprite.Group,
            shrink: tuple[int, int],
            apply_tool: Callable,
            z=LAYERS['main']):

        self.frames = frames
        self.frame_index = 0
        self.state = 'idle'
        self.facing_direction = 'down'

        super().__init__(
            pos,
            self.frames[self.state][self.facing_direction][self.frame_index],
            groups,
            z=z,
        )

        # hitbox
        self.hitbox_rect = pygame.Rect(pos, (34, 8))
        self.hitbox_offset = pygame.Vector2(0, 62) 
        self.hitbox_rect.midbottom = self.rect.midbottom - self.hitbox_offset

        # movement
        self.direction = pygame.Vector2()
        self.speed = 100
        self.collision_sprites = collision_sprites

        # tools
        self.available_tools = ['axe', 'hoe', 'water']
        self.current_tool = FarmingTool.get_first_tool_id()
        self.tool_index = self.current_tool.value - FarmingTool.get_first_tool_id().value

        self.tool_active = False
        self.just_used_tool = False
        self.apply_tool = apply_tool

        # seeds
        self.available_seeds = ['corn', 'tomato']
        self.current_seed = FarmingTool.get_first_seed_id()
        self.seed_index = self.current_seed.value - FarmingTool.get_first_seed_id().value

        # inventory
        self.inventory = {
            InventoryResource.WOOD: 0,
            InventoryResource.APPLE: 0,
            InventoryResource.CORN: 0,
            InventoryResource.TOMATO: 0,
            InventoryResource.CORN_SEED: 0,
            InventoryResource.TOMATO_SEED: 0,
        }

        # Not all Entities can go to the market, so those that can't should not have money either
        self.money = 0


    def get_state(self):
        self.state = 'walk' if self.direction else 'idle'

    def get_facing_direction(self):
        # prioritizes vertical animations, flip if statements to get horizontal
        # ones
        if self.direction.x:
            self.facing_direction = 'right' if self.direction.x > 0 else 'left'
        if self.direction.y:
            self.facing_direction = 'down' if self.direction.y > 0 else 'up'

    def get_target_pos(self):
        return screen_to_tile(self.hitbox_rect.center)

    def move(self, dt):
        # x 
        x_movement = self.direction.x * self.speed * dt
        self.rect.x += int(x_movement)
        self.check_collision('horizontal')
        
        # y
        y_movement = self.direction.y * self.speed * dt
        self.rect.y += int(y_movement)
        self.check_collision('vertical')

    # FIXME: Sometimes NPCs get stuck inside the player's hitbox
    def check_collision(self, direction):
        self.hitbox_rect.midbottom = self.rect.midbottom - self.hitbox_offset
        self.is_colliding = False

        for sprite in self.collision_sprites:
            if sprite is not self and sprite.hitbox_rect.colliderect(self.hitbox_rect):

                self.is_colliding = True
                
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.hitbox_rect.right = sprite.hitbox_rect.left 
                    if self.direction.x < 0:
                        self.hitbox_rect.left = sprite.hitbox_rect.right
                if direction == 'vertical':
                    if self.direction.y < 0:
                        self.hitbox_rect.top = sprite.hitbox_rect.bottom 
                    if self.direction.y > 0:
                        self.hitbox_rect.bottom = sprite.hitbox_rect.top

        
        self.rect.midbottom = self.hitbox_rect.midbottom + self.hitbox_offset

        

    def animate(self, dt):
        current_animation = self.frames[self.state][self.facing_direction]
        self.frame_index += 4 * dt
        if not self.tool_active:
            self.image = current_animation[int(
                self.frame_index) % len(current_animation)]
        else:
            tool_animation = self.frames[self.available_tools[self.tool_index]
            ][self.facing_direction]
            if self.frame_index < len(tool_animation):
                self.image = tool_animation[min(
                    (round(self.frame_index), len(tool_animation) - 1))]
                if round(self.frame_index) == len(tool_animation) - \
                        1 and not self.just_used_tool:
                    self.just_used_tool = True
                    self.use_tool(ItemToUse.REGULAR_TOOL)
            else:
                # self.use_tool('tool')
                self.state = 'idle'
                self.tool_active = False
                self.just_used_tool = False

    def use_tool(self, option: ItemToUse):
        self.apply_tool((self.current_tool, self.current_seed)[option], self.get_target_pos(), self)

    def add_resource(self, resource, amount=1):
        self.inventory[resource] += amount

    def update(self, dt):
        self.get_state()
        self.get_facing_direction()
        self.move(dt)
        self.animate(dt)

