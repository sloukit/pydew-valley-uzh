import pygame

from src.settings import OVERLAY_POSITIONS
from src.sprites.entities.player import Player
from src.support import import_font

from src.support import get_translated_string as _

class BoxKeybindingsLabel:
    def __init__(self, entity: Player):
        # setup
        self.display_surface = pygame.display.get_surface()
        self.player = entity

        # dimensions
        self.left = 20
        self.top = 20

        width, height = 330, 50
        self.font = import_font(23, "font/LycheeSoda.ttf")

        self.rect = pygame.Rect(self.left, self.top, width, height)

        self.rect.topleft = OVERLAY_POSITIONS["box_info_label"]

    def display(self):
        # colors connected to player state
        black = "Black"
        gray = "Gray"
        foreground_color = gray if self.player.blocked else black

        # rects and surfs
        pad_y = 2

        box_keybindings_label_surf = self.font.render(f"{_('box info label')}", False, foreground_color)
        box_keybindings_label_rect = box_keybindings_label_surf.get_frect(
            midright=(self.rect.right - 20, self.rect.centery + pad_y)
        )

        # display
        pygame.draw.rect(self.display_surface, "White", self.rect, 0, 4)
        pygame.draw.rect(self.display_surface, foreground_color, self.rect, 4, 4)
        self.display_surface.blit(box_keybindings_label_surf, box_keybindings_label_rect)
