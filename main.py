import sys
import pygame

from src import settings
from src import support
from src import level
from src import main_menu


class Game:
    def __init__(self, mm):
        self.main_menu = mm
        self.settings_menu = None
        self.character_frames: dict[str, settings.AniFrames] | None = None
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
        self.running = True
        self.level = level.Level(
            self.tmx_maps,
            self.character_frames,
            self.level_frames,
            self.overlay_frames,
            self.font,
            self.sounds)

    def load_assets(self):
        self.tmx_maps = support.tmx_importer('data/maps')
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

        # sounds
        self.sounds = support.sound_importer('audio', default_volume=0.25)

        self.font = support.import_font(30, 'font/LycheeSoda.ttf')

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            keys = pygame.key.get_just_pressed()
            self.screen.fill('gray')
            self.level.update(dt)
            if self.level.entities["Player"].paused:
                pause_menu = self.level.entities["Player"].pause_menu
                self.settings_menu = False
                if pause_menu.pressed_play:
                    self.level.entities["Player"].paused = (
                        not self.level.entities["Player"].paused
                    )
                    pause_menu.pressed_play = False
                elif pause_menu.pressed_quit:
                    pause_menu.pressed_quit = False
                    self.running = False
                    self.main_menu.menu = True
                    self.level.entities["Player"].paused = False
                    self.main_menu.run()
                elif pause_menu.pressed_settings:
                    self.settings_menu = (
                        self.level.entities["Player"].settings_menu
                    )
                if self.settings_menu and self.settings_menu.go_back:
                    self.settings_menu.go_back = False
                    self.settings_menu = False
                    pause_menu.pressed_settings = False
                if not self.settings_menu:
                    pause_menu.update()
                if self.settings_menu:
                    self.settings_menu.update()
            if self.settings_menu:
                if keys[pygame.K_ESCAPE]:
                    self.settings_menu = False
                    pause_menu.pressed_settings = False

            pygame.display.update()


class MainMenu:
    def __init__(self):
        self.menu = True
        self.screen = pygame.display.set_mode((
            settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT,
        ))
        pygame.init()
        self.font = support.import_font(30, 'font/LycheeSoda.ttf')
        pygame.display.set_caption('PyDew')
        self.clock = pygame.time.Clock()
        self.sounds = support.sound_importer('audio', default_volume=0.25)
        self.main_menu = main_menu.main_menu(self.font, self.sounds["music"])
        self.background = pygame.image.load("images/menu_background/bg.png")
        self.background = pygame.transform.scale(
            self.background, (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.game = Game(self)

    def run(self):
        while self.menu:
            dt = self.clock.tick() / 1000  # noqa: F841
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            if self.main_menu.pressed_play:
                self.sounds["music"].stop()
                self.main_menu.pressed_play = False
                self.game.running = True
                self.game.run()
                self.menu = False
            elif self.main_menu.pressed_quit:
                self.main_menu.pressed_quit = False
                self.menu = False
                pygame.quit()
                sys.exit()
            self.screen.blit(self.background, (0, 0))
            self.main_menu.update()
            pygame.display.update()


if __name__ == '__main__':
    game = MainMenu()
    game.run()
