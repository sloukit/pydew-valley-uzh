import pygame
from src.settings import (
    OVERLAY_POSITIONS,
)
from src.support import import_font
from math import pi, sin, cos


class Overlay:
    def __init__(self, entity, overlay_frames, game_time):

        # general setup
        self.display_surface = pygame.display.get_surface()
        self.player = entity

        # imports
        self.overlay_frames = overlay_frames
        self.clock = Clock(game_time)

    def display(self):

        # tool
        tool_surf = self.overlay_frames[self.player.current_tool]
        tool_rect = tool_surf.get_frect(midbottom=OVERLAY_POSITIONS['tool'])
        self.display_surface.blit(tool_surf, tool_rect)

        # seeds
        seed_surf = self.overlay_frames[self.player.current_seed]
        seed_rect = seed_surf.get_frect(midbottom=OVERLAY_POSITIONS['seed'])
        self.display_surface.blit(seed_surf, seed_rect)

        # clock
        self.clock.display()

class Clock:
    def __init__(self, game_time, type = 'analog'):

        # setup
        self.display_surface = pygame.display.get_surface()
        self.game_time = game_time

        # dimensions
        self.left = 20
        self.top = 20

        # analog
        if type == 'analog':
            width, height = 80, 80
            self.center = pygame.math.Vector2(self.left + width / 2, self.top + height / 2)
            self.hand_lenght = width / 3

            self.rect = pygame.Rect(self.left, self.top, width, height)
            self.display = self.display_analog

        elif type == 'digital':
            width, height = 100, 50
            self.font = import_font(40, 'font/LycheeSoda.ttf')

            self.rect = pygame.Rect(self.left, self.top, width, height)
            self.display = self.display_digital

    def display_analog(self):

        # get time
        time = self.game_time.get_time()
        hour = time[0] % 12
        minute = time[1]

        # frame
        pygame.draw.rect(self.display_surface, 'White', self.rect, 0, 10)
        pygame.draw.rect(self.display_surface, 'Black', self.rect, 5, 10)
        
        # hands position
        hour_hand_angle = 2 * pi * (hour * 60 + minute) / (12 * 60) - pi / 2
        minute_hand_angle = 2 * pi * minute / 60 - pi / 2
        hour_vector = self.center + 0.75 * self.hand_lenght * pygame.math.Vector2(cos(hour_hand_angle), sin(hour_hand_angle)) 
        minute_vector = self.center + self.hand_lenght * pygame.math.Vector2(cos(minute_hand_angle), sin(minute_hand_angle))

        # draw hands
        pygame.draw.line(self.display_surface, 'Black', self.center, minute_vector, 5)
        pygame.draw.line(self.display_surface, 'Black', self.center, hour_vector, 5)
        pygame.draw.circle(self.display_surface, 'Black', self.center, 4)

    def display_digital(self):

        # get time
        time = self.game_time.get_time()
        hour = time[0]
        minute = time[1]

        if hour < 10:
            # if hours are less than 10, add a 0 to stay in the hh:mm format
            hour_text = f'0{hour}'
        else:
            hour_text = f'{hour}'

        if (minute < 10):
            # if minutes are less than 10, add a 0 to stay in the hh:mm format
            minute_text = f'0{minute}'
        else:
            minute_text = f'{minute}'

        # rects and surfs
        pady = 2

        colon_surf = self.font.render(':', False, 'Black')
        colon_rect = colon_surf.get_frect(center = (self.rect.centerx, self.rect.centery + pady))

        hour_surf = self.font.render(str(hour_text), False, 'Black')
        hour_rect = hour_surf.get_frect(midright = (self.rect.centerx - colon_rect.width, self.rect.centery + pady))

        minute_surf = self.font.render(str(minute_text), False, 'Black')
        minute_rect = minute_surf.get_frect(midleft = (self.rect.centerx + colon_rect.width, self.rect.centery + pady))

        # display
        pygame.draw.rect(self.display_surface, 'White', self.rect, 0, 4)
        pygame.draw.rect(self.display_surface, 'Black', self.rect, 4, 4)
        self.display_surface.blit(colon_surf, colon_rect)
        self.display_surface.blit(hour_surf, hour_rect)
        self.display_surface.blit(minute_surf, minute_rect)
