import pygame, sys

from pygame import Vector2 as vector
from pygame.mouse import get_pos as mouse_pos
from pygame.mouse import get_pressed as mouse_buttons

from .settings import SCREEN_WIDTH, SCREEN_HEIGHT, GameState
from .support import save_data, load_data


# -------  Menu ------- #

class GeneralMenu:
    def __init__(self, title, options, switch_screen, size, background=None):
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.buttons_surface = pygame.Surface(size)
        self.buttons_surface.set_colorkey('green')
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)
        self.background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT)) if background else None
        self.title = title

        # rect
        self.size = size
        self.rect = None
        self.rect_setup()

        # buttons
        self.options = options
        self.buttons = []
        self.button_setup()

        # switch
        self.switch_screen = switch_screen
    

    # setup
    def rect_setup(self):
        self.rect = pygame.Rect((0, 0), self.size)
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    def button_setup(self):
        button_width = 400
        button_height = 50
        space = 10
        generic_button_rect = pygame.Rect((0,0), (button_width, button_height))
        for item in self.options:
            button = Button(item, self.font, generic_button_rect, self.rect.topleft)
            self.buttons.append(button)
            generic_button_rect = generic_button_rect.move(0, button_height + space)


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
            
    def click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button.hover_active:
                    self.button_action(button.text)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    
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
        text_rect = text_surf.get_frect(midtop=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20))

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
            button.draw(self.buttons_surface)
        self.display_surface.blit(self.buttons_surface, self.rect.topleft)

    
    def draw(self):
        self.draw_background()
        self.draw_title()
        self.draw_buttons()
    

    # update
    def update(self, dt):
        self.event_loop()
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
                self.switch_screen(GameState.LEVEL)

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
                self.switch_screen(GameState.LEVEL)

class SettingsMenu(GeneralMenu):
    def __init__(self, switch_screen, sounds):
        options = ['Keybinds', 'Volume', 'Back']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Settings'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)

        # rect
        self.setup()

        # description
        description_pos = self.rect.topright + vector(100, 0)
        self.keybinds_description = KeybindsDescription(description_pos)
        self.volume_description = VolumeDescription(description_pos, sounds)

        self.current_description = self.keybinds_description

    # setup
    def button_action(self, text):
        if text == 'Keybinds':
            self.current_description = self.keybinds_description
        if text == 'Volume':
            self.current_description = self.volume_description
        if text == 'Back':
            self.keybinds_description.save_data()
            self.volume_description.save_data()
            self.switch_screen(GameState.PAUSE)

    def setup(self):
        offset = vector(-350, 0)
        self.rect.topleft += offset
        for button in self.buttons:
            button.offset = vector(self.rect.topleft)

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
        self.draw_background()
        self.draw_title()
        self.draw_buttons()
        self.current_description.draw()

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

class Button:
    def __init__(self, text, font, rect, offset):
        self.font = font
        self.text = text
        self.rect = rect
        self.offset = vector(offset)
        self.color = 'White'
        self.hover_active = False

        self.display_surface = None

    def mouse_hover(self):
        return self.rect.collidepoint(mouse_pos()-self.offset)
    
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

