import pygame
from src.settings import OVERLAY_POSITIONS
from src.gui.health_bar import HealthProgressBar

class Overlay:
    def __init__(self, entity, overlay_frames):

        # general setup
        self.display_surface = pygame.display.get_surface()
        self.player = entity

        # imports
        self.overlay_frames = overlay_frames

        # ui objects
        self.health_bar = HealthProgressBar(100)

    def display(self, time):

        # seeds
        seed_surf = self.overlay_frames[self.player.get_current_seed_string()]
        seed_rect = seed_surf.get_frect(midbottom=OVERLAY_POSITIONS['seed'])
        self.display_surface.blit(seed_surf, seed_rect)

        # tool
        tool_surf = self.overlay_frames[self.player.get_current_tool_string()]
        tool_rect = tool_surf.get_frect(midbottom=OVERLAY_POSITIONS['tool'])
        self.display_surface.blit(tool_surf, tool_rect)

        # clock
        font = pygame.font.SysFont('Arial', 30)  # font/size is temporary
        # if hours are less than 10, add a 0 to stay in the hh:mm format
        hours = str(time[0]).rjust(2, "0")
        # if minutes are less than 10, add a 0 to stay in the hh:mm format
        minutes = str(time[1]).rjust(2, "0")

        text_surface = font.render(f"{hours}:{minutes}", False, 'white')
        text_rect = text_surface.get_rect(topright=OVERLAY_POSITIONS['clock'])
        self.display_surface.blit(text_surface, text_rect)

        # health bar
        self.health_bar.draw(self.display_surface)
