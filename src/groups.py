import pygame
from src.settings import LAYERS, SCREEN_WIDTH, SCREEN_HEIGHT, Coordinate
from src.npc.dialog import TextBox


# TODO : we could replace this with pygame.sprite.LayeredUpdates, as that
# is a subclass of pygame.sprite.Group that natively supports layers


class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2()
        self.cam_surf = pygame.Surface(self.display_surface.get_size())

    def draw(self, target_pos: Coordinate):
        self.offset.x = -(target_pos[0] - SCREEN_WIDTH / 2)
        self.offset.y = -(target_pos[1] - SCREEN_HEIGHT / 2)

        for layer in LAYERS.values():

            for sprite in sorted(
                    self.sprites(),
                    key=lambda spr: spr.rect.centery):
                if sprite.z == layer:
                    self.display_surface.blit(
                        sprite.image,
                        sprite.rect.topleft + (
                            self.offset
                            if not isinstance(sprite, TextBox)
                            else (0, 0)
                        ))
