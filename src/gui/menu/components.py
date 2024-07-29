import pygame
from pygame.math import Vector2 as vector
from pygame.mouse import get_pos as mouse_pos

from src.controls import Control
from src.support import resource_path


class Component:
    def __init__(self, rect):
        self.display_surface = pygame.display.get_surface()
        self.initial_rect = rect.copy()
        self.rect = rect

        self.animation_active = False
        self.is_press_active = False

        self.press_animation_steps = [-10]
        self.release_animation_steps = [10, 0]
        self.animation_steps = self.press_animation_steps

        self.animation_speed = 0.15
        self.current_step_index = 0

        self.initial_x = 0
        self.current_x = 0
        self.target_x = self.animation_steps[self.current_step_index]

    # animation controls
    def start_press_animation(self):
        self.animation_active = True
        self.is_press_active = True

    def start_release_animation(self):
        if self.is_press_active:
            self.extend_animation_with_release_steps()
        else:
            self.animation_steps = self.release_animation_steps
            self.animation_active = True

        self.is_press_active = False

    def reset_animation(self):
        self.animation_active = False
        self.is_press_active = False
        self.animation_steps = self.press_animation_steps
        self.current_step_index = 0
        self.target_x = self.animation_steps[self.current_step_index]
        self.current_x = 0
        self.update_rect(0)

    # animation
    def extend_animation_with_release_steps(self):
        press_list = self.press_animation_steps
        release_list = self.release_animation_steps
        self.animation_steps = press_list + release_list

    def advance_to_next_step(self):
        if self.is_last_step():
            if not self.is_press_active:
                self.reset_animation()
        else:
            self.current_step_index += 1
            self.update_rect(self.target_x)
            self.target_x = self.animation_steps[self.current_step_index]

    def has_reached_target_x(self, x):
        return abs(self.current_x - self.target_x) < abs(x)

    def is_last_step(self):
        return self.current_step_index >= len(self.animation_steps) - 1

    def animate(self, dt):
        if self.animation_active:
            direction = 1 if self.target_x > self.current_x else -1
            x_increment = direction * self.animation_speed * dt * 1000
            if self.has_reached_target_x(x_increment):
                self.advance_to_next_step()
            else:
                self.current_x += x_increment
                self.update_rect(self.current_x)

    # draw
    def draw(self, surface):
        pygame.draw.rect(surface, 'red', self.rect, 0, 4)

    # update
    def update_rect(self, x):
        self.rect.width = self.initial_rect.width + x
        self.rect.height = self.initial_rect.height + x
        self.rect.center = self.initial_rect.center

    def update(self, dt):
        self.animate(dt)


class Button(Component):
    def __init__(self, text, font, rect, offset):
        super().__init__(rect)
        self.initial_rect = rect.copy()
        self.font_size = 30
        self.font = font
        self.text = text
        self.offset = vector(offset)
        self.color = 'White'
        self.hover_active = False

        self.display_surface = None

    def mouse_hover(self):
        return self.rect.collidepoint(mouse_pos())

    # draw
    def draw_text(self):
        text_surf = self.font.render(self.text, False, 'Black')
        text_rect = text_surf.get_frect(center=self.rect.center)
        self.display_surface.blit(text_surf, text_rect)

    def draw_hover(self):
        if self.mouse_hover():
            self.hover_active = True
            pygame.draw.rect(self.display_surface, 'Black', self.rect, 4, 4)
        else:
            self.hover_active = False

    def draw(self, surface):
        self.display_surface = surface
        pygame.draw.rect(self.display_surface, self.color, self.rect, 0, 4)
        self.draw_text()
        self.draw_hover()


