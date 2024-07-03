import pygame
from src.settings import *


class SettingsMenu:
    def __init__(self, font, sounds):

        # general setup
        self.display_surface = pygame.display.get_surface()
        self.font = font
        self.index = 0
        # options
        self.width = 400
        self.space = 10
        self.padding = 8
        self.sounds = sounds
        self.go_back = False
        self.current_item = 0
        self.slider = None
        # entries

        self.options = ("keybinds", "volume", "back")
        self.option_data = { 0: {
                "Up": "UP ARROW",
                "Down": "DOWN ARROW",
                "Left": "LEFT ARROW",
                "Right": "RIGHT ARROW",
                "Use": "SPACE",
                "Cycle Tools": "Q",
                "Cycle Seeds": "E",
                "Plant Current Seed": "LCTRL",
            },

            1: {
            "slider": self.slider,
        },
            2: {

             "back": "Press Space to go back to the main menu!"
            },

        }

        # create the text surfaces
        self.text_surfs = []
        self.total_height = 0

        for item in self.options:
            text_surf = self.font.render(item, False, 'Black')
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)

        self.menu_top = SCREEN_HEIGHT / 20 + 100
        self.main_rect = pygame.Rect(
            SCREEN_WIDTH / 20 - self.width / 20,
            self.menu_top,
            self.width,
            self.total_height)

        # buy / sell text surface
        
    def input(self, keys):
        #  THIS CODE FOR THE SLIDER CAUSES UNEXPECTED LAG WHEN GOING THROUGH THE MENU - CURRENTLY NOT FUNCTIONAL
        # if self.slider:
        #     for event in pygame.event.get():
        #         self.slider.handle_event(event)

        self.index = (
            self.index + int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        ) % len(self.options)

        if keys[pygame.K_SPACE]:
            self.current_item = self.options[self.index]
            return self.current_item

    def show_entry(self, text_surf, top, index, text_index):
        # background
        bg_rect = pygame.Rect(self.main_rect.left, top, self.width,
                              text_surf.get_height() + (self.padding * 2))
        pygame.draw.rect(self.display_surface, 'White', bg_rect, 0, 4)
        big_rect = pygame.Rect(
            SCREEN_WIDTH // 15 + self.width,
            (SCREEN_HEIGHT // 20 + self.total_height // 2) + 25,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2)
        pygame.draw.rect(self.display_surface, 'White', big_rect, 0, 4)
        # text
        if not self.slider:
            self.slider = Slider(
                SCREEN_WIDTH // 15 + self.width + 10,
                (SCREEN_HEIGHT // 20 + self.total_height // 2) + 35,
                big_rect.width / 2,
                10,
                0,
                100,
                50,
                self.sounds)
        text_rect = text_surf.get_frect(
            midleft=(
                self.main_rect.left +
                (
                    self.main_rect.width /
                    2) -
                text_surf.get_width() /
                2,
                bg_rect.centery))
        big_text_surfs = []
        if self.option_data[index]:
            for key, value in self.option_data[index].items():
                if isinstance(value, str):
                    text = f"{key}: {value}"
                    big_text_surf = self.font.render(text, False, 'Black')
                    big_text_surfs.append(big_text_surf)
                else:
                    if key == "slider":
                        # Call the function
                        self.slider.draw(self.display_surface)
                        v = self.slider.get_value()
                        text = f"Volume: {round(v)}"
                        big_text_surf = self.font.render(text, False, 'Black')
                        big_text_surfs.append(big_text_surf)
            for i, big_text_surf in enumerate(big_text_surfs):
                big_text_rect = big_text_surf.get_rect(
                    topleft=(big_rect.left + 10, big_rect.top + 15 + i * 20))
                self.display_surface.blit(big_text_surf, big_text_rect)
        self.display_surface.blit(text_surf, text_rect)
        # selected
        if index == text_index:
            pygame.draw.rect(self.display_surface, 'black', bg_rect, 4, 4)
            pygame.draw.rect(self.display_surface, 'white', big_rect, 4, 4)

    def draw(self):
        text_surf = self.font.render('Settings', False, 'Black')
        text_rect = text_surf.get_frect(
            midtop=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20))

        pygame.draw.rect(self.display_surface, 'White',
                         text_rect.inflate(10, 10), 0, 4)
        self.display_surface.blit(text_surf, text_rect)

        

        for text_index, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + text_index * \
                (text_surf.get_height() + (self.padding * 2) + self.space)
            self.show_entry(text_surf, top, self.index, text_index)


class Slider:
    def __init__(
            self,
            x,
            y,
            width,
            height,
            min_value,
            max_value,
            initial_value,
            sounds):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.sounds = sounds
        self.value = initial_value
        self.clicking = False
        self.knob_radius = 10

    def draw(self, surface):
        pygame.draw.rect(surface, (220, 185, 138), self.rect, 0, 4)
        pygame.draw.rect(surface, (243, 229, 194),
                         self.rect.inflate(-4, -4), 0, 4)
        knob_x = self.rect.left + \
            (self.rect.width - 10) * (self.value - self.min_value) / \
            (self.max_value - self.min_value)
        pygame.draw.circle(surface, (232, 207, 166), (int(
            knob_x), self.rect.centery), self.knob_radius)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.clicking = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.clicking = False
        elif event.type == pygame.MOUSEMOTION and self.clicking:
            self.value = self.min_value + (self.max_value - self.min_value) * (
                event.pos[0] - self.rect.left) / (self.rect.width - 10)
            self.value = max(self.min_value, min(self.max_value, self.value))
            self.sounds['music'].set_volume(min((self.value / 1000), 0.4))
            for key in self.sounds:
                if key != 'music':
                    self.sounds[key].set_volume((self.value / 100))

    def get_value(self):
        return self.value
