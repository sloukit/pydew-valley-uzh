import pygame
from .settings import *


class MainMenuInternal:
    def __init__(self, font, music):
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.font = font
        self.index = 0
        self.music = music

        # options
        self.width = 400
        self.space = 10
        self.padding = 8
        self.pressed_play = False
        self.pressed_quit = False
        # entries
        self.options = ("Play", "Quit")
        
        self.music.play() 
        # create the text surfaces
        self.text_surfs = []
        self.total_height = 0

        for item in self.options:
            text_surf = self.font.render(item, False, 'Black')
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)

        self.total_height += (len(self.text_surfs) - 1) * self.space
        self.menu_top = SCREEN_HEIGHT / 2 - self.total_height / 2
        self.main_rect = pygame.Rect(SCREEN_WIDTH / 2 - self.width / 2, self.menu_top, self.width, self.total_height)

        # buy / sell text surface

    def input(self, keys):
        self.index = (self.index + int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])) % len(self.options)

        if keys[pygame.K_SPACE]:
            current_item = self.options[self.index]
            return current_item
        
    def show_entry(self, text_surf, top, index, text_index):
        # background
        bg_rect = pygame.Rect(self.main_rect.left, top, self.width, text_surf.get_height() + (self.padding * 2))
        pygame.draw.rect(self.display_surface, 'White', bg_rect, 0, 4)

        # text
        text_rect = text_surf.get_frect(midleft=(self.main_rect.left + (self.main_rect.width/2)-text_surf.get_width()/2, bg_rect.centery))
        self.display_surface.blit(text_surf, text_rect)

        # selected
        if index == text_index:
            pygame.draw.rect(self.display_surface, 'black', bg_rect, 4, 4)

    def draw(self):
        text_surf = self.font.render('Main Menu', False, 'Black')
        text_rect = text_surf.get_frect(midtop=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20))

        pygame.draw.rect(self.display_surface, 'White', text_rect.inflate(10, 10), 0, 4)
        self.display_surface.blit(text_surf, text_rect)

        for text_index, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + text_index * (text_surf.get_height() + (self.padding * 2) + self.space)
            self.show_entry(text_surf, top, self.index, text_index)
