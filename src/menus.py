import pygame
import sys

from pygame import Vector2 as vector
from pygame.mouse import get_pos as mouse_pos

from .settings import SCREEN_WIDTH, SCREEN_HEIGHT, GameState, KEYBINDS
from .support import save_data, load_data


# -------  Menu ------- #

class GeneralMenu:
    def __init__(self,  title, options, switch, size, background, center=None):
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.buttons_surface = pygame.Surface(size)
        self.buttons_surface.set_colorkey('green')
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)
        screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.background = pygame.transform.scale(background, screen_size)
        self.title = title

        # rect
        self.center = center
        self.size = size
        self.rect = None
        self.rect_setup()

        # buttons
        self.pressed_button = None
        self.options = options
        self.buttons = []
        self.button_setup()

        # switch
        self.switch_screen = switch

    # setup
    def rect_setup(self):
        self.rect = pygame.Rect((0, 0), self.size)
        screen_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.rect.center = self.center if self.center else screen_center

    def button_setup(self):
        # button setup
        button_width = 400
        button_height = 50
        size = (button_width, button_height)
        space = 10
        top_margin = 20

        # generic button rect
        generic_button_rect = pygame.Rect((0, 0), size)
        generic_button_rect.top = self.rect.top + top_margin
        generic_button_rect.centerx = self.rect.centerx

        # create buttons
        for title in self.options:
            rect = generic_button_rect
            button = Button(title, self.font, rect, self.rect.topleft)
            self.buttons.append(button)
            generic_button_rect = rect.move(0, button_height + space)

    # events
    def event_loop(self):
        self.mouse_hover()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            self.click(event)
            self.handle_events(event)

    def handle_events(self, event):
        pass

    def get_hovered_button(self):
        for button in self.buttons:
            if button.mouse_hover():
                return button
        return None

    def click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed_button = self.get_hovered_button()
            if self.pressed_button:
                self.pressed_button.start_press_animation()

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed_button:
                self.pressed_button.start_release_animation()

                if self.pressed_button.mouse_hover():
                    self.button_action(self.pressed_button.text)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

                self.pressed_button = None

    def mouse_hover(self):
        for button in self.buttons:
            if button.hover_active:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                return
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def button_action(self, text):
        if text == 'Play':
            self.switch_screen(GameState.LEVEL)
        if text == 'Quit':
            self.quit_game()

    def quit_game(self):
        pygame.quit()
        sys.exit()

    # draw
    def draw_title(self):
        text_surf = self.font.render(self.title, False, 'Black')
        midtop = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20)
        text_rect = text_surf.get_frect(midtop=midtop)

        bg_rect = pygame.Rect((0, 0), (200, 50))
        bg_rect.center = text_rect.center

        pygame.draw.rect(self.display_surface, 'White', bg_rect, 0, 4)
        self.display_surface.blit(text_surf, text_rect)

    def draw_background(self):
        if self.background:
            self.display_surface.blit(self.background, (0, 0))

    def draw_buttons(self):
        self.buttons_surface.fill('green')
        for button in self.buttons:
            button.draw(self.display_surface)
        self.display_surface.blit(self.buttons_surface, self.rect.topleft)

    def draw(self):
        self.draw_background()
        self.draw_title()
        self.draw_buttons()

    # update
    def update_buttons(self, dt):
        for button in self.buttons:
            button.update(dt)

    def update(self, dt):
        self.event_loop()
        self.update_buttons(dt)

        self.draw()


class MainMenu(GeneralMenu):
    def __init__(self, switch_screen):
        options = ['Play', 'Quit']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Main Menu'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)

    def button_action(self, text):
        if text == 'Play':
            self.switch_screen(GameState.LEVEL)
        if text == 'Quit':
            self.quit_game()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_game()
            if event.key == pygame.K_RETURN:
                self.button_action('Play')


class PauseMenu(GeneralMenu):
    def __init__(self, switch_screen):
        options = ['Resume', 'Options', 'Quit']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Pause Menu'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)

    def button_action(self, text):
        if text == 'Resume':
            self.switch_screen(GameState.LEVEL)
        if text == 'Options':
            self.switch_screen(GameState.SETTINGS)
        if text == 'Quit':
            self.quit_game()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.button_action('Resume')

