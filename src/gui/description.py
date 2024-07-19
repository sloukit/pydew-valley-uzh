
import pygame
from src import support
from src.gui.components import Button, Slider, KeySetup
from src.settings import KEYBINDS
from src.support import load_data, save_data, resource_path
from pygame.math import Vector2 as vector



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
    def handle_events(self, event):
        self.mouse_wheel(event)

    def mouse_wheel(self, event):
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
    def __init__(self, pos):
        super().__init__(pos)
        self.keybinds = self.import_controls()
        self.keys_group = []
        self.selection_key = None
        self.pressed_key = None

        # setup
        self.create_keybinds()
        reset_btn_rect = pygame.Rect(0, 0, 100, 50)
        reset_btn_rect.bottomright = self.rect.bottomleft - vector(10, 0)

        self.reset_button = Button('Reset', self.font, reset_btn_rect, (0, 0))

    # setup
    @staticmethod
    def import_controls():
        default_keybinds = KEYBINDS
        try:
            keybinds = support.load_data('keybinds.json')

            if len(keybinds) == len(default_keybinds):
                return keybinds
            
            for key in default_keybinds:
                if key not in keybinds:
                    keybinds[key] = default_keybinds[key]
            
            return keybinds
                    
        except FileNotFoundError:
            support.save_data(KEYBINDS, 'keybinds.json')
            return default_keybinds

    def save_data(self):
        data = {}

        for key in self.keys_group:
            value = {}
            value['type'] = key.type
            value['value'] = key.value
            value['text'] = key.title

            data[key.name] = value

        save_data(data, 'keybinds.json')

    def create_keybinds(self):
        index = 0
        for name, params in self.keybinds.items():
            unicode = self.value_to_unicode(params['value'])
            path = self.get_path(params['value'])

            image = pygame.image.load(path)
            image = pygame.transform.scale(image, (40, 40))

            topleft = (10, 10 + 60 * index)
            key_setup_button = KeySetup(name, unicode, params, topleft, image)
            self.keys_group.append(key_setup_button)

            index += 1

        self.description_slider_surface = pygame.Surface((600, 60 * index + 10))
        self.description_slider_rect = self.description_slider_surface.get_rect()
        self.description_slider_surface.set_colorkey('green')

    # events
    def handle_events(self, event):
        super().handle_events(event)
        self.set_key(event)
        self.keysetup_selection(event)

    # keybinds
    def get_hovered_key(self):
        s1_pos = self.description_rect.topleft
        s2_pos = self.description_slider_rect.topleft
        offset = vector(s1_pos) + vector(s2_pos)
        for key in self.keys_group:
            if key.hover(offset):
                return key
        return None

    def keysetup_selection(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.remove_selection()
            hovered_key = self.get_hovered_key()
            if hovered_key:
                self.pressed_key = hovered_key
                self.pressed_key.start_press_animation()

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            s1_pos = self.description_rect.topleft
            s2_pos = self.description_slider_rect.topleft
            offset = vector(s1_pos) + vector(s2_pos)
            if self.pressed_key:
                self.pressed_key.start_release_animation()

                if self.pressed_key.hover(offset):
                    self.selection_key = self.pressed_key
                    self.selection_key.bg_color = 'red'
                else:
                    self.remove_selection()

    def set_key(self, event):
        if self.selection_key:
            s1_pos = self.description_rect.topleft
            s2_pos = self.description_slider_rect.topleft
            offset = vector(s1_pos) + vector(s2_pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in [1, 3]:
                if self.selection_key.hover(offset):
                    rpath = resource_path('images/keys/rclick.png')
                    lpath = resource_path('images/keys/lclick.png')
                    path = lpath if event.button == 1 else rpath
                    value = 0 if event.button == 1 else 2
                    k_type = 'mouse'
                    unicode = None
                    self.update_key_value(path, value, k_type, unicode)

            if event.type == pygame.KEYDOWN:
                path = self.get_path(event.key)
                value = event.key
                k_type = 'key'
                unicode = event.unicode.upper()
                self.update_key_value(path, value, k_type, unicode)

    def update_key_value(self, path, value, k_type, unicode):
        image = pygame.image.load(path)
        image = pygame.transform.scale(image, (40, 40))

        k_unicode = unicode if self.is_generic(unicode) else None
        self.selection_key.unicode = k_unicode
        self.selection_key.type = k_type
        self.selection_key.symbol_image = image
        self.selection_key.value = value

    def remove_selection(self):
        self.selection_key = None

        if self.pressed_key:
            self.pressed_key.bg_color = 'grey'
            self.pressed_key = None

    def reset_keybinds(self):
        for key in self.keys_group:
            key.value = KEYBINDS[key.name]['value']
            key.type = KEYBINDS[key.name]['type']
            key.unicode = self.value_to_unicode(key.value)
            path = self.get_path(key.value)
            image = pygame.image.load(path)
            image = pygame.transform.scale(image, (40, 40))
            key.symbol_image = image

    def is_generic(self, symbol):
        if not symbol or len(symbol) != 1:
            return False
        alpha = symbol in "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        other = symbol in "!@#$%^&*()_+-=[]{}|;':,.<>/?"
        return alpha or other

    def get_path(self, keydown):
        if keydown == 0:
            return resource_path("images/keys/lclick.png")
        if keydown == 2:
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

    def value_to_unicode(self, value):
        if value is None:
            return None
        if value in range(48, 58):
            return str(value - 48)
        if value in range(97, 123):
            return chr(value - 32)
        return None

    # update
    def update_keybinds(self, dt):
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
    def handle_events(self, event):
        super().handle_events(event)
        self.slider.handle_event(event)

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
