import sys
import pygame

from src import settings
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, GameState
from src import support
from src import level

from src.level import Level
from src.menus import MainMenu, PauseMenu, SettingsMenu, ShopMenu
from src.dialog import DialogueManager, prepare_tb_image


class Game:
    def __init__(self):
        # main setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('PyDew')

        self._tb_base = None
        self.tb_main_text_base_surf: pygame.Surface | None = None
        self.tb_cname_base_surf: pygame.Surface | None = None

        # frames
        self.character_frames: dict[str, settings.AniFrames] | None = None
        self.level_frames = None
        self.overlay_frames = None

        # assets
        self.tmx_maps = None
        self.sounds = None
        self.font = None
        self.level_frames: dict | None = None
        self.tmx_maps: settings.MapDict | None = None
        self.overlay_frames: dict[str, pygame.Surface] | None = None
        self.font: pygame.font.Font | None = None
        self.sounds: settings.SoundDict | None = None
        pygame.init()
        self.screen = pygame.display.set_mode((
            settings.SCREEN_WIDTH,
            settings.SCREEN_HEIGHT,
        ))
        pygame.display.set_caption('PyDew')
        self.clock = pygame.time.Clock()
        self.running = True
        self.load_assets()

        # game setup
        self.running = True
        self.clock = pygame.time.Clock()

        # screens
        self.main_menu = MainMenu(self.switch_state)
        self.pause_menu = PauseMenu(self.switch_state)
        self.settings_menu = SettingsMenu(self.switch_state, self.sounds)
        self.level = Level(self, self.tmx_maps, self.character_frames, self.level_frames, self.overlay_frames, self.font, self.sounds, self.switch_state)

        self.screens = {
            GameState.MAIN_MENU: self.main_menu,
            GameState.PAUSE: self.pause_menu,
            GameState.SETTINGS: self.settings_menu,
            GameState.LEVEL: self.level
        }

        self.current_state = GameState.MAIN_MENU

        self.dm = DialogueManager(self.level.all_sprites, self.tb_cname_base_surf, self.tb_main_text_base_surf)

    def switch_state(self, state):
        self.current_state = state

    def load_assets(self):
        self.tmx_maps = support.tmx_importer('data/maps')

        # frames
        self.level_frames = {
            'animations': support.animation_importer('images', 'animations'),
            'soil': support.import_folder_dict('images/soil'),
            'soil water': support.import_folder_dict('images/soil water'),
            'tomato': support.import_folder('images/plants/tomato'),
            'corn': support.import_folder('images/plants/corn'),
            'rain drops': support.import_folder('images/rain/drops'),
            'rain floor': support.import_folder('images/rain/floor'),
            'objects': support.import_folder_dict('images/objects')
        }
        self.overlay_frames = support.import_folder_dict('images/overlay')
        self.character_frames = support.character_importer('images/characters')
        self._tb_base = pygame.image.load(support.resource_path("images/textbox.png")).convert_alpha()
        self.tb_cname_base_surf = self._tb_base.subsurface(pygame.Rect(0, 0, 212, 67))
        self.tb_main_text_base_surf = self._tb_base.subsurface(pygame.Rect(0, 74, 391, 202))
        prepare_tb_image(self.tb_cname_base_surf, self.tb_main_text_base_surf)

        # sounds
        self.sounds = support.sound_importer('audio', default_volume=0.25)

        self.font = support.import_font(30, 'font/LycheeSoda.ttf')

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            screen = self.screens[self.current_state]
            screen.update(dt)

            pygame.display.update()


if __name__ == '__main__':
    game = Game()
    game.run()
