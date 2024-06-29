import pygame
from .settings import *

class Slider:
    def __init__(self, x, y, width, height, min_value, max_value, initial_value, sounds):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.sounds = sounds
        self.value = initial_value
        self.clicking = False
        self.knob_radius = 10

    def draw(self, surface):
        pygame.draw.rect(surface, (220, 185, 138), self.rect, 0, 4)
        pygame.draw.rect(surface, (243, 229, 194), self.rect.inflate(-4, -4), 0, 4)
        knob_x = self.rect.left + (self.rect.width - 10) * (self.value - self.min_value) / (self.max_value - self.min_value)
        pygame.draw.circle(surface, (232, 207, 166), (int(knob_x), self.rect.centery), self.knob_radius)

    def update(self):
        m_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:
            if self.rect.collidepoint(m_pos):
                self.clicking = True
        else:
            self.clicking = False
        if pygame.mouse.get_rel()[0] and self.clicking:
            self.value = self.min_value + (self.max_value - self.min_value) * (m_pos[0] - self.rect.left) / (self.rect.width - 10)
            self.value = max(self.min_value, min(self.max_value, self.value))
            self.sounds['music'].set_volume(min((self.value / 1000), 0.4))
            for key in self.sounds:
                if key != 'music':
                    self.sounds[key].set_volume((self.value / 100))

    def get_value(self):
        return self.value
