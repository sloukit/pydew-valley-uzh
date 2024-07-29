from typing import Type

import pygame
from pygame.math import Vector2 as vector

from src.controls import Controls
from src.gui.menu.components import Button, Slider, KeySetup
from src.support import load_data, save_data, resource_path


class Description:
    def __init__(self, pos):
        # surface
        self.display_surface = pygame.display.get_surface()
        self.description_surface = None
        self.description_slider_surface = None

        # rect
        self.rect = pygame.Rect(pos, (600, 400))
        self.setup()

        # font
        self.font = pygame.font.Font(resource_path('font/LycheeSoda.ttf'), 30)

    # setup
    def setup(self):
        # description
        self.description_rect = pygame.Rect(0, 0, 600, 400)
        self.description_rect.topright = self.rect.topright
        self.description_surface = pygame.Surface(self.description_rect.size)
        self.description_surface.set_colorkey('green')

        # slider
        self.description_slider_surface = pygame.Surface((600, 600))
        self.description_slider_rect = self.description_surface.get_rect()
        self.description_slider_surface.set_colorkey('green')

    # events
    def handle_event(self, event) -> bool:
        return self.mouse_wheel(event)

    def mouse_wheel(self, event) -> bool:
        if event.type == pygame.MOUSEWHEEL:
            speed = 10
            self.description_slider_rect.y += event.y * speed

            y = self.description_slider_rect.y
            y_max = 0
            self.description_slider_rect.y = min(y_max, y)

            height_s1 = self.description_surface.get_height()
            height_s2 = self.description_slider_surface.get_height()
            y = self.description_slider_rect.y
            y_min = height_s1 - height_s2
            self.description_slider_rect.y = max(y_min, y)
            return True
        return False

    # draw
    def make_surface_transparent(self):
        self.description_surface.fill('green')
        self.description_slider_surface.fill('green')

    def draw_slider_bar(self):
        height1 = self.description_slider_surface.get_height()
        height2 = self.description_surface.get_height()
        Y1 = self.description_slider_rect.top

        coeff = height2 / height1
        slider_height = coeff * height2

        slide_bar_rect = pygame.Rect(0, 0, 10, slider_height)
        slide_bar_rect.right = self.description_rect.right - 2
        slide_bar_rect.top = self.description_rect.top - Y1 * coeff

        pygame.draw.rect(self.display_surface, 'grey', slide_bar_rect, 0, 4)

    def draw(self):
        pygame.draw.rect(self.display_surface, 'White', self.rect, 0, 4)
        self.make_surface_transparent()
        self.draw_slider_bar()


