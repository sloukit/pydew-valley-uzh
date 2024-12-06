from collections.abc import Callable

import pygame  # noqa

from src.enums import GameState
from src.settings import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.sprites.entities.player import Player

# TODO: Refactor this class


class ShopMenu:
    def __init__(
        self, player: Player, switch_screen: Callable[[GameState], None], font
    ):
        # general setup

        self.buy_text = font.render("buy", False, "Black")
        self.sell_text = font.render("sell", False, "Black")
        self.main_rect = None
        self.menu_top = None
        self.player = player
        self.switch_screen = switch_screen
        self.display_surface = pygame.display.get_surface()
        self.font = font
        self.index = 0
        self.text_surfs = []
        self.total_height = 0

        # options
        self.width = 400
        self.space = 10
        self.padding = 8

        # entries
        self.options = list(self.player.inventory)
        self.setup()

    def display_money(self):
        text_surf = self.font.render(f"${self.player.money}", False, "Black")
        text_rect = text_surf.get_frect(
            midbottom=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20)
        )

        pygame.draw.rect(self.display_surface, "White", text_rect.inflate(10, 10), 0, 4)
        self.display_surface.blit(text_surf, text_rect)

    def setup(self):
        # create the text surfaces
        for item in self.options:
            text = item.as_serialised_string()
            text_surf = self.font.render(text, False, "Black")
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)

        self.total_height += (len(self.text_surfs) - 1) * self.space

        self.menu_top = SCREEN_HEIGHT / 2 - self.total_height / 2
        self.main_rect = pygame.Rect(
            SCREEN_WIDTH / 2 - self.width / 2,
            self.menu_top,
            self.width,
            self.total_height,
        )

        # buy / sell text surface

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PLAY)
                return True

            elif event.key == pygame.K_SPACE:
                current_item = self.options[self.index]
                if current_item.is_seed():
                    if self.player.money >= current_item.get_worth():
                        self.player.inventory[current_item] += 1
                        self.player.money -= current_item.get_worth()

                else:
                    if self.player.inventory[current_item] > 0:
                        self.player.inventory[current_item] -= 1
                        self.player.money += current_item.get_worth() // 2
                return True

            elif event.key in (pygame.K_DOWN, pygame.K_UP):
                self.index = (
                    self.index
                    + int(event.key == pygame.K_DOWN)
                    - int(event.key == pygame.K_UP)
                ) % len(self.options)
                return True

        return False

    def show_entry(
        self,
        text_surf: pygame.Surface,
        amount: int,
        top: int,
        index: int,
        text_index: int,
    ):
        # background
        bg_rect = pygame.Rect(
            self.main_rect.left,
            top,
            self.width,
            text_surf.get_height() + (self.padding * 2),
        )
        pygame.draw.rect(self.display_surface, "White", bg_rect, 0, 4)

        # text
        text_rect = text_surf.get_frect(
            midleft=(self.main_rect.left + 20, bg_rect.centery)
        )
        self.display_surface.blit(text_surf, text_rect)

        # amount
        amount_surf = self.font.render(str(amount), False, "Black")
        amount_rect = amount_surf.get_frect(
            midright=(self.main_rect.right - 20, bg_rect.centery)
        )
        self.display_surface.blit(amount_surf, amount_rect)

        # selected
        if index == text_index:
            pygame.draw.rect(self.display_surface, "black", bg_rect, 4, 4)
            pos_rect = self.buy_text.get_frect(
                midleft=(self.main_rect.left + 250, bg_rect.centery)
            )
            surf = self.buy_text if self.options[index].is_seed() else self.sell_text
            self.display_surface.blit(surf, pos_rect)

    def update(self, dt: int):
        self.display_money()

        for text_index, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + text_index * (
                text_surf.get_height() + (self.padding * 2) + self.space
            )
            amount_list = list(self.player.inventory.values())
            amount = amount_list[text_index]
            self.show_entry(text_surf, amount, top, self.index, text_index)
