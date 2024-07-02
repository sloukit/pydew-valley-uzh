from src.settings import *
from src.support import *
from src.level import Level
from src.main_menu import main_menu
from src.settings_menu import settings_menu
from src.pause_menu import pause_menu


class GameStateManager:
    def __init__(self, initial_state) -> None:
        self.current_state = initial_state

    def get_state(self):
        return self.current_state
    
    def set_state(self, state):
        self.current_state = state

# place holder class to test the different gamestates
class Start:
    def __init__(self, gamestate) -> None:
        self.display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.gamestate = gamestate

    def run(self):
        # placeholder for the start state
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                self.gamestate.set_state('level')
        # self.display.fill('blue')  # placeholder for start screen rendering
        pygame.display.update()


class Game():
    def __init__(self) -> None:
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
        self.running = True
        self.load_assets()

        # added logic for the different gamestates

        # initial_state means where the begin state starts, for example if we add a start screen, it could be 'start'
        self.gamestate = GameStateManager(initial_state='menu')
        self.start = Start(gamestate=self.gamestate)
        self.main_menu = MainMenu(gamestate=self.gamestate)
        self.level = Level(self.tmx_maps, self.character_frames, self.level_frames, self.overlay_frames, self.font, self.sounds)
        self.settings_menu = settings_menu(font=self.font, sounds=self.sounds)
        self.pause_menu = pause_menu(font=self.font)

        # a dict with all the keys for the game states
        self.states = {
            'menu': self.main_menu,
            'start': self.start,  # placeholder for now
            'level': self.level,
            'pause': self.pause_menu,  # need to add this to player object
            'settings': self.settings_menu  # need to add this to player object
            }
        self.settings_menu = False

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

    # main game loop
    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # need to look at this clause
                if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                    if self.gamestate.get_state() == 'level':
                        self.gamestate.set_state('pause')
                    elif self.gamestate.get_state() == 'pause':
                        self.gamestate.set_state('level')
                    elif self.gamestate.get_state() == 'settings':
                        self.gamestate.set_state('pause')
            keys = pygame.key.get_just_pressed()
            self.screen.fill('gray')
            self.level.update(dt)

            current_state = self.states[self.gamestate.get_state()]
            # in order to let this work you have to create a run method in every class you want to use gamestates.
            # have an update method and a pygame.display.update() call and it should work.
            current_state.run()

            if self.gamestate.get_state() == 'level':
                self.level.update(dt)

            # if self.level.entities["Player"].paused:
            #     pause_menu = self.level.entities["Player"].pause_menu
            #     self.settings_menu = False

            #     if pause_menu.pressed_play:
            #         self.level.entities["Player"].paused = not self.level.entities["Player"].paused
            #         pause_menu.pressed_play = False
            #     elif pause_menu.pressed_quit:
            #         pause_menu.pressed_quit = False
            #         self.running = False
            #         self.main_menu.menu = True
            #         self.level.entities["Player"].paused = False
            #         self.main_menu.run()
            #     elif pause_menu.pressed_settings:
            #         self.settings_menu = self.level.entities["Player"].settings_menu
            #     if self.settings_menu and self.settings_menu.go_back:
            #         self.settings_menu.go_back = False
            #         self.settings_menu = False
            #         pause_menu.pressed_settings = False

            #     if not self.settings_menu:
            #         pause_menu.update()
            #     if self.settings_menu:
            #         self.settings_menu.update()
            # if self.settings_menu != False:
            #     if keys[pygame.K_ESCAPE]:
            #         self.settings_menu = False
            #         pause_menu.pressed_settings = False

            pygame.display.update()


class MainMenu:
    def __init__(self, gamestate) -> None:
        self.menu = True
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.init()
        self.font = import_font(30, 'font/LycheeSoda.ttf')
        pygame.display.set_caption('PyDew')
        self.clock = pygame.time.Clock()
        self.sounds = sound_importer('audio', default_volume=0.25)
        self.main_menu = main_menu(self.font, self.sounds["music"])
        self.background = pygame.image.load("images/menu_background/bg.png")
        self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.gamestate = gamestate

    def run(self):
        # dt = self.clock.tick() / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.start_game()
        if self.main_menu.pressed_play:
            self.start_game()
        elif self.main_menu.pressed_quit:
            self.main_menu.pressed_quit = False
            self.menu = False
            pygame.quit()
            sys.exit()
        self.screen.blit(self.background, (0, 0))
        self.main_menu.update()
        pygame.display.update()

    # this can be the start of the game for example
    def start_game(self):
        self.sounds['music'].stop()
        self.main_menu.pressed_play = False
        self.gamestate.set_state('start')

if __name__ == '__main__':
    game = Game()
    game.run()