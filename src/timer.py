class Timer:
    def __init__(self, duration, repeat=False, autostart=False, func=None):
        self.duration = duration
        self.ticks = 0
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
        self.ticks = 0

    def deactivate(self):
        self.active = False
        self.finished = True
        self.ticks = 0
        if self.repeat:
            self.activate()

    def get_progress(self) -> float:
        # returns a value between 0 and 1 that shows the timers progress
        # 1 means duration finished
        return self.ticks / self.duration if self.active else 0

    def update(self, dt):
        self.ticks += dt
        if self.active:
            if self.ticks >= self.duration:
                while self.ticks >= self.duration:
                    if self.func and self.ticks != 0:
                        self.func()
                    self.ticks -= self.duration
                self.deactivate()