class KeySetup(Component):
    def __init__(self, name: str, control: Control, unicode: str, pos: tuple[int, int], image: pygame.Surface):
        # params
        self.name = name
        self.value = control.control_value
        self.title = control.text
        self.unicode = unicode

        # design
        self.font = pygame.font.Font(resource_path('font/LycheeSoda.ttf'), 30)
        self.hover_active = False
        self.bg_color = 'grey'

        # rect
        self.pos = pos
        self.rect = pygame.Rect(pos, (300, 50))
        self.offset = vector()
        super().__init__(self.rect)

        # symbol
        self.symbol_image = image
        self.symbol_image = pygame.transform.scale(self.symbol_image, (40, 40))
        midright = self.rect.midright - vector(10, 0)
        self.symbol_image_rect = self.symbol_image.get_rect(midright=midright)

    def hover(self, offset: pygame.math.Vector2):
        self.offset = vector(offset)
        self.hover_active = self.rect.collidepoint(mouse_pos() - self.offset)
        return self.hover_active

    # draw
    def draw_key_name(self):
        text_surf = self.font.render(self.title, False, 'Black')
        midleft = (self.rect.left + 10, self.rect.centery)
        text_rect = text_surf.get_frect(midleft=midleft)
        rect = text_rect.inflate(10, 10)
        pygame.draw.rect(self.surface, 'White', rect, 0, 4)
        self.surface.blit(text_surf, text_rect)

    def draw_symbol(self):
        text_surf = self.font.render(self.unicode, False, 'White')
        text_rect = text_surf.get_frect(center=self.symbol_image_rect.center)
        self.surface.blit(self.symbol_image, self.symbol_image_rect)
        self.surface.blit(text_surf, text_rect)

    def draw(self, surface: pygame.Surface):
        self.surface = surface
        pygame.draw.rect(self.surface, self.bg_color, self.rect, 0, 4)
        self.draw_key_name()
        self.draw_symbol()


class Slider:
    def __init__(self, rect, min_value, max_value, init_value, sounds, offset):
        # main setup
        self.surface = None
        self.rect = rect
        self.offset = vector(offset)

        # values
        self.min_value = min_value
        self.max_value = max_value
        self.value = init_value

        # sounds
        self.sounds = sounds
        self.font = pygame.font.Font(resource_path('font/LycheeSoda.ttf'), 30)

        # knob
        self.knob_radius = 10
        self.drag_active = False

    def get_value(self):
        return self.value

    # events
    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos() - self.offset):
                self.drag_active = True
                return True

        if self.drag_active:

            if event.type == pygame.MOUSEBUTTONUP:
                self.drag_active = False
                return True

            if event.type == pygame.MOUSEMOTION:
                diff = self.max_value - self.min_value
                origin_x = mouse_pos()[0] - self.offset.x - self.rect.left
                size = self.rect.width - 10
                self.value = self.min_value + diff * origin_x / size
                self.value = max(self.min_value, min(self.max_value, self.value))
                self.update_volume()
                return True

        return False

    def update_volume(self):
        self.sounds['music'].set_volume(min((self.value / 1000), 0.4))
        for key in self.sounds:
            if key != 'music':
                self.sounds[key].set_volume((self.value / 100))

    # draw
    def draw_value(self):
        text_surf = self.font.render(str(int(self.value)), False, 'Black')
        midtop = (self.rect.centerx, self.rect.bottom + 10)
        text_rect = text_surf.get_frect(midtop=midtop)
        self.surface.blit(text_surf, text_rect)

    def draw_knob(self):
        value = (self.value - self.min_value)
        diff = (self.max_value - self.min_value)
        knob_x = self.rect.left + (self.rect.width - 10) * value / diff
        color = (232, 207, 166)
        center = (int(knob_x), self.rect.centery)
        pygame.draw.circle(self.surface, color, center, self.knob_radius)

    def draw_rect(self):
        # border
        border_color = (220, 185, 138)
        pygame.draw.rect(self.surface, border_color, self.rect, 0, 4)

        # bg
        bg_color = (243, 229, 194)
        rect = self.rect.inflate(-4, -4)
        pygame.draw.rect(self.surface, bg_color, rect, 0, 4)

    def draw(self, surface):
        self.surface = surface
        self.draw_rect()
        self.draw_knob()
        self.draw_value()
