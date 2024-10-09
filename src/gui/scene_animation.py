import time
from typing import Iterable

import pygame

from src.camera.camera_target import CameraTarget


class SceneAnimation:
    def __init__(self, targets: list[CameraTarget]):
        self.targets = targets
        self.current_index = 0
        # This is used so the camera can focus on the desired area instead of the player
        self.rect = pygame.FRect(0, 0, 8, 8)
        self.current_pos = pygame.Vector2(targets[0].pos if targets else (0, 0))
        self.rect.center = self.current_pos
        self.active = False
        self.pause_start_time = None

    def get_current_position(self):
        return self.current_pos

    def clear(self):
        self.targets.clear()

    def set_target_points(self, targets: Iterable[CameraTarget]):
        self.targets.clear()
        self.targets.extend(targets)
        self.reset()

    def start(self):
        if not self.targets:
            return
        self.active = True

    def reset(self):
        self.current_index = 0
        if self.targets:
            self.rect.center = self.targets[0].pos
            self.current_pos = pygame.Vector2(self.targets[0].pos)
        self.active = False
        self.pause_start_time = None

    def pause_active(self):
        return self.pause_start_time is not None

    def pause_not_finished(self):
        elapsed_pause_time = time.time() - self.pause_start_time
        pause_duration = self.targets[self.current_index].pause
        return elapsed_pause_time < pause_duration

    def reset_pause(self):
        self.pause_start_time = None
        self.current_index += 1

    def move_towards_target(self, dt):
        current_target = self.targets[self.current_index]
        target_pos = pygame.Vector2(current_target.pos)
        direction = target_pos - self.current_pos
        distance_to_target = direction.length()

        if distance_to_target <= current_target.speed * dt:
            self.rect.center = self.current_pos = target_pos
            self.pause_start_time = time.time()
        else:
            direction = direction.normalize()
            self.current_pos += direction * current_target.speed * dt
            self.rect.center = self.current_pos

    def has_more_targets(self):
        return self.current_index < len(self.targets)

    __bool__ = has_more_targets

    def animate(self, dt):
        if not self.active:
            return

        if self.pause_active():
            if self.pause_not_finished():
                return
            self.reset_pause()

        if self.has_more_targets():
            self.move_towards_target(dt)
        else:
            self.active = False
            self.reset()

    def update(self, dt):
        self.animate(dt)

        # check the if the zoom is allowed
        self.zoom_allowed = self.active
