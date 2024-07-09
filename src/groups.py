from .settings import SCREEN_WIDTH, SCREEN_HEIGHT, LAYERS
import pygame
from pygame import Vector2 as vector


class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = vector()
        self.cam_surf = self.display_surface.copy()

    def draw(self, target_pos):
        self.offset.x = - (target_pos[0] - SCREEN_WIDTH//2)
        self.offset.y = - (target_pos[1] - SCREEN_HEIGHT//2)

        for layer in LAYERS.values():

            for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
                if sprite.z == layer:
                    self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)
                
                if sprite.name is not None:
                    rect = sprite.rect.copy()
                    rect.topleft += self.offset
                    pygame.draw.rect(self.display_surface, 'red', rect, 1)          
