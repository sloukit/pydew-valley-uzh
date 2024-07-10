import pygame
from src.settings import (
    LAYERS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.sprites import WaterDrop
import random


class Sky:
    def __init__(self, game_time):
        self.display_surface = pygame.display.get_surface()
        self.full_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game_time = game_time

        # color
        self.colors = {
            '6' : (160, 187, 255),
            '12' : (255, 255, 255),
            '18' : (255, 240, 234),
            '20' : (255, 219, 203),
            '24' : (38, 101, 189)
        }
        self.colors_hours = list(self.colors.keys)
        self.colors_rgb = list(self.colors.values())

        self.color = self.get_color()

    def get_color(self):

        # get time
        hour, minute = self.game_time.get_time()
        precise_hour = hour + minute / 60

        # find nearest hours in self.colors
        color_index = 0
        for index, color_hour in enumerate(self.colors_hours):
            if precise_hour < color_hour:
                color_index = index - 1
                break
        else:
            color_index = -1

        # start and end colors
        start_color = list(self.colors_rgb)[color_index]
        end_color = list(self.colors_rgb)[color_index + 1]
        start_hour = int(self.colors_hours)[color_index]
        end_hour = int(self.colors_hours)[color_index + 1]

        # just for time intervals like 23:00 - 7:00
        end_hour = end_hour if end_hour > start_hour else end_hour + 24
        precise_hour = precise_hour if precise_hour >= start_hour else precise_hour + 24

        # calculate color
        color_perc = (precise_hour - start_hour) / (end_hour - start_hour)
        color = [255, 255, 255]
        for index, (start_value, end_value) in enumerate(zip(start_color, end_color)):
            color[index] = int(color_perc * end_value + (1 - color_perc) * start_value)

        return color

    def display(self):

        # draw
        self.color = self.get_color()
        self.full_surf.fill(self.color)
        self.display_surface.blit(self.full_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

class Rain:
    def __init__(self, all_sprites, level_frames, map_size):
        self.all_sprites = all_sprites
        self.floor_w, self.floor_h = map_size
        self.floor_frames = level_frames['rain floor']
        self.drop_frames = level_frames['rain drops']

    def create_floor(self):
        WaterDrop(
            surf=random.choice(self.floor_frames),
            pos=(
                random.randint(0, self.floor_w),
                random.randint(0, self.floor_h),
            ),
            moving=False,
            groups=self.all_sprites,
            z=LAYERS['rain floor'])

    def create_drops(self):
        WaterDrop(
            surf=random.choice(self.drop_frames),
            pos=(
                random.randint(0, self.floor_w),
                random.randint(0, self.floor_h),
            ),
            moving=True,
            groups=self.all_sprites,
            z=LAYERS['rain drops'])

    def update(self):
        self.create_floor()
        self.create_drops()