class KeySetup:
    def __init__(self, key_name, key_value, pos, symbol_image):
        self.key_name = key_name
        self.key_symbol = None
        self.key_value = key_value
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)
        self.offset = vector()

        # rect
        self.pos = pos
        self.rect = pygame.Rect(pos, (300, 50))

        # symbol
        self.symbol_image = symbol_image
        self.symbol_image = pygame.transform.scale(self.symbol_image, (40, 40))
        self.symbol_image_rect = self.symbol_image.get_rect(midright=self.rect.midright - vector(10, 0))
    

    def hover(self, offset):
        self.offset = vector(offset)
        return self.rect.collidepoint(mouse_pos() - self.offset)


    # draw
    def draw_key_name(self, surface):
        text_surf = self.font.render(self.key_name, False, 'Black')
        text_rect = text_surf.get_frect(midleft=(self.rect.left + 10, self.rect.centery))
        pygame.draw.rect(surface, 'White', text_rect.inflate(10, 10), 0, 4)
        surface.blit(text_surf, text_rect)
    
    def draw_symbol(self, surface):
        text_surf = self.font.render(self.key_symbol, False, 'White')
        text_rect = text_surf.get_frect(center=self.symbol_image_rect.center)   
        surface.blit(self.symbol_image, self.symbol_image_rect)
        surface.blit(text_surf, text_rect)
    
    def draw(self, surface):
        pygame.draw.rect(surface, 'grey', self.rect, 0, 4)
        self.draw_key_name(surface)
        self.draw_symbol(surface)

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
            self.value = self.min_value + (self.max_value - self.min_value) * (mouse_pos()[0] - self.offset.x - self.rect.left) / (self.rect.width - 10)
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
        text_rect = text_surf.get_frect(midtop=(self.rect.centerx, self.rect.bottom + 10))
        self.surface.blit(text_surf, text_rect)
    
    def draw_knob(self):
        knob_x = self.rect.left + (self.rect.width - 10) * (self.value - self.min_value) / (self.max_value - self.min_value)
        pygame.draw.circle(self.surface, (232, 207, 166), (int(knob_x), self.rect.centery), self.knob_radius)

    def draw_rect(self):
        pygame.draw.rect(self.surface, (220, 185, 138), self.rect, 0, 4)
        pygame.draw.rect(self.surface, (243, 229, 194), self.rect.inflate(-4, -4), 0, 4)


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
        self.description_slider_surface = pygame.Surface((600, 500))
        self.description_slider_rect = self.description_surface.get_rect()
        self.description_slider_surface.set_colorkey('green')


    # events
    def handle_events(self, event):
        self.mouse_wheel(event)

    def mouse_wheel(self, event):
        if event.type == pygame.MOUSEWHEEL:
            speed = 10
            self.description_slider_rect.y += event.y * speed
            self.description_slider_rect.y = min(0, self.description_slider_rect.y)
            self.description_slider_rect.y = max(self.description_surface.height - self.description_slider_surface.height, self.description_slider_rect.y)


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
        self.key_setup = None     # TODO: change name

        # setup
        self.import_data()
        self.create_keybinds()
        

    # setup
    def create_keybinds(self):
        index = 0
        for key_name, value in self.keybinds.items():
            key_value = value
            symbol = self.value_to_unicode(key_value)

            path = self.get_path(key_value)
            image = pygame.image.load(path)
            image = pygame.transform.scale(image, (40, 40))

            pos = (10, 10 + 60 * index)
            key_setup = KeySetup(key_name, key_value, pos, image)
            key_setup.key_symbol = symbol
            self.keys_group.append(key_setup)
            index += 1
    
    def save_data(self):
        data = {}
        for key in self.keys_group:
            data[key.key_name] = key.key_value
        save_data(data, 'keybinds.json')

    def import_data(self):
        self.keybinds = {
            "Up": pygame.K_UP,
            "Down": pygame.K_DOWN,
            "Left": pygame.K_LEFT,
            "Right": pygame.K_RIGHT,
            "Use": pygame.K_SPACE,
            "Cycle Tools": pygame.K_TAB,
            "Cycle Seeds": pygame.K_LSHIFT,
            "Plant Current Seed": pygame.K_RETURN,
        }

        try:
            self.keybinds = load_data('keybinds.json')
        except FileNotFoundError:
            pass


    # events
    def handle_events(self, event):
        super().handle_events(event)
        self.select_keySetup(event)
        self.set_key(event)

    # keybinds
    def select_keySetup(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            for key in self.keys_group:
                offset = vector(self.description_slider_rect.topleft) + self.description_rect.topleft
                if key.hover(offset):
                    self.key_setup = key
                    return
            self.key_setup = None

    def set_key(self, event):
        if self.key_setup:
            if event.type == pygame.KEYDOWN:
                symbol = event.unicode.upper()
                path = self.get_path(event.key)
                image = pygame.image.load(path)
                image = pygame.transform.scale(image, (40, 40))

                self.key_setup.key_symbol = symbol if self.is_generic(symbol) else None
                self.key_setup.symbol_image = image
                self.key_setup.key_value = event.key
                self.key_setup = None
        
    def is_generic(self, symbol):
        return symbol in "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?"

    def get_path(self, keydown):
        if keydown == None:
            return "images/keys/generic.svg"

        special_keys = {
            pygame.K_SPACE: "images/keys/space.svg",
            pygame.K_LCTRL: "images/keys/lctrl.png",
            pygame.K_LEFT: "images/keys/left.png",
            pygame.K_UP: "images/keys/up.svg",
            pygame.K_DOWN: "images/keys/down.svg",
            pygame.K_RIGHT: "images/keys/right.svg"
        }

        if keydown in special_keys:
            return special_keys[keydown]
        
        return "images/keys/generic.svg"

    def value_to_unicode(self, value):
        if value == None:
            return None
        if value in range(48, 58):
            return str(value - 48)
        if value in range(97, 123):
            return chr(value - 32)
        return None
    

    # draw
    def draw_selected_key_indicator(self):
        if self.key_setup:
            pygame.draw.rect(self.description_slider_surface, 'red', self.key_setup.rect, 4, 4)

    def draw_keybinds(self):
        for key in self.keys_group:
            key.draw(self.description_slider_surface)

        self.draw_selected_key_indicator()
        self.description_surface.blit(self.description_slider_surface, self.description_slider_rect)
        self.display_surface.blit(self.description_surface, self.description_rect.topleft)
    
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
        self.slider = Slider(slider_rect, 0, 100, 50, self.sounds, self.rect.topleft)
    
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
        self.description_surface.blit(self.description_slider_surface, self.description_slider_rect.topleft)
        self.display_surface.blit(self.description_surface, self.description_rect.topleft)

    def draw(self):
        super().draw()
        self.draw_slider()
    



