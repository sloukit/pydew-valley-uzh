import pygame

from src.settings import OVERLAY_POSITIONS
from src.support import import_font


class FPS:
    def __init__(self, clock: pygame.time.Clock):
        # setup
        self.display_surface = pygame.display.get_surface()
        self.clock = clock

        # dimensions
        self.left = 20
        self.top = 20

        width, height = 180, 50
        self.font = import_font(40, "font/LycheeSoda.ttf")

        self.rect = pygame.Rect(self.left, self.top, width, height)

        self.rect.bottomright = OVERLAY_POSITIONS["FPS"]

    def display(self):
        # get FPS
        fps = self.clock.get_fps()

        # rects and surfs
        pad_y = 2

        label_surf = self.font.render("FPS:", False, "Black")
        label_rect = label_surf.get_frect(
            midleft=(self.rect.left + 20, self.rect.centery + pad_y)
        )

        fps_surf = self.font.render(f"{fps:5.1f}", False, "Black")
        fps_rect = fps_surf.get_frect(
            midright=(self.rect.right - 20, self.rect.centery + pad_y)
        )

        # display
        pygame.draw.rect(self.display_surface, "White", self.rect, 0, 4)
        pygame.draw.rect(self.display_surface, "Black", self.rect, 4, 4)
        self.display_surface.blit(label_surf, label_rect)
        self.display_surface.blit(fps_surf, fps_rect)
