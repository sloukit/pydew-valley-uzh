from .settings import *
from .sprites import WaterDrop
from random import choice, randint

class Sky:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.full_surf = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
        self.start_color = [255,255,255]
        self.end_color = (38,101,189)

    def display(self, dt):
        for index, value in enumerate(self.end_color):
            if self.start_color[index] > value:
                self.start_color[index] -= 2 * dt

        self.full_surf.fill(self.start_color)
        self.display_surface.blit(self.full_surf, (0,0), special_flags = pygame.BLEND_RGBA_MULT)


class Rain:
    def __init__(self, all_sprites, level_frames, map_size):
        self.all_sprites = all_sprites
        self.floor_w, self.floor_h = map_size
        self.floor_frames = level_frames['rain floor']
        self.drop_frames = level_frames['rain drops']

    def create_floor(self):
        WaterDrop(
            surf = choice(self.floor_frames), 
            pos = (randint(0,self.floor_w),randint(0,self.floor_h)), 
            moving = False, 
            groups = self.all_sprites, 
            z = LAYERS['rain floor'])

    def create_drops(self):
        WaterDrop(
            surf = choice( self.drop_frames ), 
            pos = (randint(0,self.floor_w),randint(0,self.floor_h)), 
            moving = True, 
            groups = self.all_sprites, 
            z = LAYERS['rain drops'])

    def update(self):
        self.create_floor()
        self.create_drops()