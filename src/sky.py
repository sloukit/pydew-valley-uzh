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
        self.start_color = [255, 255, 255]
        self.end_color = (38, 101, 189)
        self.game_time = game_time

    def display(self):
        # get time
        time = self.game_time.get_time()
        hour = time[0]
        minute = time[1]
        num_minutes = hour * 60 + minute

        # 0 for noon, 1 for midnight
        normalized_minutes = abs(num_minutes / (12 * 60) - 1)

        # set color
        for index, value in enumerate(self.end_color):
            self.start_color[index] = int(255 * (1 - normalized_minutes) + value * normalized_minutes)

        self.full_surf.fill(self.start_color)
        self.display_surface.blit(
            self.full_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

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
