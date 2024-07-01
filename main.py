from src.settings import *
from src.support import *
from src.level import Level
from src.main_menu import MainMenuInternal
from src.dialog import DialogueManager


class Game:
    def __init__(self, mm: "MainMenu"):
        self._tb_base = None
        self.tb_main_text_base_surf: pygame.Surface | None = None
        self.tb_cname_base_surf: pygame.Surface | None = None
        self.main_menu: "MainMenu" = mm  # Removing the quotes in this type annotation will cause Python to complain and raise an UnboundLocalError
        self.character_frames: dict[str, AniFrames] | None = None
        self.level_frames: dict | None = None
        self.tmx_maps: MapDict | None = None
        self.overlay_frames: dict[str, pygame.Surface] | None = None
        self.font: pygame.font.Font | None = None
        self.sounds: SoundDict | None = None
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('PyDew')
        self.clock = pygame.time.Clock()
        self.settings_menu = False
        self.running = True
        self.load_assets()
        self.running = True
        self.level = Level(self, self.tmx_maps, self.character_frames, self.level_frames, self.overlay_frames, self.font,
                           self.sounds)
        self.dm = DialogueManager(self.level.all_sprites, self.tb_cname_base_surf, self.tb_main_text_base_surf)

    def load_assets(self):
        self.tmx_maps = tmx_importer('data/maps')
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
        self._tb_base = pygame.image.load(resource_path("images/textbox.png")).convert_alpha()
        self.tb_cname_base_surf = self._tb_base.subsurface(pygame.Rect(0, 0, 212, 67))
        self.tb_main_text_base_surf = self._tb_base.subsurface(pygame.Rect(0, 74, 391, 202))

        # sounds
        self.sounds = sound_importer('audio', default_volume=0.25)

        self.font = import_font(30, 'font/LycheeSoda.ttf')

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
                pause_menu = self.level.entities["Player"].PauseMenu
                self.settings_menu = False
                if pause_menu.pressed_play:
                    self.level.entities["Player"].paused = not self.level.entities["Player"].paused
                    pause_menu.pressed_play = False
                elif pause_menu.pressed_quit:
                    pause_menu.pressed_quit = False
                    self.running = False
                    self.main_menu.menu = True
                    self.level.entities["Player"].paused = False
                    self.main_menu.run()
                elif pause_menu.pressed_settings:
                    self.settings_menu = self.level.entities["Player"].SettingsMenu
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
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.init()
        self.font = import_font(30, 'font/LycheeSoda.ttf')
        pygame.display.set_caption('PyDew')
        self.clock = pygame.time.Clock()
        self.sounds = sound_importer('audio', default_volume=0.25)
        self.main_menu = MainMenuInternal(self.font, self.sounds["music"])
        self.background = pygame.image.load("images/menu_background/bg.png")
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game: Game = Game(self)

    def run(self):
        while self.menu:
            dt = self.clock.tick() / 1000
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
    main_menu = MainMenu()
    main_menu.run()
