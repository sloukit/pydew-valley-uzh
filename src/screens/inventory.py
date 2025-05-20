import pygame  # noqa

from src.support import get_translated_string, parse_crop_types
from src.events import SET_CURSOR, post_event
from src.gui.menu.abstract_menu import AbstractMenu
from src.enums import (
    FarmingTool,
    InventoryResource,
    GameState,
    StudyGroup,
    SeedType,
    CustomCursor,
)
from src.gui.menu.components import Button, ImageButton
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from itertools import chain
from operator import itemgetter
from typing import Callable, Any
from src.controls import Controls


class _IMButton(ImageButton):
    def __init__(self, content: pygame.Surface, rect: pygame.Rect, name: str):
        super().__init__(content, rect)
        self._name = name

    @property
    def text(self):
        return self._name


_EQUIP_BTN_CHECKMARK_FRECT_KWARGS = ({"bottomright": (64, 64)}, {"bottomleft": (0, 64)})


class _EquipButton(_IMButton):
    _CHECKMARK: pygame.Surface | None = None
    _get_checkmark_rect: Callable[[dict[str, Any]], pygame.FRect] | None = None

    @classmethod
    def set_checkmark_surf(cls, surf: pygame.Surface):
        cls._CHECKMARK = surf
        cls._get_checkmark_rect = surf.get_frect

    def __prepare_contents(self, draw_checkmark_to_left: bool):
        img_to_calculate = self._contents[0]
        surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        img_rect = img_to_calculate.get_frect(center=(32, 32))
        blit_list = [
            (img_to_calculate, img_rect),
            (
                self._CHECKMARK,
                self._get_checkmark_rect(
                    **_EQUIP_BTN_CHECKMARK_FRECT_KWARGS[draw_checkmark_to_left]
                ),
            ),
        ]
        surf.fblits(blit_list)
        self._contents[1] = surf

    def __init__(
        self,
        content: pygame.Surface,
        rect: pygame.Rect,
        name: str,
        selected: bool = False,
        draw_checkmark_to_left: bool = False,
    ):
        self._contents = [content, None]
        self.__prepare_contents(draw_checkmark_to_left)
        super().__init__(self._contents[selected], rect, name)
        self._selected = selected

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, val: bool):
        self.content = self._contents[val]
        self._content_rect = self.content.get_frect(center=self.rect.center)
        self._selected = val


def prepare_checkmark_for_buttons(surf: pygame.Surface):
    _EquipButton.set_checkmark_surf(surf)


_SPACING_BETWEEN_ROWS = 20
_TOP_MARGIN = 200
_LEFT_MARGIN = 40
_BUTTON_SIZE = (80, 80)

_AVAILABLE_TOOLS = ("axe", "hoe", "water")
_get_resource_count = itemgetter(1)


