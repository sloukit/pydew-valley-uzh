from collections.abc import Callable
from typing import Any

import pygame
from pygame.mouse import get_pressed as mouse_buttons

from src import support
from src.client import authn
from src.enums import CustomCursor, GameState
from src.events import SET_CURSOR, post_event
from src.gui.menu.general_menu import GeneralMenu
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH, USE_SERVER

_SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


class MainMenu(GeneralMenu):
    def __init__(
        self,
        switch_screen: Callable[[GameState], None],
        set_token: Callable[[dict[str, Any]], None],
    ) -> None:
        options = ["Play", "Quit", "Enter a Token to Play"]
        title = "Main Menu"
        size = (400, 400)
        super().__init__(title, options, switch_screen, size)
        self.set_token = set_token
        self.input_active = False
        self.token_input = ""
        # TODO revert, this only for debug
        self.play_button_enabled = False  # Initialize as False

        # textbox input
        self.input_active = False
        self.input_box = pygame.Rect(100, 390, 200, 50)
        self.input_text = ""
        self.play_button_enabled = False

        # Cursor blinking
        self.cursor_visible = True
        self.cursor_timer = pygame.time.get_ticks()
        self.cursor_interval = 500

    def draw_input_box(self) -> None:
        button_width = 400
        button_height = 50
        box_color = (255, 255, 255)
        border_color = (141, 133, 201)
        text_color = (0, 0, 0)
        background_color = (210, 204, 255)

        self.input_box.width = button_width
        self.input_box.height = button_height
        self.input_box.centerx = _SCREEN_CENTER[0]

        background_rect = self.input_box.copy()
        background_rect.inflate_ip(0, 50)
        background_rect.move_ip(0, -8)
        pygame.draw.rect(
            self.display_surface, background_color, background_rect, border_radius=10
        )

        if self.input_active:
            label_font = self.font
            label_text = support.TR["enter_play_token"]
            label_surface = label_font.render(label_text, True, text_color)

            # Position the label slightly above the input box
            label_rect = label_surface.get_rect(
                midbottom=(self.input_box.centerx, self.input_box.top + 5)
            )
            self.display_surface.blit(label_surface, label_rect)

        # Draw the input box
        pygame.draw.rect(
            self.display_surface, box_color, self.input_box, border_radius=10
        )
        pygame.draw.rect(
            self.display_surface, border_color, self.input_box, 3, border_radius=10
        )

        # Render the current text inside the input box
        font = self.font
        text_surface = font.render(self.input_text, True, text_color)
        text_rect = text_surface.get_rect(
            midleft=(self.input_box.x + 10, self.input_box.centery)
        )
        self.display_surface.blit(text_surface, text_rect)

        # Blinking cursor
        if self.input_active:
            current_time = pygame.time.get_ticks()
            if current_time - self.cursor_timer >= self.cursor_interval:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = current_time
            if self.cursor_visible:
                cursor_rect = pygame.Rect(text_rect.topright, (2, text_rect.height))
                pygame.draw.rect(self.display_surface, text_color, cursor_rect)

    def draw(self) -> None:
        super().draw()
        if self.input_active:
            self.draw_input_box()

    def validate_token(self, token: str) -> dict[str, Any]:
        result: dict[str, Any] = {"token": token, "jwt": "", "game_version": -1}

        if USE_SERVER:
            resp = authn(token)
            # if jwt token is not empty and game_version key in response
            if resp.get("jwt", "") and "game_version" in resp:
                result = resp
                result["token"] = token
        else:
            # special debug tokens
            valid_tokens = [0, 999]
            # regular valid tokens
            valid_tokens.extend(range(100, 850))

            try:
                token_int = int(token)
                if token_int in valid_tokens:
                    result["jwt"] = "dummy_token"
            except ValueError:
                print("ERROR! Invalid token:", token)
                return result

        # print("result:", result)
        return result

    def button_action(self, text) -> None:
        if text == "Play" and self.play_button_enabled:
            # Only allow playing if the token is valid
            post_event(SET_CURSOR, cursor=CustomCursor.ARROW)
            self.switch_screen(GameState.PLAY)
        elif text == "Enter a Token to Play":
            self.input_active = True
            self.token_input = ""
        elif text == "Quit":
            self.quit_game()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if super().handle_event(event):
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            self.pressed_button = self.get_hovered_button()
            if self.input_box.collidepoint(event.pos):
                self.input_active = True
                return True
            else:
                self.input_active = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_box.collidepoint(event.pos) and self.input_active:
                self.input_active = True
                return True
            else:
                self.input_active = False

        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                if self.input_text:
                    response = self.validate_token(self.input_text)
                    if response.get("jwt", ""):
                        # Check if the token is valid
                        self.set_token(response)
                        self.play_button_enabled = True
                        self.input_active = False
                        self.remove_button("Enter a Token to Play")
                        self.draw()
                        self.input_text = ""
                    return True
            elif event.key == pygame.K_ESCAPE:
                self.input_active = False
                self.input_text = ""
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True
            else:
                if event.key not in [pygame.K_TAB, pygame.K_DELETE]:
                    self.input_text += event.unicode
                return True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_game()
                return True

            if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                # Play button is available => start game
                if self.play_button_enabled:
                    self.switch_screen(GameState.PLAY)
                # Play button is not available => ask for token
                else:
                    self.input_active = True
                return True

        return False
