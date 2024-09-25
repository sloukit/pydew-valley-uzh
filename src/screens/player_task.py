from typing import Callable

import pygame
import pygame.freetype

from src.gui.menu.abstract_menu import AbstractMenu
from src.enums import GameState
from src.gui.menu.components import Slider, EntryField
from src.gui.menu.task_menu import TaskMenu
from src.screens.minigames.gui import (
    Linebreak,
    Text,
    TextChunk,
    _draw_box,
    _ReturnButton,
)
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH, SoundDict
from src.support import get_outline, import_freetype_font
from src.colors import (SL_ORANGE_BRIGHTEST)

"""
Move all of this to menu, keep it visual only, and make new player_task in screens that deals with functionality?
- add image to task textbox
- add entryfields to task textbox, save 3 returned data
- add conditions to confirm button
- create dictionary to map item names to images
entry fields get updated constantly?? therefore self.active gets reset constantly

"""


class PlayerTask:
    def __init__(self, switch_screen: Callable[[], None]):
        self.task_menu = TaskMenu(switch_screen)

    def handle_event(self, event):
        self.task_menu.handle_event(event)

    def update(self, dt):
        self.task_menu.update(dt)