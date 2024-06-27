from .settings import *

class Overlay:
	def __init__(self,entity, overlay_frames):

		# general setup
		self.display_surface = pygame.display.get_surface()
		self.player = entity

		# imports 
		self.overlay_frames = overlay_frames

	def display(self):

		# tool
		tool_surf = self.overlay_frames[self.player.current_tool]
		tool_rect = tool_surf.get_frect(midbottom = OVERLAY_POSITIONS['tool'])
		self.display_surface.blit(tool_surf,tool_rect)

		# seeds
		seed_surf = self.overlay_frames[self.player.current_seed]
		seed_rect = seed_surf.get_frect(midbottom = OVERLAY_POSITIONS['seed'])
		self.display_surface.blit(seed_surf,seed_rect)