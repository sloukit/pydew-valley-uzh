from src.settings import *
from src.support import *
from src.level import Level
from src.main_menu import MainMenuInternal
from src.pause_menu import PauseMenu
from src.settings_menu import SettingsMenu



class Game():
    def __init__(self):
        # pygame
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.init()
        pygame.display.set_caption('PyDew')

        # variables 
        self.gamestate = "main menu"
        self.playing_gamestate = "unpaused"
        self.font = import_font(30, 'font/LycheeSoda.ttf')
        self.clock = pygame.time.Clock()
        self.sounds = sound_importer('audio', default_volume=0.25)
        

        self.main_menu = MainMenuInternal(self.font, self.sounds["music"])
        self.pause_menu = PauseMenu(self.font)
        self.settings_menu = SettingsMenu(self.font, self.sounds["music"])
        self.background = pygame.transform.scale(pygame.image.load("images/menu_background/bg.png"), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.running = True

        # assets
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
        
        self.level = Level(self.tmx_maps, self.character_frames, self.level_frames, self.overlay_frames, self.font, self.sounds)

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000
            keys = pygame.key.get_just_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:     
                    self.quit()

            # UPDATE -----------------------------------
            match self.gamestate:
                case "main menu":
                        match self.main_menu.input(keys):
                            case "Play":
                                self.gamestate = "playing"
                                self.level.entities["Player"].paused = False
                                self.playing_gamestate = "unpaused"
                            case "Quit":
                                self.quit()                  

                case "playing":
                    self.level.update(dt)   
                    if keys[pygame.K_ESCAPE]:
                        if self.playing_gamestate == "unpaused": self.playing_gamestate = "paused"
                        else: self.playing_gamestate = "unpaused"
                        

                    match self.playing_gamestate:
                        case "unpaused":
                            self.level.entities["Player"].paused = False

                        case "paused":
                            self.level.entities["Player"].paused = True
                            match self.pause_menu.input(keys):
                                case "resume":
                                    self.level.entities["Player"].paused = False
                                    self.playing_gamestate = "unpaused"
                                case "options":
                                    self.playing_gamestate = "options"
                                case "main menu":
                                    self.gamestate = "main menu"
                                    self.playing_gamestate = "unpaused"

                        case "options":
                            self.level.entities["Player"].paused = True
                            match self.settings_menu.input(keys):
                                case "back":
                                    self.playing_gamestate = "paused"
                                


            # DRAW ------------------------------------
            self.screen.fill('gray')

            match self.gamestate:
                case "main menu":
                    self.screen.blit(self.background, (0, 0))
                    self.main_menu.draw()

                case "playing":
                    self.level.draw(dt)

                    match self.playing_gamestate:
                        case "unpaused":
                            pass
                        case "paused":
                            self.pause_menu.draw()
                        case "options":
                            self.settings_menu.draw()
            

            pygame.display.update()

    def quit(self):
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = Game()
    game.run()