import os
from dataclasses import dataclass
from types import SimpleNamespace

import pygame

from src.enums import Direction, EntityState
from src.settings import SCALE_FACTOR, CHAR_TILE_SIZE
from src.support import resource_path


@dataclass
class _AniFrames:
    frames: list[pygame.Surface]
    hitbox: pygame.Rect

    def get_frame(self, index: int) -> pygame.Surface:
        return self.frames[int(index % len(self.frames))]

    def get_hitbox(self) -> pygame.Rect:
        return self.hitbox

    def __len__(self) -> int:
        return len(self.frames)


type EntityAsset = dict[EntityState, dict[Direction, _AniFrames]]


class _Hitbox:
    default: pygame.Rect

    _state_exceptions: dict[EntityState, pygame.Rect]
    _direction_exceptions: dict[Direction, pygame.Rect]
    _exceptions: dict[tuple[EntityState, Direction], pygame.Rect]

    def __init__(self, default: pygame.Rect):
        """
        This class can be used to specify custom Sprite hitboxes.

        Use this classes methods to specify exceptions (conditions under which
        a hitbox different to the default one should be used)

        :param default: The default hitbox to use, when no hitbox has been
                        found for a specific state / direction
        """

        self.default = default

        self._state_exceptions = {}
        self._direction_exceptions = {}
        self._exceptions = {}

    def set_direction_exception(
            self, direction: Direction, rect: pygame.Rect
    ) -> None:
        """
        Tell the class, in which direction a hitbox should be used that differs
        from the default one.

        Hitboxes that were stored through this method will be used before any
        hitbox specific to the current Entity state is considered.
        """
        self._direction_exceptions[direction] = rect

    def set_state_exception(
            self, state: EntityState, rect: pygame.Rect
    ) -> None:
        """
        Tell the class, in which state a hitbox should be used that differs
        from the default one.
        """
        self._state_exceptions[state] = rect

    def set_exception(
            self, state: EntityState, direction: Direction, rect: pygame.Rect
    ) -> None:
        """
        Tell the class, in which state a hitbox should be used that differs
        from the default one.

        Hitboxes that were stored through this method will be used before any
        hitbox specific to the current Entity state or direction is considered.
        """
        self._exceptions[(state, direction)] = rect

    def get_hitbox(
            self, state: EntityState, direction: Direction
    ) -> pygame.Rect:
        state_exception = self._state_exceptions.get(state)
        direction_exception = self._direction_exceptions.get(direction)
        exception = self._exceptions.get((state, direction))
        if not exception:
            if not direction_exception:
                if not state_exception:
                    return self.default
                return state_exception
            return direction_exception
        return exception

    def scale_hitboxes(self, factor: float) -> None:
        for item in [self._state_exceptions.values(),
                     self._direction_exceptions.values(),
                     self._exceptions.values(),
                     [self.default]]:
            for hitbox in item:
                hitbox.update(
                    hitbox.left * factor,
                    hitbox.top * factor,
                    hitbox.width * factor,
                    hitbox.height * factor
                )


def state_importer(
        path: str, size: int, state: EntityState, directions: list[Direction],
        hitbox: _Hitbox
) -> dict[Direction, _AniFrames]:

    directions_dict = {}
    full_path = os.path.join(path)
    surf = pygame.image.load(full_path).convert_alpha()

    for row, direction in enumerate(directions):
        frames = []

        for col in range(surf.get_width() // size):
            subsurface = surf.subsurface(
                col * size,
                row * size,
                size,
                size
            )
            subsurface = pygame.transform.scale_by(subsurface, SCALE_FACTOR)
            frames.append(subsurface)

        current_hitbox = hitbox.get_hitbox(state, direction)
        directions_dict[direction] = _AniFrames(
            frames, current_hitbox
        )

    if Direction.LEFT in directions and Direction.RIGHT not in directions:
        frames = []
        for i in range(len(directions_dict[Direction.LEFT])):
            frame = directions_dict[Direction.LEFT].get_frame(i)
            frame = pygame.transform.flip(frame, True, False)
            frames.append(frame)
        hitbox = hitbox.get_hitbox(state, Direction.RIGHT)
        directions_dict[Direction.RIGHT] = _AniFrames(frames, hitbox)
    elif Direction.RIGHT in directions and Direction.LEFT not in directions:
        frames = []
        for i in range(len(directions_dict[Direction.RIGHT])):
            frame = directions_dict[Direction.RIGHT].get_frame(i)
            frame = pygame.transform.flip(frame, True, False)
            frames.append(frame)
        hitbox = hitbox.get_hitbox(state, Direction.LEFT)
        directions_dict[Direction.LEFT] = _AniFrames(frames, hitbox)
    return directions_dict


def entity_importer(
        path: str, size: int, directions: list[Direction],
        hitbox: _Hitbox
) -> dict[EntityState, dict[Direction, _AniFrames]]:
    hitbox.scale_hitboxes(SCALE_FACTOR)
    states = {}
    for folder_path, sub_folders, file_names in os.walk(path):
        for file_name in file_names:
            current_state = EntityState(file_name.split(".")[0])
            states[current_state] = state_importer(
                path=os.path.join(folder_path, file_name),
                size=size,
                state=current_state,
                directions=directions,
                hitbox=hitbox,
            )
    return states


ENTITY_ASSETS = SimpleNamespace()

ENTITY_ASSETS.CHICKEN: EntityAsset | None = None  # type: ignore
ENTITY_ASSETS.COW: EntityAsset | None = None  # type: ignore
ENTITY_ASSETS.RABBIT: EntityAsset | None = None  # type: ignore


def setup_entity_assets():
    chicken_hitbox = _Hitbox(pygame.Rect(1, 11, 11, 3))
    chicken_hitbox.set_direction_exception(
        Direction.LEFT, pygame.Rect(4, 11, 11, 3)
    )

    chicken_asset = entity_importer(
        path=resource_path("images/entities/chicken"),
        size=16,
        directions=[Direction.RIGHT],
        hitbox=chicken_hitbox
    )

    ENTITY_ASSETS.CHICKEN = chicken_asset

    cow_hitbox = _Hitbox(pygame.Rect(6, 25, 16, 4))
    cow_hitbox.set_direction_exception(
        Direction.LEFT, pygame.Rect(10, 25, 16, 4)
    )

    cow_asset = entity_importer(
        path=resource_path("images/entities/cow"),
        size=32,
        directions=[Direction.RIGHT],
        hitbox=cow_hitbox
    )

    ENTITY_ASSETS.COW = cow_asset

    rabbit_hitbox = _Hitbox(pygame.Rect(18, 26, 12, 6))
    rabbit_hitbox.set_direction_exception(
        Direction.LEFT, pygame.Rect(20, 26, 8, 6)
    )
    rabbit_hitbox.set_direction_exception(
        Direction.RIGHT, pygame.Rect(20, 26, 8, 6)
    )
    rabbit_hitbox.set_exception(
        EntityState.AXE, Direction.LEFT, pygame.Rect(24, 26, 8, 6)
    )
    rabbit_hitbox.set_exception(
        EntityState.AXE, Direction.RIGHT, pygame.Rect(16, 26, 8, 6)
    )

    rabbit_asset = entity_importer(
        path=resource_path("images/characters/rabbit"),
        size=CHAR_TILE_SIZE,
        directions=[Direction.DOWN, Direction.UP, Direction.LEFT],
        hitbox=rabbit_hitbox
    )

    ENTITY_ASSETS.RABBIT = rabbit_asset
