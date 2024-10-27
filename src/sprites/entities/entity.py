from abc import ABC, abstractmethod

import pygame

from src import settings
from src.enums import Direction, EntityState, Layer
from src.gui.interface import indicators
from src.settings import SCALED_TILE_SIZE
from src.sprites.base import MovingSprite, Sprite
from src.sprites.chunk_system.collision_chunks import CollisionManager
from src.sprites.setup import EntityAsset
from src.support import get_entity_facing_direction, screen_to_tile


class Entity(MovingSprite, ABC):
    frames: dict[str, settings.AniFrames]
    frame_index: int
    _current_ani_frame: list[pygame.Surface] | None

    state: EntityState
    facing_direction: Direction

    direction: pygame.Vector2
    speed: int
    collision_manager: CollisionManager

    def __init__(
        self,
        pos: settings.Coordinate,
        assets: EntityAsset,
        groups: tuple[pygame.sprite.Group, ...],
        collision_manager: CollisionManager,
        z=Layer.MAIN,
    ):
        self.assets = assets

        self._current_ani = None
        self._current_hitbox = None
        self._current_frame = None

        # Because the following three attributes are properties that depend on
        # each other, the first two of them must be set without calling their
        # property setter
        self._frame_index = 0
        self._facing_direction = Direction.RIGHT
        self.state = EntityState.IDLE

        self.focused = False
        self.focused_indicator = None

        super().__init__(
            pos,
            self.assets[self.state][self.facing_direction].get_frame(0),
            groups,
            z=z,
        )

        # movement
        self.direction = pygame.Vector2()
        self.speed = 100
        self.collision_manager = collision_manager
        self.is_colliding = False

        # Axe hitbox, which allows for independent usage of the axe by any
        # entity (player or NPC)
        self.axe_hitbox = pygame.Rect(0, 0, 32, 32)

    def _update_axe_hitbox(self):
        match self.facing_direction:
            case Direction.DOWN:
                self.axe_hitbox.x = self.rect.centerx - 24
                self.axe_hitbox.y = self.rect.centery + 24
            case Direction.UP:
                self.axe_hitbox.x = self.rect.centerx - 8
                self.axe_hitbox.bottom = self.rect.centery + 8
            case Direction.LEFT:
                self.axe_hitbox.right = self.rect.centerx - 16
                self.axe_hitbox.y = self.rect.centery + 8
            case Direction.RIGHT:
                self.axe_hitbox.x = self.rect.centerx + 16
                self.axe_hitbox.y = self.rect.centery + 8

    def update_animation(self):
        self._current_ani = self.assets[self.state][self.facing_direction]

    def update_hitbox(self):
        self._current_hitbox = self._current_ani.get_hitbox()

    def update_frame(self):
        self._current_frame = self._current_ani.get_frame(self.frame_index)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state: EntityState):
        self._state = state
        self.update_animation()
        self.update_hitbox()
        self.update_frame()

    @property
    def facing_direction(self):
        return self._facing_direction

    @facing_direction.setter
    def facing_direction(self, direction: Direction):
        self._facing_direction = direction
        self.update_animation()
        self.update_hitbox()
        self.update_frame()

    @property
    def frame_index(self):
        return self._frame_index

    @frame_index.setter
    def frame_index(self, frame_index: int):
        self._frame_index = frame_index
        self.update_frame()

    def get_state(self):
        if self.direction:
            self.state = EntityState.WALK
        else:
            self.state = EntityState.IDLE

    def get_facing_direction(self):
        self.facing_direction = get_entity_facing_direction(
            self.direction, self.facing_direction
        )
        self._update_axe_hitbox()

    def get_target_pos(self):
        return screen_to_tile(self.hitbox_rect.center)

    def get_tile_pos(self) -> tuple[int, int]:
        return (
            int(self.hitbox_rect.centerx / SCALED_TILE_SIZE),
            int(self.hitbox_rect.centery / SCALED_TILE_SIZE),
        )

    def focus(self):
        self.focused = True
        self.focused_indicator = Sprite(
            (0, 0), indicators.ENTITY_FOCUSED, (self.groups()[0],), Layer.EMOTES
        )

    def unfocus(self):
        self.focused = False
        if self.focused_indicator:
            self.focused_indicator.kill()
            self.focused_indicator = None

    def teleport(self, pos: tuple[float, float]):
        """
        Moves the Entity rect directly to the specified point
        """
        self.rect.update(
            (pos[0] - self.rect.width / 2, pos[1] - self.rect.height / 2),
            self.rect.size,
        )

    @abstractmethod
    def move(self, dt: float):
        pass

    def check_collision(self):
        if self.last_hitbox_rect == self.hitbox_rect:
            self.is_colliding = False
        else:
            self.is_colliding = self.collision_manager.update_sprite(self)

    @abstractmethod
    def animate(self, dt: float):
        """
        Animate the Entity. Child classes should implement method and
        set current image based on self._current_ani_frame
        """
        self.frame_index += 4 * dt

    def _prepare_for_update(self):
        # Updating all attributes necessary for updating the Entity
        self.last_hitbox_rect.update(self.hitbox_rect)
        self.get_state()
        self.get_facing_direction()

    def _do_common_update_ops(self):
        self._prepare_for_update()

        if self.focused_indicator:
            self.focused_indicator.rect.update(
                (
                    self.rect.centerx - self.focused_indicator.rect.width / 2,
                    self.rect.centery - 56 - self.focused_indicator.rect.height / 2,
                ),
                self.focused_indicator.rect.size,
            )

    def update(self, dt: float):
        self._do_common_update_ops()
        self.move(dt)
        self.animate(dt)
        self.image = self._current_frame

    def update_blocked(self, dt):
        """Only used when cutscenes are run, and entities are not meant to move."""
        self._do_common_update_ops()
        self.animate(dt)
        self.image = self._current_frame
