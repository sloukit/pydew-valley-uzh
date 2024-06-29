from .settings import *


class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2()
        self.cam_surf = pygame.Surface(self.display_surface.get_size())

    def draw(self, target_pos):
        self.offset.x = -(target_pos[0] - SCREEN_WIDTH / 2)
        self.offset.y = -(target_pos[1] - SCREEN_HEIGHT / 2)

        for layer in LAYERS.values():

            for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
                if sprite.z == layer:
                    self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)
