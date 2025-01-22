from collections.abc import Iterable
from typing import Callable

import pygame

from src.colors import (
    SL_ORANGE_BRIGHT,
    SL_ORANGE_BRIGHTER,
    SL_ORANGE_DARK,
    SL_ORANGE_MEDIUM,
)
from src.enums import SelfAssessmentDimension
from src.gui.menu.abstract_menu import AbstractMenu
from src.gui.menu.components import AbstractButton
from src.screens.minigames.gui import Text, TextChunk, _draw_box, _ReturnButton
from src.settings import SAM_BORDER_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH
from src.support import get_translated_string as _
from src.support import import_font, resource_path


class _SAMButton(AbstractButton):
    _name: str
    _selected: bool

    def __init__(self, name: str, img: pygame.Surface):
        super().__init__(img, pygame.Rect())
        self._name = name

        self.color = SL_ORANGE_BRIGHT
        self.content = self._content
        self._content_rect = self.content.get_frect()

        self.rect = self._content_rect.copy()
        self.rect.size = SAM_BORDER_SIZE

        self.initial_rect = self.rect.copy()

        self._selected = False

    @property
    def text(self):
        return self._name

    def draw_hover(self):
        if self.mouse_hover():
            self.hover_active = True
            color = SL_ORANGE_MEDIUM
        else:
            self.hover_active = False
            color = self.color

        if self._selected:
            color = SL_ORANGE_BRIGHTER

        pygame.draw.rect(self.display_surface, color, self.rect, 0, 2)

    def move(self, topleft: tuple[float, float]):
        self.rect.topleft = topleft
        self.initial_rect.center = self.rect.center
        self._content_rect.center = self.rect.center

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, SL_ORANGE_DARK, self.rect.inflate(6, 6), 6, 4)

        self.display_surface = surface
        self.draw_hover()
        self.draw_content()

    def change_img(self, new_img: pygame.Surface):
        self._content.fill((0, 0, 0, 0))
        self._content.blit(new_img, (0, 0))

    def select(self):
        self._selected = True

    def deselect(self):
        self._selected = False


class SelfAssessmentMenu(AbstractMenu):
    """
    Attributes:
        _return_func: Function that is called when the menu should close

        _selection: Selection of dimensions in which the Player should assess themselves
        _current_dimension: Currently selected dimension

        selected_sam: The manikin the Player has selected from the current dimension
        _selected_scale: The scale of the Player's currently selected manikin
    """

    _return_func: Callable[[], None]

    _selection: tuple[SelfAssessmentDimension, ...]
    current_dimension_index: int
    _current_dimension: SelfAssessmentDimension

    selected_sam: _SAMButton | None
    _selected_scale: int | None

    _continue_button: _ReturnButton | None
    _continue_button_text: str | None

    _sam_buttons: list[_SAMButton]
    _sam_results: dict[str, int]

    _surface: pygame.Surface | None

    font_title: pygame.Font

    def __init__(
        self,
        return_func: Callable[[], None],
        selection: Iterable[SelfAssessmentDimension],
    ):
        super().__init__(
            title=_("How do you feel right now?"), size=(SCREEN_WIDTH, SCREEN_HEIGHT)
        )

        self._return_func = return_func

        self._selection = tuple(selection)
        self.current_dimension_index = 0

        self.selected_sam = None
        self._selected_scale = None

        self._continue_button = None
        self._continue_button_text = _("Continue")

        self._sam_buttons = []
        self._sam_results = {}

        self._surface = None

        self.font_title = import_font(48, "font/LycheeSoda.ttf")

        self.setup()

    @property
    def current_dimension_index(self):
        return self._current_dimension_index

    @current_dimension_index.setter
    def current_dimension_index(self, index: int):
        self._current_dimension_index = index
        self._current_dimension = self._selection[self.current_dimension_index]

    @property
    def selected_sam(self):
        return self._selected_sam

    @selected_sam.setter
    def selected_sam(self, sam: _SAMButton | None = None):
        self._selected_sam = sam
        if self._selected_sam is not None:
            self._selected_scale = int(self._selected_sam.text) + 1

    def setup(self):
        box_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        padding = (16, 24)

        self._surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 64))

        self.button_setup()

        button_top_margin = 32
        button_area_height = self._continue_button.rect.height + button_top_margin

        text = Text(TextChunk(_("How do you feel right now?"), self.font_title))

        sam_button_w = SAM_BORDER_SIZE[0]
        sam_button_h = SAM_BORDER_SIZE[1]
        sam_button_padding = 48
        sam_button_wp = sam_button_w + sam_button_padding
        sam_button_hp = sam_button_h + sam_button_padding

        box_size = (
            sam_button_wp * 7 + padding[0] * 2,
            text.surface_rect.height
            + sam_button_hp
            + padding[1] * 2
            + button_area_height,
        )

        _draw_box(self._surface, box_center, box_size)

        text_surface = pygame.Surface(text.surface_rect.size, pygame.SRCALPHA)
        text.draw(text_surface)
        self._surface.blit(
            text_surface,
            (
                box_center[0] - text.surface_rect.width / 2,
                box_center[1]
                - text.surface_rect.height / 2
                - sam_button_hp / 2
                - button_area_height / 2,
            ),
        )

        self._continue_button.move(
            (
                box_center[0] - self._continue_button.rect.width / 2,
                box_center[1]
                - self._continue_button.rect.height
                + box_size[1] / 2
                - padding[1],
            )
        )

        for i in range(len(self._sam_buttons)):
            self._sam_buttons[i].move(
            x_offset = -(len(self._sam_buttons) - 1) / 1.75 * sam_button_wp
            self._sam_buttons[i].move(
                (
                    box_center[0] + x_offset + sam_button_wp * i,
                    box_center[1] - sam_button_h / 2,
                )
            )

    @staticmethod
    def _load_sam_img(dim: str, i: int) -> pygame.Surface:
        return pygame.image.load(
            resource_path(f"images/sam/{dim}/sam-{dim}-{i + 1}.png")
        ).convert_alpha()

    def _continue(self):
        if not self.selected_sam:
            return

        dimension = self._selection[self.current_dimension_index].name
        assessment = int(self.selected_sam._name)
        self._sam_results[dimension] = assessment

        # print(f"{self._current_dimension.name} - {self._selected_scale}")
        self.selected_sam.deselect()
        self.selected_sam = None

        if self.current_dimension_index >= len(self._selection) - 1:
            self.current_dimension_index = 0
            self._return_func(self._sam_results)
        else:
            self.current_dimension_index += 1

        dim = self._selection[self.current_dimension_index]
        for pos, sam_button in enumerate(self._sam_buttons):
            sam_button.change_img(self._load_sam_img(dim.name.lower(), pos))

    def button_action(self, name: str):
        if name == self._continue_button.text:
            self._continue()
        elif name.isdigit() and 0 <= int(name) <= len(self._sam_buttons) - 1:
            if self.selected_sam:
                self.selected_sam.deselect()
            next_selected_sam = self._sam_buttons[int(name)]
            if self.selected_sam == next_selected_sam:
                self.selected_sam = None
            else:
                next_selected_sam.select()
                self.selected_sam = next_selected_sam

    def button_setup(self):
        self._continue_button = _ReturnButton(self._continue_button_text)
        self.buttons.append(self._continue_button)

        for i in range(7):
            btn = _SAMButton(
                str(i),
                self._load_sam_img(
                    self._selection[self.current_dimension_index].name.lower(), i
                ),
            )
            self._sam_buttons.append(btn)

        self.buttons.extend(self._sam_buttons)

    def draw_title(self):
        self.display_surface.blit(self._surface, (0, 0))
