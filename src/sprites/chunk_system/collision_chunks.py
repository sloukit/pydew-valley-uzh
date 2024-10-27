from itertools import chain

import pygame

from src.settings import COLLISION_CHUNK_H, COLLISION_CHUNK_W
from src.sprites.base import MovingSprite, Sprite
from src.sprites.chunk_system.sprite_manager import SpriteChunk, SpriteManager
from src.utils import DefaultCallableDict


class CollisionChunk(SpriteChunk):
    def add(self, sprite: Sprite):
        super().add(sprite)
        sprite.add_to_collision_chunk(self)

    def remove(self, sprite: Sprite):
        ret = super().remove(sprite)
        sprite.remove_from_collision_chunk()
        return ret


class CollisionManager(SpriteManager):
    _containers: dict[tuple[int, int], CollisionChunk]

    def __init__(self):
        self._containers = DefaultCallableDict(
            lambda x: CollisionChunk(
                x, (COLLISION_CHUNK_W, COLLISION_CHUNK_H), self.on_sprite_exit_chunk
            )
        )

    def add(self, sprite: Sprite):
        self.get_sprite_chunk(sprite).add(sprite)

    def add_persistent(self, sprite: Sprite):
        self.get_sprite_chunk(sprite).add_persistent(sprite)

    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            self.get_sprite_chunk(sprite).remove(sprite)

    def update(self):
        super().update()

    def on_sprite_exit_chunk(self, sprite: Sprite):
        if sprite.collision_chunk.remove(sprite):
            self.get_sprite_chunk(sprite).add_persistent(sprite)
        else:
            self.get_sprite_chunk(sprite).add(sprite)

    def get_chunk(self, pos: tuple[int, int]):
        return self._containers[pos]

    def get_sprite_pos(self, sprite: Sprite):
        pos = (
            int(sprite.hitbox_rect.left / COLLISION_CHUNK_W),
            int(sprite.hitbox_rect.top / COLLISION_CHUNK_H),
        )
        return pos

    def get_sprite_chunk(self, sprite: Sprite):
        pos = self.get_sprite_pos(sprite)
        return self.get_chunk(pos)

    def check_collision(self, hitbox: pygame.FRect):
        for sprite in self:
            if sprite.hitbox_rect.colliderect(hitbox) and sprite.hitbox_rect != hitbox:
                return True

    def update_sprite(self, sprite: MovingSprite) -> bool:
        """
        :return: Whether the sprite collides with anything
        """
        center_chunk = self.get_sprite_pos(sprite)
        chunks = [
            self.get_chunk((i, j))
            for j in range(center_chunk[1] - 1, center_chunk[1] + 2)
            for i in range(center_chunk[0] - 1, center_chunk[0] + 2)
        ]

        colliding_rect = None
        for c_sprite in chain(*chunks):
            if (
                c_sprite.hitbox_rect.colliderect(sprite.hitbox_rect)
                and c_sprite != sprite
            ):
                colliding_rect = c_sprite.hitbox_rect
                distances_rect = colliding_rect

                if isinstance(c_sprite, MovingSprite):
                    # When colliding with another moving sprite, the hitbox to
                    # compare to will also reflect its last-frame's state
                    distances_rect = c_sprite.last_hitbox_rect

                # Compares each point of the last-frame's sprite hitbox to the
                # hitbox the Entity collided with, to check at which
                # direction the collision happened first
                distances = (
                    abs(sprite.last_hitbox_rect.right - distances_rect.left),
                    abs(sprite.last_hitbox_rect.left - distances_rect.right),
                    abs(sprite.last_hitbox_rect.bottom - distances_rect.top),
                    abs(sprite.last_hitbox_rect.top - distances_rect.bottom),
                )

                shortest_distance = min(distances)
                if shortest_distance == distances[0]:
                    sprite.hitbox_rect.right = colliding_rect.left
                elif shortest_distance == distances[1]:
                    sprite.hitbox_rect.left = colliding_rect.right
                elif shortest_distance == distances[2]:
                    sprite.hitbox_rect.bottom = colliding_rect.top
                elif shortest_distance == distances[3]:
                    sprite.hitbox_rect.top = colliding_rect.bottom
        return bool(colliding_rect)