class KeybindsDescription(Description):
    def __init__(self, pos: tuple[int, int], controls: Type[Controls]):
        super().__init__(pos)
        self.controls = controls

        self.keys_group = []
        self.selection_key = None
        self.pressed_key = None

        # setup
        self.create_keybinds()
        reset_btn_rect = pygame.Rect(0, 0, 100, 50)
        reset_btn_rect.bottomright = self.rect.bottomleft - vector(10, 0)

        self.reset_button = Button('Reset', self.font, reset_btn_rect, (0, 0))

    def save_data(self):
        for key in self.keys_group:
            self.controls[key.name].control_value = key.value

        save_data(self.controls.as_dict(), 'keybinds.json')

    def create_keybinds(self):

        margin = 10
        size = (600, 60 * self.controls.length() + 2*margin)
        self.description_slider_surface = pygame.Surface((size))
        self.description_slider_rect = self.description_slider_surface.get_rect()
        self.description_slider_surface.set_colorkey('green')

        self.keys_group.clear()
        index = 0
        for control in self.controls.all_controls():
            name = self.controls(control).name

            unicode = self.value_to_unicode(control.control_value)
            path = self.get_path(control.control_value)

            image = pygame.image.load(path)
            image = pygame.transform.scale(image, (40, 40))

            topleft = (10, 10 + 60 * index)
            key_setup_button = KeySetup(name, control, unicode, topleft, image)
            self.keys_group.append(key_setup_button)

            index += 1

    # events
    def handle_event(self, event: pygame.event.Event) -> bool:
        return (super().handle_event(event) or
                self.set_key(event) or
                self.handle_click(event))

    # keybinds
    def get_hovered_key(self):
        s1_pos = self.description_rect.topleft
        s2_pos = self.description_slider_rect.topleft
        offset = vector(s1_pos) + vector(s2_pos)
        for key in self.keys_group:
            if key.hover(offset):
                return key
        return None

    def handle_click(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.remove_selection()
            hovered_key = self.get_hovered_key()
            if hovered_key:
                self.pressed_key = hovered_key
                self.pressed_key.start_press_animation()
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed_key:
                s1_pos = self.description_rect.topleft
                s2_pos = self.description_slider_rect.topleft
                offset = vector(s1_pos) + vector(s2_pos)

                self.pressed_key.start_release_animation()

                if self.pressed_key.hover(offset):
                    self.selection_key = self.pressed_key
                    self.selection_key.bg_color = 'red'
                else:
                    self.remove_selection()

                return True

            return False

    def set_key(self, event: pygame.event.Event) -> bool:
        if self.selection_key:
            s1_pos = self.description_rect.topleft
            s2_pos = self.description_slider_rect.topleft
            offset = vector(s1_pos) + vector(s2_pos)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button > pygame.BUTTON_RIGHT:
                    # Scrolling should not be allowed as keybind
                    return False
                if self.selection_key.hover(offset):
                    rpath = resource_path('images/keys/rclick.png')
                    lpath = resource_path('images/keys/lclick.png')
                    unknown = resource_path('images/keys/generic.png')
                    if event.button == pygame.BUTTON_LEFT:
                        path = lpath
                    elif event.button == pygame.BUTTON_RIGHT:
                        path = rpath
                    else:
                        path = unknown
                    value = event.button
                    unicode = None
                    self.update_key_value(path, value, unicode)
                    return True

            if event.type == pygame.KEYDOWN:
                path = self.get_path(event.key)
                value = event.key
                unicode = event.unicode.upper()
                self.update_key_value(path, value, unicode)
                return True

        return False

    def update_key_value(self, path: str, value: int, unicode: str | None):
        image = pygame.image.load(path)
        image = pygame.transform.scale(image, (40, 40))

        k_unicode = unicode if self.is_generic(unicode) else None
        self.selection_key.unicode = k_unicode
        self.selection_key.symbol_image = image
        self.selection_key.value = value

    def remove_selection(self):
        self.selection_key = None

        if self.pressed_key:
            self.pressed_key.bg_color = 'grey'
            self.pressed_key = None

    def reset_keybinds(self):
        self.controls.load_default_keybinds()
        self.create_keybinds()

    @staticmethod
    def is_generic(symbol: str | None):
        if not symbol or len(symbol) != 1:
            return False
        alphanumeric = symbol in "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        other = symbol in "!@#$%^&*()_+-=[]{}|;':,.<>/?"
        return alphanumeric or other

    @staticmethod
    def get_path(keydown: int):
        if keydown == pygame.BUTTON_LEFT:
            return resource_path("images/keys/lclick.png")
        if keydown == pygame.BUTTON_RIGHT:
            return resource_path("images/keys/rclick.png")

        special_keys = {
            pygame.K_SPACE: "images/keys/space.png",
            pygame.K_LCTRL: "images/keys/lctrl.png",
            pygame.K_LEFT: "images/keys/left.png",
            pygame.K_UP: "images/keys/up.png",
            pygame.K_DOWN: "images/keys/down.png",
            pygame.K_RIGHT: "images/keys/right.png",
            pygame.K_RETURN: "images/keys/return.png",
            pygame.K_TAB: "images/keys/tab.png",
            pygame.K_LSHIFT: "images/keys/lshift.png",
            pygame.K_RSHIFT: "images/keys/rshift.png",
            pygame.K_RCTRL: "images/keys/rctrl.png",
            pygame.K_LALT: "images/keys/alt.png",
            pygame.K_RALT: "images/keys/alt.png",
        }

        if keydown in special_keys:
            return resource_path(special_keys[keydown])

        return resource_path("images/keys/generic.png")

    @staticmethod
    def value_to_unicode(value: int | None):
        if value is None:
            return None
        if value in range(48, 58):
            return str(value - 48)
        if value in range(97, 123):
            return chr(value - 32)
        return None

    # update
    def update_keybinds(self, dt: float):
        for key in self.keys_group:
            key.update(dt)

    # draw
    def draw_keybinds(self):
        for key in self.keys_group:
            key.draw(self.description_slider_surface)

        # blit description slider
        pos = self.description_slider_rect.topleft
        self.description_surface.blit(self.description_slider_surface, pos)

        # blit description
        pos = self.description_rect.topleft
        self.display_surface.blit(self.description_surface, pos)

    def draw(self):
        super().draw()
        self.draw_keybinds()


class VolumeDescription(Description):
    def __init__(self, pos, sounds):
        super().__init__(pos)
        self.sounds = sounds

        # setup
        self.create_slider()
        self.import_data()

    # setup
    def create_slider(self):
        slider_rect = pygame.Rect((30, 30), (200, 10))
        pos = self.rect.topleft
        self.slider = Slider(slider_rect, 0, 100, 50, self.sounds, pos)

    def save_data(self):
        data = self.slider.get_value()
        save_data(int(data), 'volume.json')

    def import_data(self):
        try:
            self.slider.value = load_data('volume.json')
        except FileNotFoundError:
            pass

    # events
    def handle_event(self, event) -> bool:
        return (super().handle_event(event) or
                self.slider.handle_event(event))

    # draw
    def draw_slider(self):
        self.slider.draw(self.description_slider_surface)

        # blit description slider
        pos = self.description_slider_rect.topleft
        self.description_surface.blit(self.description_slider_surface, pos)

        # blit description
        pos = self.description_rect.topleft
        self.display_surface.blit(self.description_surface, pos)

    def draw(self):
        super().draw()
        self.draw_slider()
