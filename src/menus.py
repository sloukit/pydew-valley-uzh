import pygame
from .settings import *
from .ui import Slider

class Menu:
    def __init__(self, font, game_state, menu_type, bg=None):
        self.menu_type = menu_type
        self.display_surface = pygame.display.get_surface()
        self.font = font
        self.game_state = game_state
        self.bg = bg
        self.title = ''

        # options
        self.width = 400
        self.space = 10
        self.padding = 8
        self.align = 'center'

        # entries
        self.options = []
        self.index = 0

        # setup
        self.text_surfs = []
        self.total_height = 0
        self.menu_top = 0
        self.main_rect = None
        self.setup()

    def setup(self):
        for item in self.options:
            text_surf = self.font.render(item, False, 'Black')
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)

        self.total_height += (len(self.text_surfs) - 1) * self.space
        self.menu_top = SCREEN_HEIGHT / 2 - self.total_height / 2
        self.main_rect = pygame.Rect(SCREEN_WIDTH / 2 - self.width / 2, self.menu_top, self.width, self.total_height)

    def exit(self):
        self.index = 0
        self.game_state.pop()

    def action(self, current_option):
        print(f'\033[92m{current_option}\033[0m')

    def input(self):
        keys = pygame.key.get_just_pressed()

        self.index = (self.index + int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])) % len(self.options)

        if keys[pygame.K_ESCAPE]:
            self.exit()

        if keys[pygame.K_SPACE]:
            current_option = self.options[self.index]
            self.action(current_option)

    def show_entry(self, text_surf, top, index, text_index):
        # entry background
        bg_rect = pygame.Rect(self.main_rect.left, top, self.width, text_surf.get_height() + (self.padding * 2))
        pygame.draw.rect(self.display_surface, 'White', bg_rect, 0, 4)

        # text
        text_rect = text_surf.get_frect(midleft=(self.main_rect.left + 20, bg_rect.centery)) if self.align == 'left' else text_surf.get_frect(center=bg_rect.center)

        self.display_surface.blit(text_surf, text_rect)

        # selected
        if index == text_index:
            pygame.draw.rect(self.display_surface, 'black', bg_rect, 4, 4)


    def draw(self):
        # drawing the background
        if self.bg:
            self.display_surface.blit(self.bg, (0, 0))
        else:
            self.display_surface.fill('black')
        # drawing the entries
        for text_index, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + text_index * (text_surf.get_height() + (self.padding * 2) + self.space)
            self.show_entry(text_surf, top, self.index, text_index)
        # drawing the title
        if self.title:
            text_surf = self.font.render(self.title, False, 'Black')
            text_rect = text_surf.get_frect(midtop=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20))
            pygame.draw.rect(self.display_surface, 'White', text_rect.inflate(10, 10), 0, 4)
            self.display_surface.blit(text_surf, text_rect)

    def update(self):
        self.input()
        self.draw()

    def run(self):
        while self.game_state[-1] == self.menu_type:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    while self.game_state[-1] != 'quit':
                        self.game_state.pop()

            self.update()
            pygame.display.update()


# ~~~~~~~~~~~~~~~~~~~~ game sub-menus ~~~~~~~~~~~~~~~~~~~~~~~~~
class PauseMenu(Menu):
    def __init__(self, font, game_state, bg=None):
        super().__init__(font, game_state, menu_type='pause_menu', bg=bg)
        self.options = ['Resume', 'Settings', 'Main Menu']
        self.setup()
        self.title = "Pause"

    def action(self, current_option):
        match(current_option):
            case "Resume":
                self.exit()
            case "Settings":
                self.game_state.append('settings_menu')
            case "Main Menu":
                while(self.game_state[-1] != "main_menu"):
                    self.game_state.pop()


