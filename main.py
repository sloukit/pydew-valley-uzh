from src.settings import *
from src.support import *
from src.level import Level
from src.menus import MainMenu, PauseMenu, SettingsMenu

class Game:
    def __init__(self, game_state):
        self.game_state = game_state

        # basics
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption('PyDew')

        # loading assets
        self.character_frames = None
        self.level_frames = None
        self.tmx_maps = None
        self.overlay_frames = None
        self.font = None
        self.sounds = None
        self.load_assets()

        # the level
        self.level = Level(self.tmx_maps, self.character_frames, self.level_frames, self.overlay_frames, self.font, self.sounds, game_state)

        # menus
        self.pause_menu = PauseMenu(self.font, self.game_state)
        self.settings_menu = SettingsMenu(self.font, self.game_state, sounds=self.sounds)

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

        # sounds
        self.sounds = sound_importer('audio', default_volume=0.25)

        self.font = import_font(30, 'font/LycheeSoda.ttf')

    def run(self):
        while self.game_state[-1] == 'game':
            dt = self.clock.tick() / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    while self.game_state[-1] != 'quit':
                        self.game_state.pop()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.pause_menu.bg = self.screen.copy()
                        self.settings_menu.bg = self.screen.copy()
                        self.game_state.append('pause_menu')


            self.screen.fill('gray')
            self.level.update(dt)

            pygame.display.update()


class Manager:
    def __init__(self):
        self.states = ['quit', 'main_menu']
        self.game = Game(self.states)
        menu_bg = pygame.image.load(join('images', 'menu_background', 'bg.png')).convert()
        self.main_menu = MainMenu(self.game.font, self.states, bg=menu_bg)

    def run(self):
        while True:
            match(self.states[-1]):
                case 'main_menu':
                    self.main_menu.run()
                case 'game':
                    self.game.run()
                case 'pause_menu':
                    self.game.pause_menu.run()
                case 'settings_menu':
                    self.game.settings_menu.run()
                case 'shop_menu':
                    self.game.level.shop_menu.run()
                case 'quit':
                    pygame.quit()
                    sys.exit()
                case _:
                    print("\033[91munexpected state\033[0m")
                    self.states = ['quit']

if __name__ == '__main__':
    Manager().run()
