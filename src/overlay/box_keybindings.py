import pygame

from src.settings import OVERLAY_POSITIONS
from src.sprites.entities.player import Player
from src.support import import_font, import_image
from src.sprites.base import Sprite
from src.support import get_translated_string as _
from src.gui.interface.dialog import TextBox



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

class BoxKeybindings:

    def __init__(self):
        self.info = []
        self.visible = False
        self.pos = OVERLAY_POSITIONS["box_info"]
        self.image = import_image("images/ui/KeyBindUI_Placeholder.png").convert_alpha()
        self.font = import_font(20, "font/LycheeSoda.ttf")
        self.box_keybindings_rect = pygame.Rect(
            self.pos[0],
            self.pos[1],
            self.image.get_width(),
            self.image.get_height(),
        )
        self.color = (255, 255, 255)
        self.padding = 8

    def prepare_info(self) -> list:
        text = _("box info space")
        text_surf = self.font.render(text, False, "Black")
        self.info.append(text_surf)

    def toggle_visibility(self):
        self.visible = not self.visible

    def draw(self, screen):
        if not self.visible:
            return

        screen.blit(self.image, self.box_keybindings_rect)

        for info_surf in self.info:
            bg_rect = pygame.Rect(
                self.box_keybindings_rect.left,
                self.box_keybindings_rect.top,
                self.box_keybindings_rect.width,
                info_surf.get_height() + (self.padding * 2),
            )
            text_rect = info_surf.get_frect(
                midleft=(self.box_keybindings_rect.left + 50, bg_rect.centery + 5)
            )
            screen.blit(info_surf, text_rect)