class InventoryMenu(AbstractMenu):
    _FT_TO_OVERLAY_IMG = {
        FarmingTool.AXE: "axe",
        FarmingTool.HOE: "hoe",
        FarmingTool.WATERING_CAN: "water",
    }

    def __init__(
        self,
        player,
        frames: dict,
        switch_screen: Callable,
        assign_tool: Callable,
        assign_seed: Callable,
        round_config: dict[str, Any],
    ):
        super().__init__(get_translated_string("Inventory"), (SCREEN_WIDTH, 800))
        self.player = player
        self._inventory = player.inventory
        self._av_tools = _AVAILABLE_TOOLS
        self.switch_screen = switch_screen
        self.assign_tool = assign_tool
        self.assign_seed = assign_seed
        self.round_config = round_config
        self.item_frames = frames["items"]
        self.object_frames = frames["level"]["objects"]
        self.cosmetic_frames = frames["cosmetics"]
        # Splitting this into three lists, because
        # the inventory's content can get updated with new resources,
        # and if tools are progressively handed over to the player,
        # the same requirement might appear for tools and personal items
        self._assignable_irs = set()
        self._inv_buttons = []
        self._ft_buttons = []
        self._special_btns = []
        self.allowed_crops = []
        self.button_setup(player)
        self.sections_titles_setup()

    def sections_titles_setup(self) -> None:
        # show Equipment column only if feature "inventory_goggles" is enabled
        if self.player.round_config.get("inventory_goggles", False):
            self.SECTION_TITLES = (
                get_translated_string("Resources"),
                get_translated_string("Tools"),
                get_translated_string("Equipment"),
            )
        else:
            self.SECTION_TITLES = (
                get_translated_string("Resources"),
                get_translated_string("Tools"),
            )

    def _prepare_img_for_ir_button(self, ir: InventoryResource, count: int):
        btn_name = ir.as_serialised_string()
        img = self.item_frames[btn_name]
        calc_rect = img.get_frect(center=(32, 32))
        calc_img = pygame.Surface((64, 64), pygame.SRCALPHA)
        amount = self.font.render(str(count), False, "black")
        blit_list = ((img, calc_rect), (amount, amount.get_frect(bottomright=(64, 64))))
        calc_img.fblits(blit_list)  # faster than doing two separate blits
        return calc_img, btn_name

    def _is_crop_enabled(self, inventory: tuple[InventoryResource, int]) -> bool:
        ir, count = inventory
        return ir.as_serialised_string() in self.allowed_crops

    def round_config_changed(self, round_config: dict[str, Any]) -> None:
        self.round_config = round_config
        crop_types_list = self.round_config.get("crop_types_list", [])

        self.allowed_crops = parse_crop_types(
            crop_types_list,
            include_base_allowed_crops=True,
            include_crops=True,
            include_seeds=True,
        )

    def _inventory_part_btn_setup(self, player, button_size: tuple[int, int]):
        # Portion of the menu to allow the player to see
        # how many of each resource they gathered,
        # and possibly assign them as their current seed
        # (if the selected one is a seed).
        generic_rect = pygame.Rect((0, 0), button_size)
        available_width_for_btns = self.size[0] * 2 // 3
        btns_per_line = available_width_for_btns // button_size[0]
        x_spacing = (available_width_for_btns % button_size[0]) // max(
            1, btns_per_line - 1
        )
        for button_no, (ir, count) in enumerate(
            filter(
                self._is_crop_enabled,
                filter(_get_resource_count, self._inventory.items()),
            )
        ):
            calc_img, btn_name = self._prepare_img_for_ir_button(ir, count)
            row, column = divmod(button_no, 6)  # , _ ,
            btn_rect = generic_rect.copy()
            btn_rect.x = _LEFT_MARGIN + button_size[0] * column + x_spacing * column
            btn_rect.y = _TOP_MARGIN + (button_size[1] + _SPACING_BETWEEN_ROWS) * row
            if ir.is_seed():
                # Keep track of equip buttons so we can toggle whether they display
                # a checkmark when equipped
                self._assignable_irs.add(btn_name)
                # , _ ,
                seed = SeedType.from_inventory_resource(ir).as_fts()
                yield _EquipButton(
                    calc_img, btn_rect, btn_name, player.current_seed == seed, True
                )
            else:
                yield _IMButton(calc_img, btn_rect, btn_name)

    def _ft_btn_setup(self, player, button_size: tuple[int, int]):
        # Portion of the menu to allow the player to select their current tool.
        rect = pygame.Rect((0, 0), button_size)
        rect.centerx = self.rect.width / 2
        for index, tool in enumerate(self._av_tools):
            img = self.item_frames[tool]
            calc_img = pygame.Surface((64, 64), pygame.SRCALPHA)
            calc_img.blit(img, img.get_frect(center=(32, 32)))
            btn_rect = rect.copy()
            btn_rect.y = _TOP_MARGIN + (button_size[1] + _SPACING_BETWEEN_ROWS) * index
            yield _EquipButton(
                calc_img,
                btn_rect,
                tool,
                player.current_tool.as_serialised_string() == tool,
            )

    def _special_btn_setup(self, player, button_size: tuple[int, int]):
        # Part of the menu for items such as the goggles, the hat, etc.

        # Check which items should be listed in this section
        buttons_to_display = []
        if player.has_goggles is not None:
            buttons_to_display.append("goggles")
        match player.study_group:
            # No items are shown if the player is not in a group yet (StudyGroup.NO_GROUP)
            case StudyGroup.INGROUP:
                buttons_to_display.extend({"hat", "necklace"})
            case StudyGroup.OUTGROUP:
                buttons_to_display.append("horn")

        # Should the player have absolutely no cosmetics on themselves
        # whatsoever, show only one button with "No Equipment" on it
        # and stop yielding buttons
        if not buttons_to_display:
            text_rect = self.font.render(
                get_translated_string("No equipment"), False, "black"
            ).get_rect(centerx=self.rect.width * 3 / 4, centery=self.rect.centery)
            yield Button(get_translated_string("No equipment"), text_rect, self.font)
            return

        generic_rect = pygame.Rect(0, 0, *button_size)
        generic_rect.centerx = self.rect.width * 3 / 4
        for i, btn_name in enumerate(buttons_to_display):
            rect = generic_rect.copy()
            rect.y = _TOP_MARGIN + (button_size[1] + _SPACING_BETWEEN_ROWS) * i
            if btn_name == "goggles":
                yield _EquipButton(
                    self.cosmetic_frames["goggles"], rect, btn_name, player.has_goggles
                )
                continue
            yield _IMButton(self.cosmetic_frames[btn_name], rect, btn_name)

    def button_action(self, text):
        if text in self._av_tools:
            self.assign_tool(text)
            for btn in self._ft_buttons:
                btn.selected = btn.text == text
        if "seed" in text:
            self.assign_seed(text)
            if text in self._assignable_irs:
                for btn in filter(
                    lambda button: button.text in self._assignable_irs,
                    self._inv_buttons,
                ):
                    btn.selected = btn.text == text
        if text == "goggles":
            has_goggles = not self.player.has_goggles
            self.player.has_goggles = has_goggles
            for btn in self._special_btns:
                if btn.text == "goggles":
                    btn.selected = has_goggles
                    break

    def button_setup(self, player):
        self._inv_buttons.extend(self._inventory_part_btn_setup(player, _BUTTON_SIZE))
        self._ft_buttons.extend(self._ft_btn_setup(player, _BUTTON_SIZE))
        # show Equipment column only if feature "inventory_goggles" is enabled
        if self.player.round_config.get("inventory_goggles", False):
            self._special_btns.extend(self._special_btn_setup(player, _BUTTON_SIZE))
        self.buttons.extend(
            chain(self._inv_buttons, self._ft_buttons, self._special_btns)
        )

    def draw_title(self):
        super().draw_title()
        top = SCREEN_HEIGHT / 20 + 75
        for i, section_name in enumerate(self.SECTION_TITLES):
            text_surf = self.font.render(section_name, False, "black")
            text_rect = text_surf.get_frect(
                top=top, centerx=(self.rect.width * (i + 1)) / 4
            )

            bg_rect = pygame.Rect(0, 0, text_rect.width + 40, 50)
            bg_rect.center = text_rect.center

            pygame.draw.rect(self.display_surface, "white", bg_rect, 0, 4)
            self.display_surface.blit(text_surf, text_rect)

    def refresh_buttons_content(self):
        self.sections_titles_setup()
        """Replace the existing buttons for available tools and resource count,
        in case the values change."""
        for btn in chain(self._inv_buttons, self._ft_buttons, self._special_btns):
            self.buttons.remove(btn)
        self._assignable_irs.clear()
        self._inv_buttons.clear()
        self._ft_buttons.clear()
        self._special_btns.clear()
        self._inv_buttons.extend(
            self._inventory_part_btn_setup(self.player, _BUTTON_SIZE)
        )
        self._ft_buttons.extend(self._ft_btn_setup(self.player, _BUTTON_SIZE))
        if self.player.round_config["inventory_goggles"]:
            self._special_btns.extend(
                self._special_btn_setup(self.player, _BUTTON_SIZE)
            )
        self.buttons.extend(
            chain(self._inv_buttons, self._ft_buttons, self._special_btns)
        )

    def handle_event(self, event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == Controls.INVENTORY.control_value:
                post_event(SET_CURSOR, cursor=CustomCursor.ARROW)
                self.switch_screen(GameState.PLAY)
                return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                post_event(SET_CURSOR, cursor=CustomCursor.ARROW)
                self.switch_screen(GameState.PAUSE)
                return True

    def draw_description(self):
        pass
