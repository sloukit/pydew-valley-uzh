import pygame
from src.settings import *



class Overlay:
    def __init__(self, entity, overlay_frames):

        # general setup
        self.display_surface = pygame.display.get_surface()
        self.player = entity

        # imports
        self.overlay_frames = overlay_frames

    def display(self, time):

        # tool

        tool_surf = self.overlay_frames[self.player.get_current_tool_string()]

        tool_rect = tool_surf.get_frect(midbottom=OVERLAY_POSITIONS['tool'])
        self.display_surface.blit(tool_surf, tool_rect)

        # seeds

        seed_surf = self.overlay_frames[self.player.get_current_seed_string()]

        seed_rect = seed_surf.get_frect(midbottom=OVERLAY_POSITIONS['seed'])
        self.display_surface.blit(seed_surf, seed_rect)

        # clock
        font = pygame.font.SysFont('Arial', 30)  # font/size is temporary


        hours = str(time[0]).rjust(2, "0")  # if hours are less than 10, add a 0 to stay in the hh:mm format
        minutes = str(time[1]).rjust(2, "0")  # if minutes are less than 10, add a 0 to stay in the hh:mm format
        # if time[0] < 10:
        #     hours = f"0{time[0]}"
        # else:
        #     hours = f"{time[0]}"

        # if (time[1] < 10):
        #     minutes = f"0{time[1]}"  # if minutes are less than 10, add a 0 to stay in the hh:mm format
        # else:
        #     minutes = f"{time[1]}"

        text_surface = font.render(f"{hours}:{minutes}", False, (255, 255, 255))

        self.display_surface.blit(text_surface, (10, 10))
