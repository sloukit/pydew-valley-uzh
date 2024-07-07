import pygame
from src.settings import OVERLAY_POSITIONS


class Overlay:
    def __init__(self, entity, overlay_frames):

        # general setup
        self.display_surface = pygame.display.get_surface()
        self.player = entity

        # imports
        self.overlay_frames = overlay_frames

    def display(self, time):

        # tool
        tool_surf = self.overlay_frames[self.player.current_tool]
        tool_rect = tool_surf.get_frect(midbottom=OVERLAY_POSITIONS['tool'])
        self.display_surface.blit(tool_surf, tool_rect)

        # seeds
        seed_surf = self.overlay_frames[self.player.current_seed]
        seed_rect = seed_surf.get_frect(midbottom=OVERLAY_POSITIONS['seed'])
        self.display_surface.blit(seed_surf, seed_rect)

        # clock
        font = pygame.font.SysFont('Arial', 30)  # font/size is temporary

        # hours, minutes format
        hours = f"0{time[0]}" if time[0] < 10 else f"{time[0]}"
        minutes = f"0{time[1]}" if time[1] < 10 else f"{time[1]}"

        text_surface = font.render(f"{hours}:{minutes}", False, (255, 255, 255))
        self.display_surface.blit(text_surface, (10, 10))
