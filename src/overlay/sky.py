import random

import pygame

from src.enums import Layer
from src.overlay.game_time import GameTime
from src.settings import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from src.sprites.water_drop import WaterDrop


class Sky:
    def __init__(self, game_time: GameTime):
        self.display_surface = pygame.display.get_surface()
        self.game_time = game_time
        self.full_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        # color
        self.colors = {
            "6": (160, 187, 255),
            "12": (255, 255, 255),
            "18": (255, 240, 234),
            "20": (255, 219, 203),
            "22": (38, 101, 189),
        }
        self.colors_hours = list(map(int, self.colors.keys()))
        self.colors_rgb = list(self.colors.values())

        self.color = self.get_color()

    def get_color(self):
        return self.colors["12"]

    def display(self):
        # draw
        self.color = self.get_color()
        self.full_surf.fill(self.color)
        self.display_surface.blit(
            self.full_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT
        )


class Rain:
    def __init__(self, all_sprites, level_frames, map_size=None):
        if map_size is None:
            self.floor_w, self.floor_h = (0, 0)
        else:
            self.set_floor_size(map_size)

        self.all_sprites = all_sprites
        self.floor_frames = level_frames["rain floor"]
        self.drop_frames = level_frames["rain drops"]

    def set_floor_size(self, size: tuple[int, int]):
        self.floor_w, self.floor_h = size

    def create_floor(self):
        WaterDrop(
            surf=random.choice(self.floor_frames),
            pos=(
                random.randint(0, self.floor_w),
                random.randint(0, self.floor_h),
            ),
            moving=False,
            groups=self.all_sprites,
            z=Layer.RAIN_FLOOR,
        )

    def create_drops(self):
        WaterDrop(
            surf=random.choice(self.drop_frames),
            pos=(
                random.randint(0, self.floor_w),
                random.randint(0, self.floor_h),
            ),
            moving=True,
            groups=self.all_sprites,
            z=Layer.RAIN_DROPS,
        )

    def update(self):
        self.create_floor()
        self.create_drops()
