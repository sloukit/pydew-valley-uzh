import pygame
from .settings import *

class Time:
    def __init__(self):
        self.game_hour = 12      # game starts at this hour
        self.game_minute = 0     # game starts at this minute

        # number of seconds per in game minute (reference - stardew valley each minute is 0.7 seconds)
        self.seconds_per_game_minute = 0.7

        # gets the creation time in ticks
        self.last_time = pygame.time.get_ticks()

    def increment_time(self):

        # day-night cycle
        current_time = pygame.time.get_ticks()

        # if more than seconds_per_game_minute has passed, update clock
        if (current_time - self.last_time > self.seconds_per_game_minute * 1000):
            self.last_time = current_time
            self.game_minute += 1

            # minutes cycle every 60 in game minutes
            if (self.game_minute > 59):
                self.game_minute = 0
                self.game_hour += 1
            if (self.game_hour > 23):    # hours cycle every 24 in game hours
                self.game_hour = 0

    def set_time(self, hours, minutes):
        self.game_hour = hours
        self.game_minute = minutes

    def get_time(self):
        return (self.game_hour, self.game_minute)