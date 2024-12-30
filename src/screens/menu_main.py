from collections.abc import Callable
from typing import Any

import pygame
from pygame.mouse import get_pressed as mouse_buttons

from src.client import authn
from src.enums import CustomCursor, GameState
from src.events import SET_CURSOR, post_event
from src.gui.menu.general_menu import GeneralMenu
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH, USE_SERVER
from src.support import get_translated_string as _

_SCREEN_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


class MainMenu(GeneralMenu):
    def __init__(
        self,
        switch_screen: Callable[[GameState], None],
        set_token: Callable[[dict[str, Any]], None],
    ) -> None:
        options = [_("Play"), _("Quit"), _("Enter authentication data")]
        title = _("Main Menu")
        size = (400, 400)
        super().__init__(title, options, switch_screen, size)
        self.set_token = set_token
        self.token = ""  # Variable to store token
        self.initials = ""  # Variable to store initials
        self.play_button_enabled = False  # Initialize as False

        # Token input field
        self.input_active = False
        self.input_box = pygame.Rect(100, 390, 200, 50)
        self.input_text = ""

        # Initials input field (hidden initially)
        self.initials_active = False
        self.initials_box = pygame.Rect(100, 390, 200, 50)
        self.initials_text = ""

        # Cursor blinking
        self.cursor_visible = True
        self.cursor_timer = pygame.time.get_ticks()
        self.cursor_interval = 500

    def draw_input_box(self, box, input_text, label_text, input_active) -> None:
        button_width = 400
        button_height = 50
        box_color = (255, 255, 255)
        border_color = (141, 133, 201)
        text_color = (0, 0, 0)
        background_color = (210, 204, 255)

        box.width = button_width
        box.height = button_height
        box.centerx = _SCREEN_CENTER[0]

        background_rect = box.copy()
        background_rect.inflate_ip(0, 50)
        background_rect.move_ip(0, -8)
        pygame.draw.rect(
            self.display_surface, background_color, background_rect, border_radius=10
        )

        if input_active:
            label_font = self.font
            label_surface = label_font.render(label_text, True, text_color)

            # Position the label slightly above the input box
            label_rect = label_surface.get_rect(midbottom=(box.centerx, box.top + 5))
            self.display_surface.blit(label_surface, label_rect)

        # Draw the input box
        pygame.draw.rect(self.display_surface, box_color, box, border_radius=10)
        pygame.draw.rect(self.display_surface, border_color, box, 3, border_radius=10)

        # Render the current text inside the input box
        font = self.font
        text_surface = font.render(input_text, True, text_color)
        text_rect = text_surface.get_rect(midleft=(box.x + 10, box.centery))
        self.display_surface.blit(text_surface, text_rect)

        # Blinking cursor
        if input_active:
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
            self.draw_input_box(self.input_box, self.input_text, _("Enter play token:"), self.input_active)
        if self.initials_active:
            self.draw_input_box(self.initials_box, self.initials_text, _("Enter initials:"), self.initials_active)

    def validate_token(self, token: str) -> dict[str, Any]:
        result: dict[str, Any] = {"token": token, "jwt": "", "game_version": -1}

        if USE_SERVER:
            resp = authn(token)
            if resp.get("jwt", "") and "game_version" in resp:
                result = resp
                result["token"] = token
        else:
            # Debug tokens for local usage
            valid_tokens = [0, 999]
            valid_tokens.extend(range(100, 850))

            try:
                token_int = int(token)
                if token_int in valid_tokens:
                    result["jwt"] = "dummy_token"
            except ValueError:
                print("ERROR! Invalid token:", token)
                return result

        return result

    def button_action(self, text) -> None:
        if text == _("Play") and self.play_button_enabled:
            # Only allow playing if both token and initials are valid
            post_event(SET_CURSOR, cursor=CustomCursor.ARROW)
            self.switch_screen(GameState.PLAY)
        elif text == _("Enter authentication data"):
            self.input_active = True
            self.token = ""  # Reset token each time we re-enter
        elif text == _("Quit"):
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

            if self.initials_box.collidepoint(event.pos) and self.initials_active:
                self.initials_active = True
                return True
            else:
                self.initials_active = False

        if event.type == pygame.KEYDOWN:
            # Handle token input
            if self.input_active:
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    if self.input_text:
                        response = self.validate_token(self.input_text)
                        if response.get("jwt", ""):
                            # Save token and enable initials input
                            self.token = self.input_text
                            print(self.token)
                            self.set_token(response)
                            self.input_active = False
                            self.initials_active = True  # Show initials input
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
                    self.input_text += event.unicode
                    return True

            # Handle initials input
            elif self.initials_active:
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    if self.initials_text:
                        # Save initials and enable play button
                        self.initials = self.initials_text
                        print(self.initials)
                        self.play_button_enabled = True
                        self.initials_active = False
                        # Now remove the button after entering initials
                        self.remove_button(_("Enter authentication data"))
                        self.draw()  # Refresh screen after input
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.initials_text = self.initials_text[:-1]
                    return True
                else:
                    self.initials_text += event.unicode
                    return True

        return False