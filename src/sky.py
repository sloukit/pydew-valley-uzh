from .settings import *
from .sprites import WaterDrop
from random import choice, randint

class Sky:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.full_surf = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
        self.start_color = [255,255,255]
        self.end_color = (38,101,189)

        # calculates the increments between the above start and end colors to ensure they all increase/decrease at a constant rate (720 minutes between noon and midnight)
        self.color_increment = [(self.start_color[0] - self.end_color[0]) / 720, 
                                (self.start_color[1] - self.end_color[1]) / 720, 
                                (self.start_color[2] - self.end_color[2]) / 720] 
        
        self.game_hour = 12                             #   game starts at this hour
        self.game_minute = 00                           #   game starts at this minute
        self.seconds_per_minute = 0.7                   #   number of seconds per in game minute (reference - stardew valley each minute is 0.7 seconds)
        self.last_time = pygame.time.get_ticks()        #   gets the creation time in ticks

    def display(self, dt):
        #   DAY / NIGHT CYCLE 
        current_time = pygame.time.get_ticks()
        if(current_time - self.last_time > self.seconds_per_minute * 1000):     # if more than seconds_per_minute has passed, update clock
            self.last_time = current_time                                       
            self.game_minute += 1
            
            if(self.game_minute > 59):  # minutes cycle every 60 in game minutes
                self.game_minute = 0
                self.game_hour += 1
            if(self.game_hour > 23):    # hours cycle every 24 in game hours
                self.game_hour = 0

            # Loop through each index of the current overlay color, then increment it by the above determined increments between noon and midnight
            for index, value in enumerate(self.end_color):
                if (self.game_hour >= 12):
                    self.start_color[index] -= self.color_increment[index]
                    if(self.start_color[index] < 0): self.start_color[index] = 0
                else:
                    self.start_color[index] += self.color_increment[index]
                    if(self.start_color[index] > 255): self.start_color[index] = 255
            
        self.full_surf.fill(self.start_color)
        self.display_surface.blit(self.full_surf, (0,0), special_flags = pygame.BLEND_RGBA_MULT)

    def set_time(self, hours, minutes):
        self.game_hour = hours
        self.game_minute = minutes
        num_of_minutes = hours * 60 + minutes
        
        # if number of minutes is less than noon, add increments to color
        # if number of minutes is greater than noon, subtract increments to color
        if(num_of_minutes < 720):           
            new_color = [self.end_color[0],self.end_color[1],self.end_color[2]]         # darkest color is midnight
            for index, value in enumerate(self.end_color):
                new_color[index] += self.color_increment[index] * num_of_minutes
        else:
            num_of_minutes -= 720
            new_color = [255,255,255]                                                   # brightest color is noon
            for index, value in enumerate(self.end_color):
                new_color[index] -= self.color_increment[index] * num_of_minutes
            
        self.start_color = new_color 
        return

    def get_time(self):
        return (self.game_hour, self.game_minute)


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