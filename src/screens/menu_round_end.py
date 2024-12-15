from collections.abc import Callable

import pygame

from src.enums import GameState
from src.gui.menu.components import Button
from src.gui.menu.general_menu import GeneralMenu
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from src.sprites.entities.player import Player
from src.support import resource_path


class RoundMenu(GeneralMenu):
    SCROLL_AMOUNT = 10
    MAX_SCROLL = 10

    class TextUI:
        img: pygame.Surface = None
        rect: pygame.Rect = None

        def __init__(self, text, rect):
            font = pygame.font.Font(resource_path("font/LycheeSoda.ttf"), size=30)
            self.img = font.render(text, False, "Black")
            self.rect = rect
            self.imgRect = self.img.get_rect(midleft=rect.topleft)
            self.imgRect.y += 10

    def __init__(
        self,
        switch_screen: Callable[[GameState], None],
        player: Player,
        increment_round: Callable[[], None],
        get_round: Callable[[], int],
    ):
        self.player = player
        self.scroll = 0
        self.min_scroll = self.get_min_scroll()
        self.get_round = get_round
        self.title = f"Round {self.get_round()} has ended. You currently have:"
        options = ["continue to next round"]
        size = (400, 400)

        super().__init__(self.title, options, switch_screen, size)
        self.background = pygame.Surface(self.display_surface.get_size())
        self.stats_options = [""]

        self.textUIs = []
        self.increment_round = increment_round

    def reset_menu(self):
        self.increment_round()
        self.background.blit(self.display_surface, (0, 0))
        self.scroll = 0
        self.generate_items()

    def generate_items(self):
        # i'm sorry for my sins of lack of automation. For those who come after, please do better. --Kyle N.
        basicRect = pygame.Rect((0, 0), (400, 50))
        basicRect.top = self.rect.top - 74  # im sorry, this is so scuffed
        basicRect.centerx = self.rect.centerx

        self.textUIs = []

        for index, item in enumerate(list(self.player.inventory)):
            rect = pygame.Rect(basicRect)
            itemName = item.as_user_friendly_string()
            text = itemName + f": {list(self.player.inventory.values())[index]}"
            itemUI = self.TextUI(text, rect)
            self.textUIs.append(itemUI)
            basicRect = basicRect.move(0, 60)

    def get_min_scroll(self):
        return -60 * len(list(self.player.inventory)) + 460

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
        if text == "continue to next round":
            self.switch_screen(GameState.PLAY)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.switch_screen(GameState.PLAY)
                self.scroll = 0
                return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # up scroll
                self.stats_scroll(-self.SCROLL_AMOUNT)

            if event.button == 5:  # down scroll
                self.stats_scroll(self.SCROLL_AMOUNT)

        return False

    def draw_title(self):
        self.title = f"Round {self.get_round() - 1} has ended. You currently have:"
        text_surf = self.font.render(self.title, False, "Black")
        midtop = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20)
        text_rect = text_surf.get_frect(midtop=midtop)

        bg_rect = pygame.Rect((0, 0), (500, 50))
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
            item.imgRect.centery += amount

    def draw_stats(self):
        for item in self.textUIs:
            if item.rect.centery < 52 or item.rect.centery > 584:
                continue

            pygame.draw.rect(self.display_surface, "White", item.rect, 0, 4)
            self.display_surface.blit(item.img, item.imgRect.midleft)

    def draw(self):
        self.display_surface.blit(self.background, (0, 0))
        self.draw_stats()
        self.draw_title()
        self.draw_buttons()
