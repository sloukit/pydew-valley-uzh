from collections.abc import Callable
from typing import Any

import pygame

from src.enums import GameState
from src.gui.menu.components import Button
from src.gui.menu.general_menu import GeneralMenu
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.sprites.entities.player import Player
from src.support import get_translated_string as _, parse_crop_types


class RoundMenu(GeneralMenu):
    SCROLL_AMOUNT = 10
    MAX_SCROLL = -30

    class TextUI:
        img: pygame.Surface = None
        rect: pygame.Rect = None

        def __init__(self, font: pygame.Font, text: str, value: str, icon: pygame.Surface, rect: pygame.Rect) -> None:
            self.img = pygame.Surface(rect.size, flags=pygame.SRCALPHA)
            self.img.fill(pygame.Color(0, 0, 0, 0))
            pygame.draw.rect(self.img, "White", (0, 0, rect.width, rect.height), 0, 4)

            # crop icon
            self.img.blit(icon, icon.get_rect().move(10, rect.height // 2 - icon.height // 2))

            # crop name
            label = font.render(text, False, "Black")
            self.img.blit(label, label.get_rect().move(50, rect.height // 2 - label.height // 2))

            # crop amount
            val = font.render(value, False, "Black")
            val_rect = val.get_rect().move(
                rect.width - val.width - 10,
                rect.height // 2 - val.height // 2
            )
            self.img.blit(val, val_rect)

            self.rect = rect

    def __init__(
        self,
        switch_screen: Callable[[GameState], None],
        player: Player,
        increment_round: Callable[[], None],
        get_round: Callable[[], int],
        round_config: dict[str, Any],
        frames: dict[str, dict[str, pygame.Surface]],
    ):
        self.player = player
        self.textUIs: list = []
        self.min_scroll = self.get_min_scroll()
        self.scroll = 0
        self.get_round = get_round
        # note that this is config from previous round (the one that has just ended)
        self.round_config = round_config
        self.item_frames: dict[str, pygame.Surface] = frames["items"]
        self.title = ""
        options = [_("continue to next round")]
        size = (650, 400)

        self.allowed_crops = []
        super().__init__(self.title, options, switch_screen, size)
        self.background = pygame.Surface(self.display_surface.get_size())
        self.stats_options = [""]

        self.increment_round = increment_round

    def reset_menu(self):
        self.increment_round()
        self.background.blit(self.display_surface, (0, 0))
        self.generate_items()
        self.scroll = 0

    def round_config_changed(self, round_config: dict[str, Any]):
        self.round_config = round_config
        self.filter_items()

    def filter_items(self):
        crop_types_list = self.round_config.get("crop_types_list", [])
        self.allowed_crops = parse_crop_types(
            crop_types_list,
            include_base_allowed_crops=True,
            include_crops=True,
            include_seeds=True,
        )

    def generate_items(self):
        # i'm sorry for my sins of lack of automation. For those who come after, please do better. --Kyle N.
        basicRect = pygame.Rect((0, 0), (400, 50))
        basicRect.top = self.rect.top - 74  # im sorry, this is so scuffed
        basicRect.centerx = self.rect.centerx

        self.textUIs = []
        values = list(self.player.inventory.values())
        for index, item in enumerate(list(self.player.inventory)):
            if item.as_serialised_string() not in self.allowed_crops:
                continue
            rect = pygame.Rect(basicRect)
            itemName = _(item.as_user_friendly_string())
            frame_name = item.as_serialised_string()
            icon = self.item_frames[frame_name]
            icon = pygame.transform.scale_by(icon, 0.5)

            itemUI = self.TextUI(self.font, itemName, str(values[index]), icon, rect)
            self.textUIs.append(itemUI)
            basicRect = basicRect.move(0, 60)

        self.min_scroll = self.get_min_scroll()

    def get_min_scroll(self):
        return -60 * len(self.textUIs) + 460

    def button_setup(self):
        # button setup
        button_width = 400
        button_height = 50
        size = (button_width, button_height)
        space = 10
        top_margin = 400

        # generic button rect
        generic_button_rect = pygame.Rect((0, 0), size)
        generic_button_rect.top = self.rect.top + top_margin
        generic_button_rect.centerx = self.rect.centerx

        # create buttons
        for title in self.options:
            rect = generic_button_rect
            button = Button(title, rect, self.font)
            self.buttons.append(button)
            generic_button_rect = rect.move(0, button_height + space)

    def button_action(self, text: str):
        if text == _("continue to next round"):
            self.switch_screen(GameState.PLAY)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.switch_screen(GameState.PLAY)
                self.scroll = 0
                return True
            elif event.key == pygame.K_UP:
                self.stats_scroll(-self.SCROLL_AMOUNT)
            elif event.key == pygame.K_DOWN:
                self.stats_scroll(self.SCROLL_AMOUNT)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # up scroll
                self.stats_scroll(-self.SCROLL_AMOUNT)

            if event.button == 5:  # down scroll
                self.stats_scroll(self.SCROLL_AMOUNT)

        return False

    def draw_title(self):
        self.title = _("Round %d has ended. You currently have $%d, and:") % (self.get_round() - 1, self.player.money)
        text_surf = self.font.render(self.title, False, "Black")
        midtop = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20)
        text_rect = text_surf.get_frect(midtop=midtop)

        bg_rect = pygame.Rect((0, 0), (650, 50))
        bg_rect.center = text_rect.center

        pygame.draw.rect(self.display_surface, "White", bg_rect, 0, 4)
        self.display_surface.blit(text_surf, text_rect)

    def stats_scroll(self, amount):
        if self.scroll < self.min_scroll and amount < 0:
            return
        if self.scroll > self.MAX_SCROLL and amount > 0:
            return
        self.scroll += amount
        for item in self.textUIs:
            item.rect.centery += amount

    def draw_stats(self):
        for item in self.textUIs:
            if item.rect.centery < 52 or item.rect.centery > 540:
                continue

            self.display_surface.blit(item.img, item.rect.midleft)

    def draw(self):
        self.draw_stats()
        self.draw_title()
        self.draw_buttons()