class SettingsMenu(GeneralMenu):
    def __init__(self, switch_screen, sounds, level):
        options = ['Keybinds', 'Volume', 'Back']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Settings'
        size = (400, 400)
        switch = switch_screen
        center = vector(SCREEN_WIDTH/2, SCREEN_HEIGHT/2) + vector(-350, 0)
        super().__init__(title, options, switch, size, background, center)

        # description
        description_pos = self.rect.topright + vector(100, 0)
        self.keybinds_description = KeybindsDescription(description_pos)
        self.volume_description = VolumeDescription(description_pos, sounds)
        self.current_description = self.keybinds_description

        # buttons
        self.buttons.append(self.keybinds_description.reset_button)

        self.level = level

    # setup
    def button_action(self, text):
        if text == 'Keybinds':
            self.current_description = self.keybinds_description
        if text == 'Volume':
            self.current_description = self.volume_description
        if text == 'Back':
            self.keybinds_description.save_data()
            self.volume_description.save_data()
            self.level.player.update_keybinds()
            self.switch_screen(GameState.PAUSE)
        if text == 'Reset':
            self.keybinds_description.reset_keybinds()

    # events
    def handle_events(self, event):
        self.current_description.handle_events(event)
        self.echap(event)

    def echap(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PAUSE)

    # draw
    def draw(self):
        super().draw()
        self.current_description.draw()

    # update
    def update(self, dt):
        self.keybinds_description.update_keybinds(dt)
        super().update(dt)


class ShopMenu(GeneralMenu):
    def __init__(self, player, switch_screen):
        options = ['wood', 'apple', 'hoe', 'water', 'corn', 'tomato', 'seed']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Shop'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)

    def button_action(self, text):
        self.switch_screen(GameState.PAUSE)


# ------- Components ------- #


class Component:
    def __init__(self, rect):
        self.display_surface = pygame.display.get_surface()
        self.initial_rect = rect.copy()
        self.rect = rect

        self.animation_active = False
        self.is_press_active = False

        self.press_animation_steps = [-10]
        self.release_animation_steps = [10, 0]
        self.animation_steps = self.press_animation_steps

        self.animation_speed = 0.15
        self.current_step_index = 0

        self.initial_x = 0
        self.current_x = 0
        self.target_x = self.animation_steps[self.current_step_index]

    # animation controls
    def start_press_animation(self):
        self.animation_active = True
        self.is_press_active = True

    def start_release_animation(self):
        if self.is_press_active:
            self.extend_animation_with_release_steps()
        else:
            self.animation_steps = self.release_animation_steps
            self.animation_active = True

        self.is_press_active = False

    def reset_animation(self):
        self.animation_active = False
        self.is_press_active = False
        self.animation_steps = self.press_animation_steps
        self.current_step_index = 0
        self.target_x = self.animation_steps[self.current_step_index]
        self.current_x = 0
        self.update_rect(0)

    # animation
    def extend_animation_with_release_steps(self):
        press_list = self.press_animation_steps
        release_list = self.release_animation_steps
        self.animation_steps = press_list + release_list

    def advance_to_next_step(self):
        if self.is_last_step():
            if not self.is_press_active:
                self.reset_animation()
        else:
            self.current_step_index += 1
            self.update_rect(self.target_x)
            self.target_x = self.animation_steps[self.current_step_index]

    def has_reached_target_x(self, x):
        return abs(self.current_x - self.target_x) < abs(x)

    def is_last_step(self):
        return self.current_step_index >= len(self.animation_steps) - 1

    def animate(self, dt):
        if self.animation_active:
            direction = 1 if self.target_x > self.current_x else -1
            x_increment = direction * self.animation_speed * dt * 1000
            if self.has_reached_target_x(x_increment):
                self.advance_to_next_step()
            else:
                self.current_x += x_increment
                self.update_rect(self.current_x)

    # draw
    def draw(self, surface):
        pygame.draw.rect(surface, 'red', self.rect, 0, 4)

    # update
    def update_rect(self, x):
        self.rect.width = self.initial_rect.width + x
        self.rect.height = self.initial_rect.height + x
        self.rect.center = self.initial_rect.center

    def update(self, dt):
        self.animate(dt)


class Button(Component):
    def __init__(self, text, font, rect, offset):
        super().__init__(rect)
        self.initial_rect = rect.copy()
        self.font_size = 30
        self.font = font
        self.text = text
        self.offset = vector(offset)
        self.color = 'White'
        self.hover_active = False

        self.display_surface = None

    def mouse_hover(self):
        return self.rect.collidepoint(mouse_pos())

    # draw
    def draw_text(self):
        text_surf = self.font.render(self.text, False, 'Black')
        text_rect = text_surf.get_frect(center=self.rect.center)
        self.display_surface.blit(text_surf, text_rect)

    def draw_hover(self):
        if self.mouse_hover():
            self.hover_active = True
            pygame.draw.rect(self.display_surface, 'Black', self.rect, 4, 4)
        else:
            self.hover_active = False

    def draw(self, surface):
        self.display_surface = surface
        pygame.draw.rect(self.display_surface, self.color, self.rect, 0, 4)
        self.draw_text()
        self.draw_hover()


