from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from typing import Type, TypeVar

from src.sprites.base import MovingSprite, Sprite
from src.utils import DefaultCallableDict


class SpriteChunk:
    _pos: tuple[int, int]
    _size: tuple[float, float]
    _on_sprite_exit_chunk = Callable[[Sprite], None]

    _sprite_list: list[Sprite]
    _persistent_sprite_list: list[Sprite]
    _moving_sprite_list: list[Sprite]

    def __init__(
        self,
        pos: tuple[int, int],
        size: tuple[float, float],
        on_sprite_exit_chunk: Callable[[Sprite], None],
    ):
        self._pos = pos
        self._size = size
        self._on_sprite_exit_chunk = on_sprite_exit_chunk

        self._sprites = []
        self._persistent_sprites = []
        self._moving_sprites = []

    def __bool__(self):
        return bool(self._sprites)

    def __contains__(self, sprite: Sprite):
        if sprite in self._sprites:
            return True

    def __iter__(self):
        return self.sprites()

    def __len__(self):
        return len(self._sprites)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._pos} / {len(self)} sprites)>"

    def sprites(self) -> Generator[Sprite, None, None]:
        for sprite in self._sprites:
            yield sprite

    def add(self, sprite: Sprite):
        if sprite not in self._sprites:
            if isinstance(sprite, MovingSprite):
                self._moving_sprites.append(sprite)
            self._sprites.append(sprite)

    def add_persistent(self, sprite: Sprite):
        self.add(sprite)
        if sprite not in self._persistent_sprites:
            self._persistent_sprites.append(sprite)

    def remove(self, sprite: Sprite) -> bool:
        """:return: Whether the removed sprite was a persistent sprite"""
        ret = False
        if sprite in self._sprites:
            self._sprites.remove(sprite)
        if sprite in self._persistent_sprites:
            self._persistent_sprites.remove(sprite)
            ret = True
        if sprite in self._moving_sprites:
            self._moving_sprites.remove(sprite)
        return ret

    def sprite_in_chunk(self, sprite: Sprite) -> bool:
        return (
            int(sprite.rect.left / self._size[0]) == self._pos[0]
            and int(sprite.rect.top / self._size[1]) == self._pos[1]
        )

    def update(self, *args, **kwargs):
        sprite_list = []
        for sprite in self._moving_sprites:
            if not self.sprite_in_chunk(sprite):
                sprite_list.append(sprite)

        for sprite in sprite_list:
            self._on_sprite_exit_chunk(sprite)

    def empty(self):
        for sprite in set(self._sprites).symmetric_difference(self._persistent_sprites):
            self.remove(sprite)

    def empty_persistent(self):
        for sprite in self._sprites:
            self.remove(sprite)


_CT = TypeVar("_CT", bound=SpriteChunk)


class SpriteLayer:
    _chunk_size: tuple[float, float]
    _chunks: dict[tuple[int, int], _CT]

    def __init__(self, chunk_size: tuple[float, float], chunk_type: Type[_CT]):
        self._chunk_size = chunk_size
        self._chunks = DefaultCallableDict(
            lambda x: chunk_type(x, self._chunk_size, self.on_sprite_exit_chunk)
        )

    def __bool__(self):
        return next(self.sprites(), False)

    def __contains__(self, sprite: Sprite):
        for chunk in self._chunks.values():
            if sprite in chunk:
                return True

    def __iter__(self):
        return self.sprites()

    def __len__(self):
        return sum(len(chunk) for chunk in self._chunks.values())

    def __repr__(self):
        return f"<{self.__class__.__name__}({len(self)} sprites)>"

    def all_chunks(self) -> list[_CT]:
        # convert to list to allow the dictionary to change in size during iteration
        return list(self._chunks.values())

    def sprites(self) -> Generator[Sprite, None, None]:
        for chunk in self.all_chunks():
            for sprite in chunk:
                yield sprite

    def add(self, sprite: Sprite):
        self.get_sprite_chunk(sprite).add(sprite)

    def add_persistent(self, sprite: Sprite):
        self.get_sprite_chunk(sprite).add_persistent(sprite)

    def update(self, dt: float):
        for chunk in self.all_chunks():
            chunk.update(dt)

    def empty(self):
        for chunk in self.all_chunks():
            chunk.empty()

    def empty_persistent(self):
        for chunk in self.all_chunks():
            chunk.empty_persistent()

    @abstractmethod
    def on_sprite_exit_chunk(self, sprite: Sprite):
        pass

    def get_chunk(self, pos: tuple[int, int]):
        return self._chunks[pos]

    def get_sprite_chunk(self, sprite: Sprite):
        pos = (
            int(sprite.rect.left / self._chunk_size[0]),
            int(sprite.rect.top / self._chunk_size[1]),
        )
        return self.get_chunk(pos)


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class SpriteManager(ABC):
    _containers: dict[_KT, _VT]

    @abstractmethod
    def __init__(self):
        pass

    def __bool__(self):
        return next(self.sprites(), False)

    def __contains__(self, sprite: Sprite):
        for container in self._containers.values():
            if sprite in container:
                return True

    def __iter__(self):
        return self.sprites()

    def __len__(self):
        return sum(len(container) for container in self._containers.values())

    def __repr__(self):
        return f"<{self.__class__.__name__}({len(self)} sprites)>"

    def all_containers(self) -> list[_VT]:
        # convert to list to allow the dictionary to change in size during iteration
        return list(self._containers.values())

    def sprites(self) -> Generator[Sprite, None, None]:
        for container in self.all_containers():
            for sprite in container:
                yield sprite

    @abstractmethod
    def add(self, *sprites: Sprite):
        pass

    @abstractmethod
    def add_persistent(self, *sprites: Sprite):
        pass

    @abstractmethod
    def remove(self, *sprites: Sprite):
        pass

    def update(self, *args, **kwargs):
        for container in self.all_containers():
            container.update(*args, **kwargs)

    def empty(self):
        for container in self.all_containers():
            container.empty()

    def empty_persistent(self):
        for container in self.all_containers():
            container.empty_persistent()
