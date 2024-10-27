import pygame


class PersistentSpriteGroup(pygame.sprite.Group):
    _persistent_sprites: list[pygame.sprite.Sprite]

    def __init__(self, *sprites):
        """
        This Group subclass allows certain Sprites to be added as persistent
        Sprites, which will not be removed when calling Group.empty.
        When needing to remove all Sprites, including persistent Sprites, you
        should call PersistentSpriteGroup.empty_persistent.
        """
        super().__init__(*sprites)
        self._persistent_sprites = []

    def add_persistent(self, *sprites: pygame.sprite.Sprite):
        """
        Add a persistent Sprite. This Sprite will not be removed
        from the Group when Group.empty is called.
        """
        super().add(*sprites)
        self._persistent_sprites.extend(sprites)

    def empty(self):
        super().empty()
        self.add(*self._persistent_sprites)

    def empty_persistent(self):
        """
        Remove all sprites, including persistent Sprites.
        """
        super().empty()