class KeySetup(Component):
    def __init__(self, name, unicode, params, pos, image):
        # params
        self.name = name
        self.type = params['type']
        self.value = params['value']
        self.title = params['text']
        self.unicode = unicode

        # design
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)
        self.hover_active = False
        self.bg_color = 'grey'

        # rect
        self.pos = pos
        self.rect = pygame.Rect(pos, (300, 50))
        self.offset = vector()
        super().__init__(self.rect)

        # symbol
        self.symbol_image = image
        self.symbol_image = pygame.transform.scale(self.symbol_image, (40, 40))
        midright = self.rect.midright - vector(10, 0)
        self.symbol_image_rect = self.symbol_image.get_rect(midright=midright)

    def hover(self, offset):
        self.offset = vector(offset)
        self.hover_active = self.rect.collidepoint(mouse_pos() - self.offset)
        return self.hover_active

    # draw
    def draw_key_name(self):
        text_surf = self.font.render(self.title, False, 'Black')
        midleft = (self.rect.left + 10, self.rect.centery)
        text_rect = text_surf.get_frect(midleft=midleft)
        rect = text_rect.inflate(10, 10)
        pygame.draw.rect(self.surface, 'White', rect, 0, 4)
        self.surface.blit(text_surf, text_rect)

    def draw_symbol(self):
        text_surf = self.font.render(self.unicode, False, 'White')
        text_rect = text_surf.get_frect(center=self.symbol_image_rect.center)
        self.surface.blit(self.symbol_image, self.symbol_image_rect)
        self.surface.blit(text_surf, text_rect)

    def draw(self, surface):
        self.surface = surface
        pygame.draw.rect(self.surface, self.bg_color, self.rect, 0, 4)
        self.draw_key_name()
        self.draw_symbol()


class Slider:
    def __init__(self, rect, min_value, max_value, init_value, sounds, offset):
        # main setup
        self.surface = None
        self.rect = rect
        self.offset = vector(offset)

        # values
        self.min_value = min_value
        self.max_value = max_value
        self.value = init_value

        # sounds
        self.sounds = sounds
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)

        # knob
        self.knob_radius = 10
        self.drag_active = False

    def get_value(self):
        return self.value

    # events
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos() - self.offset):
                self.drag_active = True

        if event.type == pygame.MOUSEBUTTONUP:
            self.drag_active = False

        if event.type == pygame.MOUSEMOTION and self.drag_active:
            diff = self.max_value - self.min_value
            origin_x = mouse_pos()[0] - self.offset.x - self.rect.left
            size = self.rect.width - 10
            self.value = self.min_value + diff * origin_x / size
            self.value = max(self.min_value, min(self.max_value, self.value))
            self.update_volume()

    def update_volume(self):
        self.sounds['music'].set_volume(min((self.value / 1000), 0.4))
        for key in self.sounds:
            if key != 'music':
                self.sounds[key].set_volume((self.value / 100))

    # draw
    def draw_value(self):
        text_surf = self.font.render(str(int(self.value)), False, 'Black')
        midtop = (self.rect.centerx, self.rect.bottom + 10)
        text_rect = text_surf.get_frect(midtop=midtop)
        self.surface.blit(text_surf, text_rect)

    def draw_knob(self):
        value = (self.value - self.min_value)
        diff = (self.max_value - self.min_value)
        knob_x = self.rect.left + (self.rect.width - 10) * value / diff
        color = (232, 207, 166)
        center = (int(knob_x), self.rect.centery)
        pygame.draw.circle(self.surface, color, center, self.knob_radius)

    def draw_rect(self):
        # border
        border_color = (220, 185, 138)
        pygame.draw.rect(self.surface, border_color, self.rect, 0, 4)

        # bg
        bg_color = (243, 229, 194)
        rect = self.rect.inflate(-4, -4)
        pygame.draw.rect(self.surface, bg_color, rect, 0, 4)

    def draw(self, surface):
        self.surface = surface
        self.draw_rect()
        self.draw_knob()
        self.draw_value()


# ------- Description Box ------- #

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
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)

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
        self.keybinds = {}
        self.keys_group = []
        self.selection_key = None
        self.pressed_key = None

        # setup
        self.import_data()
        self.create_keybinds()
        reset_btn_rect = pygame.Rect(0, 0, 100, 50)
        reset_btn_rect.bottomright = self.rect.bottomleft - vector(10, 0)

        self.reset_button = Button('Reset', self.font, reset_btn_rect, (0, 0))

    # setup
    def import_data(self):
        self.default_keybinds = KEYBINDS

        try:
            self.keybinds = load_data('keybinds.json')
        except FileNotFoundError:
            self.keybinds = self.default_keybinds

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
                    rpath = 'images/keys/rclick.png'
                    lpath = 'images/keys/lclick.png'
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
            key.value = self.default_keybinds[key.name]['value']
            key.type = self.default_keybinds[key.name]['type']
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
            return "images/keys/lclick.png"
        if keydown == 2:
            return "images/keys/rclick.png"

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
            return special_keys[keydown]

        return "images/keys/generic.png"

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
