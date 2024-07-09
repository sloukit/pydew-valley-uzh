import pygame

from src.level import Level
from src.menus import MainMenu, PauseMenu, SettingsMenu
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, GameState
from src.support import tmx_importer, animation_importer, import_folder_dict
from src.support import import_folder, character_importer, sound_importer
from src.support import import_font


class Game:
    def __init__(self):
        # main setup
        pygame.init()
        screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.display_surface = pygame.display.set_mode(screen_size)
        pygame.display.set_caption('PyDew')

        # frames
        self.frames = None
        self.character_frames = None
        self.level_frames = None
        self.overlay_frames = None

        # assets
        self.tmx_maps = None
        self.sounds = None
        self.font = None
        self.load_assets()

        # game setup
        self.running = True
        self.clock = pygame.time.Clock()

        # screens
        self.level = Level(self.switch_state, self.tmx_maps, self.frames, self.sounds)
        self.main_menu = MainMenu(self.switch_state)
        self.pause_menu = PauseMenu(self.switch_state)
        self.settings_menu = SettingsMenu(self.switch_state, self.sounds, self.level)

        # state
        self.screens = {
            GameState.MAIN_MENU: self.main_menu,
            GameState.PAUSE: self.pause_menu,
            GameState.SETTINGS: self.settings_menu,
            GameState.LEVEL: self.level
        }

        self.current_state = GameState.MAIN_MENU

    def switch_state(self, state):
        self.current_state = state


    def load_assets(self):
        self.tmx_maps = tmx_importer('data/maps')

        # frames
        self.level_frames = {
            'animations': animation_importer('images', 'animations'),
            'soil': import_folder_dict('images/soil'),
            'soil water': import_folder_dict('images/soil water'),
            'tomato': import_folder('images/plants/tomato'),
            'corn': import_folder('images/plants/corn'),
            'rain drops': import_folder('images/rain/drops'),
            'rain floor': import_folder('images/rain/floor'),
            'objects': import_folder_dict('images/objects')
        }
        self.overlay_frames = import_folder_dict('images/overlay')
        self.character_frames = character_importer('images/characters')
        
        self.frames = {
            'character': self.character_frames,
            'level': self.level_frames,
            'overlay': self.overlay_frames
        }

        self.sounds = sound_importer('audio', default_volume=0.1)

        self.font = import_font(30, 'font/LycheeSoda.ttf')

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            screen = self.screens[self.current_state]
            screen.update(dt)

            pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
