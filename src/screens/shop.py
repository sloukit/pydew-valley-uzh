from collections.abc import Callable
from typing import Any

import pygame  # noqa

from src.enums import GameState, InventoryResource
from src.settings import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.sprites.entities.player import Player
from src.support import get_translated_string, parse_crop_types

# TODO: Refactor this class


class ShopMenu:
    SCROLL_AMOUNT = 10
    MAX_SCROLL = 0

    def __init__(
        self,
        player: Player,
        switch_screen: Callable[[GameState], None],
        font,
        round_config: dict[str, Any],
        frames: dict[str, dict[str, pygame.Surface]],
    ):
        # general setup

        self.buy_text = font.render(get_translated_string("buy one"), False, "Black")
        self.sell_text = font.render(get_translated_string("sell one"), False, "Black")
        self.main_rect = None
        self.player = player
        self.switch_screen = switch_screen
        self.display_surface = pygame.display.get_surface()
        self.font = font
        self.round_config = round_config
        self.item_frames: dict[str, pygame.Surface] = frames["items"]
        self.index = 0
        self.text_surfs = []
        self.img_surfs = []
        self.total_height = 0
        self.scroll = 0
        # options
        self.width = 600
        self.space = 10
        self.padding = 8

        # entries
        self.options: list[InventoryResource] = []
        self.allowed_crops: list[str] = []
        self.min_scroll: int = 0
        self.filter_options()
        self.calculate_min_scroll()
        self.setup()

    def calculate_min_scroll(self):
        self.min_scroll = (
            -(self.font.get_height() + (self.padding * 2) + self.space)
            * len(self.options)
            + 480
        )

    def round_config_changed(self, round_config: dict[str, Any]):
        self.round_config = round_config

        self.filter_options()
        self.calculate_min_scroll()
        self.setup()

    def display_labels(self):
        label = get_translated_string("Welcome to the shop!")
        header1_surf = self.font.render(f"{label} ", False, "Black")
        box_rect = pygame.Rect(
            SCREEN_WIDTH / 2 - self.width / 2,
            50,
            self.width,
            header1_surf.get_height() + (self.padding * 2) + self.space,
        )

        header1_rect = header1_surf.get_frect(midtop=(SCREEN_WIDTH / 2, 45))

        label = get_translated_string("Amount  Value")
        header2_surf = self.font.render(f"{label} ", False, "Black")
        header2_rect = header2_surf.get_frect(midright=(SCREEN_WIDTH / 2 + 300, 95))

        pygame.draw.rect(self.display_surface, "White", box_rect.inflate(10, 10), 0, 4)
        self.display_surface.blit(header1_surf, header1_rect)
        self.display_surface.blit(header2_surf, header2_rect)

        # Amount Value
        label = get_translated_string("Your money:")
        footer_surf = self.font.render(f"{label} ${self.player.money}", False, "Black")
        footer_rect = footer_surf.get_frect(
            midbottom=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20)
        )

        pygame.draw.rect(
            self.display_surface, "White", footer_rect.inflate(10, 10), 0, 4
        )
        self.display_surface.blit(footer_surf, footer_rect)

    def setup(self):
        self.text_surfs = []
        self.img_surfs = []
        self.total_height = 0

        # create the text surfaces
        for item in self.options:
            text = get_translated_string(item.as_user_friendly_string())
            text_surf = self.font.render(text, False, "Black")
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)

            frame_name = item.as_serialised_string()
            img = pygame.transform.scale_by(self.item_frames[frame_name], 0.5)

            self.img_surfs.append(img)

        self.total_height += (len(self.text_surfs) - 1) * self.space

        self.main_rect = pygame.Rect(
            SCREEN_WIDTH / 2 - self.width / 2,
            120,
            self.width,
            # self.total_height,
            SCREEN_HEIGHT - 240,
        )

    def filter_options(self):
        crop_types_list = self.round_config.get("crop_types_list", [])
        self.allowed_crops = parse_crop_types(
            crop_types_list,
            include_base_allowed_crops=True,
            include_crops=True,
            include_seeds=True,
        )

        self.options = []
        for ir in list(self.player.inventory):
            if ir.as_serialised_string() in self.allowed_crops:
                self.options.append(ir)

    def inventory_scroll(self, amount):
        if self.scroll < self.min_scroll and amount < 0:
            return

        if self.scroll > self.MAX_SCROLL and amount > 0:
            return

        self.scroll += amount

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # up scroll
                self.inventory_scroll(-self.SCROLL_AMOUNT)

            if event.button == 5:  # down scroll
                self.inventory_scroll(self.SCROLL_AMOUNT)

            down_limit = (self.index - 8) * -60 + 10
            up_limit = (self.index) * -60 + 10

            if self.scroll < up_limit:
                if event.button == 4:
                    self.index += 1

            if self.scroll > down_limit:
                if event.button == 5:
                    self.index -= 1

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PLAY)
                return True

            elif event.key == pygame.K_SPACE:
                current_item = self.options[self.index]
                if current_item.is_seed():
                    if self.player.money >= current_item.get_worth():
                        # check if the player achieved task "go to the marketplace and buy or sell"
                        # "here it is buy" something"
                        self.player.bought_sold = True
                        self.player.inventory[current_item] += 1
                        self.player.money -= current_item.get_worth()
                else:
                    if self.player.inventory[current_item] > 0:
                        # check if the player achieved task "go to the marketplace and buy or sell"
                        # "here it is sell" something"
                        self.player.bought_sold = True
                        self.player.inventory[current_item] -= 1
                        self.player.money += current_item.get_worth()
                return True

            elif event.key in (pygame.K_DOWN, pygame.K_UP):
                self.index = (
                    self.index
                    + int(event.key == pygame.K_DOWN)
                    - int(event.key == pygame.K_UP)
                ) % len(self.options)
                down_limit = (self.index - 8) * -60 + 10
                up_limit = (self.index) * -60 + 10

                if self.scroll < up_limit:
                    self.inventory_scroll(59)

                if self.scroll > down_limit:
                    self.inventory_scroll(-59)

                if self.index == 0:
                    self.scroll = 0

                if self.index == len(self.options) - 1:
                    self.scroll = -59 * (self.index - 8)

                return True

        return False

    def show_entry(
        self,
        text_surf: pygame.Surface,
        img_surf: pygame.Surface,
        amount: int,
        value: int,
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

        # img (icon)
        img_rect = img_surf.get_frect(
            midleft=(self.main_rect.left + 10, bg_rect.centery)
        )
        self.display_surface.blit(img_surf, img_rect)

        # text
        text_rect = text_surf.get_frect(
            midleft=(self.main_rect.left + 50, bg_rect.centery + 5)
        )
        self.display_surface.blit(text_surf, text_rect)

        # amount
        amount_surf = self.font.render(str(amount), False, "Black")
        amount_rect = amount_surf.get_frect(
            midright=(self.main_rect.right - 120, bg_rect.centery + 5)
        )
        self.display_surface.blit(amount_surf, amount_rect)

        # value
        value_surf = self.font.render(f"${str(value)}", False, "Black")
        value_rect = value_surf.get_frect(
            midright=(self.main_rect.right - 20, bg_rect.centery + 5)
        )
        self.display_surface.blit(value_surf, value_rect)

        # selected
        if index == text_index:
            pygame.draw.rect(self.display_surface, "black", bg_rect, 4, 4)
            pos_rect = self.buy_text.get_frect(
                midleft=(self.main_rect.left + 270, bg_rect.centery + 5)
            )
            surf = self.buy_text if self.options[index].is_seed() else self.sell_text
            self.display_surface.blit(surf, pos_rect)

    def update(self, dt: int):
        self.display_labels()

        for text_index, text_surf in enumerate(self.text_surfs):
            top = (
                +self.scroll
                + self.main_rect.top
                + text_index
                * (text_surf.get_height() + (self.padding * 2) + self.space)
            )
            if top > self.main_rect.bottom:
                continue
            if top < self.main_rect.top:
                continue
            img = self.img_surfs[text_index]
            item = self.options[text_index]
            amount = self.player.inventory[item]
            value = item.get_worth()
            self.show_entry(text_surf, img, amount, value, top, self.index, text_index)
