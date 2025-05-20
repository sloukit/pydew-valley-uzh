import pygame

from src.fblitter import FBLITTER
from src.settings import OVERLAY_POSITIONS
from src.sprites.entities.player import Player
from src.support import import_font


class Money:
    def __init__(self, entity: Player):
        # setup
        self.display_surface = pygame.display.get_surface()
        self.player = entity

        # dimensions
        self.left = 20
        self.top = 20

        width, height = 100, 50
        self.font = import_font(40, "font/LycheeSoda.ttf")

        self.rect = pygame.Rect(self.left, self.top, width, height)

        self.rect.bottomright = OVERLAY_POSITIONS["money"]

    def display(self):
        # colors connected to player state
        black = "Black"
        gray = "Gray"
        foreground_color = gray if self.player.blocked else black

        # rects and surfs
        pad_y = 2

        money_surf = self.font.render(f"${self.player.money}", False, foreground_color)
        money_rect = money_surf.get_frect(
            midright=(self.rect.right - 20, self.rect.centery + pad_y)
        )

        # display
        FBLITTER.draw_rect("white", self.rect, 0, 4)
        FBLITTER.draw_rect(foreground_color, self.rect, 4, 4)
        FBLITTER.schedule_blit(money_surf, money_rect)
