import pygame


class Timer:
    def __init__(self, duration, repeat=False, autostart=False, func=None):
        self.duration = duration
        self.start_time = 0
        self.active = False
        self.finished = False
        self.repeat = repeat
        self.func = func

        if autostart:
            self.activate()

    def __bool__(self):
        return self.active

    def activate(self):
        self.active = True
        self.finished = False
        self.start_time = pygame.time.get_ticks()

    def deactivate(self):
        self.active = False
        self.finished = True
        self.start_time = 0
        if self.repeat:
            self.activate()

    def get_progress(self) -> float:
        """returns a value between 0 and 1 that shows the timers progress
        1 means duration finshed"""
        curr = pygame.time.get_ticks()
        return (curr - self.start_time) / self.duration if self.active else 0

    def update(self):
        if self.active:
            if pygame.time.get_ticks() - self.start_time >= self.duration:
                if self.func and self.start_time != 0:
                    self.func()
                self.deactivate()