class SettingsMenu(Menu):
    def __init__(self, font, game_state, sounds, bg=None):
        super().__init__(font, game_state, menu_type='settings_menu', bg=bg)
        self.options = ("Keybinds", "Volume", "Back")
        self.setup()
        self.title = "Settings"
        self.main_rect.x = SCREEN_WIDTH / 20 - self.width / 20
        self.main_rect.y = SCREEN_HEIGHT / 20 + 100


        self.sounds = sounds
        self.big_rect = pygame.Rect(SCREEN_WIDTH // 15 + self.width, (SCREEN_HEIGHT // 20 + self.total_height//2)+25, SCREEN_WIDTH // 2,
                                    SCREEN_HEIGHT // 2)
        self.slider = Slider(SCREEN_WIDTH // 15 + self.width + 10, (SCREEN_HEIGHT // 20 + self.total_height//2)+35,
                             self.big_rect.width/2, 10, 0, 100, 50, self.sounds)
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
             "Back": "Press Space to go back to the main menu!"
            },
        }

    def show_entry(self, text_surf, top, index, text_index):
        super().show_entry(text_surf, top, index, text_index)
        pygame.draw.rect(self.display_surface, 'White', self.big_rect, 0, 4)
        big_text_surfs = []
        if self.option_data[index]:
            for key, value in self.option_data[index].items():
                if isinstance(value, str):
                    text = f"{key}: {value}"
                    big_text_surf = self.font.render(text, False, 'Black')
                    big_text_surfs.append(big_text_surf)
                else:
                    if key == "slider":
                        self.slider.draw(self.display_surface)  # Call the function
                        v = self.slider.get_value()
                        text = f"Volume: {round(v)}"
                        big_text_surf = self.font.render(text, False, 'Black')
                        big_text_surfs.append(big_text_surf)
            for i, big_text_surf in enumerate(big_text_surfs):
                big_text_rect = big_text_surf.get_rect(topleft=(self.big_rect.left + 10, self.big_rect.top + 15 + i * 20))
                self.display_surface.blit(big_text_surf, big_text_rect)

    def action(self, current_option):
        match(current_option):
            case "Back":
                self.exit()

    def update(self):
        super().update()
        self.slider.update()

class ShopMenu(Menu):
    def __init__(self, font, game_state, player, bg=None):
        super().__init__(font, game_state, menu_type="shop_menu", bg=bg)
        self.player = player
        self.options = list(self.player.inventory.keys())
        self.setup()
        self.title = 'shop'
        self.align = "left"

        # buy / sell text surface
        self.buy_text = self.font.render('buy', False, 'Black')
        self.sell_text = self.font.render('sell', False, 'Black')

    def action(self, current_option):
        if 'seed' in current_option:
            seed_price = PURCHASE_PRICES[current_option]
            if self.player.money >= seed_price:
                self.player.inventory[current_option] += 1
                self.player.money -= PURCHASE_PRICES[current_option]

        else:
            if self.player.inventory[current_option] > 0:
                self.player.inventory[current_option] -= 1
                self.player.money += SALE_PRICES[current_option]

    def display_money(self):
        # total money
        text_surf = self.font.render(f'${self.player.money}', False, 'Black')
        text_rect = text_surf.get_frect(midbottom=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20))
        pygame.draw.rect(self.display_surface, 'White', text_rect.inflate(10, 10), 0, 4)
        self.display_surface.blit(text_surf, text_rect)

    def draw(self):
        super().draw()
        self.display_money()
        # additional things for each entry
        for text_index, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + text_index * (text_surf.get_height() + (self.padding * 2) + self.space)
            bg_rect = pygame.Rect(self.main_rect.left, top, self.width, text_surf.get_height() + (self.padding * 2)) # re calculating :(
            # amount of money
            amount = list(self.player.inventory.values())[text_index]
            amount_surf = self.font.render(str(amount), False, 'Black')
            amount_rect = amount_surf.get_frect(midright=(self.main_rect.right - 20, bg_rect.centery))
            self.display_surface.blit(amount_surf, amount_rect)
            # if selected show sell or buy
            if self.index == text_index:
                pos_rect = self.buy_text.get_frect(midleft=(self.main_rect.left + 250, bg_rect.centery))
                surf = self.buy_text if 'seed' in self.options[self.index] else self.sell_text
                self.display_surface.blit(surf, pos_rect)


# ~~~~~~~~~~~~~~~~~~~~ Main Menu ~~~~~~~~~~~~~~~~~~~~~~~~~
class MainMenu(Menu):
    def __init__(self, font, game_state, bg):
        super().__init__(font, game_state, menu_type="main_menu", bg=bg)
        self.options = ['Play', 'Quit']
        self.setup()
        self.title = "Main Menu"

    def action(self, current_option):
        match(current_option):
            case "Play":
                self.game_state.append('game')
            case "Quit":
                self.exit()
