from typing import Callable

import pygame

# import pygame.freetype

# from src.gui.menu.abstract_menu import AbstractMenu
# from src.enums import GameState
# from src.gui.menu.components import Slider, EntryField
from src.gui.menu.task_menu import TaskMenu


"""

- add image to task textbox
- add entryfields to task textbox, save 3 returned data
- add conditions to confirm button
- create dictionary to map item names to images

"""


class PlayerTask:
    def __init__(self, switch_screen: Callable[[], None]):
        self.task_menu = TaskMenu(switch_screen)

    def handle_event(self, event):
        self.task_menu.handle_event(event)

    def update(self, dt):
        self.task_menu.update(dt)
