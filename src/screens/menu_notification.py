from collections.abc import Callable

import pygame

from src.enums import GameState
from src.gui.menu.general_menu import GeneralMenu
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH


class NotificationMenu(GeneralMenu):
    def __init__(
        self,
        switch_screen: Callable[[GameState], None],
        message: str,
    ):
        options = ["OK"]
        title = "Notification"
        size = (400, 400)
        self.message = message
        super().__init__(title, options, switch_screen, size)

    def button_action(self, text: str):
        if text == "OK":
            self.switch_screen(GameState.PLAY)
        # if text == "Quit":
        #     self.quit_game()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.KEYDOWN:
            if event.key in [
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_SPACE,
                pygame.K_BACKSPACE,
            ]:
                self.switch_screen(GameState.PLAY)
                return True

        return False

    def draw_title(self):
        super().draw_title()
        top = SCREEN_HEIGHT / 20 + 75
        left = SCREEN_WIDTH // 2

        text_surf = self.font.render(self.message, False, "black")
        text_rect = text_surf.get_frect(top=top, centerx=left)

        bg_rect = pygame.Rect(0, 0, text_rect.width + 40, 50)
        bg_rect.center = text_rect.center

        pygame.draw.rect(self.display_surface, "white", bg_rect, 0, 4)
        self.display_surface.blit(text_surf, text_rect)
