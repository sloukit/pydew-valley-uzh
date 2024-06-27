import asyncio

from src.settings import *
from src.support import *
from src.level import Level


class Game:
    def __init__(self):
        self.character_frames = None
        self.level_frames = None
        self.tmx_maps = None
        self.overlay_frames = None
        self.font = None
        self.sounds = None
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('PyDew')
        self.clock = pygame.time.Clock()
        self.running = True
        self.load_assets()

        self.level = Level(self.tmx_maps, self.character_frames, self.level_frames, self.overlay_frames, self.font, self.sounds)

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

    async def run(self):
        while True:
            dt = self.clock.tick() / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.screen.fill('gray')
            self.level.update(dt)

            pygame.display.update()
            await asyncio.sleep(0)


if __name__ == '__main__':
    game = Game()
    asyncio.run(game.run())
