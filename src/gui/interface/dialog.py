from src.enums import Layer
from src.sprites.base import Sprite
from src.support import resource_path
from src.settings import CHARS_PER_LINE, TB_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from src.timer import Timer
import pygame
import json
from jsmin import jsmin  # JSON minifier function (removes comments, notably)
from operator import attrgetter
import textwrap


class TextBox(Sprite):
    """Text box sprite that contains a part of text."""
    _TXT_SURF_EXTREMITIES: tuple[pygame.Rect, pygame.Rect] = (pygame.Rect(0, 0, 14, 202), pygame.Rect(373, 0, 18, 202))
    _TXT_SURF_REGULAR_AREA: pygame.Rect = pygame.Rect(14, 0, 1, 202)
    _CNAME_SURF_RECT: pygame.Rect = pygame.Rect(8, 0, 212, 67)
    _TXT_SURF_RECT: pygame.Rect = pygame.Rect(0, 64, TB_SIZE[0], TB_SIZE[1]-64)
    _TB_IMAGE: pygame.Surface | None = None

    @classmethod
    def prepare_base_tb_image(cls, cname_surf: pygame.Surface, txt_surf: pygame.Surface):
        if cls._TB_IMAGE is not None:
            return
        cls._TB_IMAGE = pygame.Surface(TB_SIZE, flags=pygame.SRCALPHA)
        start = txt_surf.subsurface(cls._TXT_SURF_EXTREMITIES[0])
        regular = txt_surf.subsurface(cls._TXT_SURF_REGULAR_AREA)
        end = txt_surf.subsurface(cls._TXT_SURF_EXTREMITIES[1])
        txt_part_top = 64
        blit_list = [
            (start, pygame.Rect(0, txt_part_top, *start.size)),
            (end, pygame.Rect(373, txt_part_top, *end.size)),
            *((regular, pygame.Rect(x, txt_part_top, *regular.size)) for x in range(start.width, 373)),
            (cname_surf, cls._CNAME_SURF_RECT)
        ]
        cls._TB_IMAGE.fblits(blit_list)

    def __init__(self, character_name: str, text: str, font: pygame.Font):
        """Create a text box.

        :param character_name: The character meant to speak using this text box.
        :param text: The dialogue the character is supposed to say.
        :param font: The font used to render this dialogue."""
        self.font: pygame.Font = font
        self.cname: str = character_name
        self.text: str = textwrap.fill(text, width=CHARS_PER_LINE)
        self.image: pygame.Surface = pygame.Surface(TB_SIZE, flags=pygame.SRCALPHA)
        self.__prepare_image()
        self._tmp_img: pygame.Surface = self._TB_IMAGE.copy()
        cname: pygame.Surface = self.font.render(character_name, True, color=pygame.Color("black"))
        cname_rect: pygame.Rect = cname.get_rect(center=self._CNAME_SURF_RECT.center)
        self._tmp_img.blit(cname, cname_rect)
        self._fin_img: pygame.Surface = self.image
        self.timer: Timer = Timer(50, True, autostart=False, func=self._advance_by_one)
        self.image = self._tmp_img.copy()
        self._finished_advancing: bool = False
        self._txt_needs_rerender: bool = True
        self._chr_index: int = 1

        super().__init__(
            (SCREEN_WIDTH / 2 - self.image.width / 2,
             SCREEN_HEIGHT - self.image.height),
            self.image, tuple(), z=Layer.TEXT_BOX, name=character_name
        )

    @property
    def finished_advancing(self):
        return self._finished_advancing

    @finished_advancing.setter
    def finished_advancing(self, val: bool):
        self._finished_advancing = val
        if val:
            self._chr_index = len(self.text)

    # finished_advancing = property(fget=attrgetter("_finished_advancing"), fset=_set_finished_advancing)

    def _advance_by_one(self):
        self._chr_index += 1
        if self._chr_index >= len(self.text):
            self._finished_advancing = True
        else:
            self._txt_needs_rerender = True

    def _prerender_text_ani(self):
        text_surf = self.font.render(self.text[:self._chr_index], True, color=pygame.Color("black"))
        text_rect = text_surf.get_rect(topleft=(15, 78))
        blit_list = [
            (self._tmp_img, (0, 0)),
            (text_surf, text_rect)
        ]
        self.image.fblits(blit_list)
        self._txt_needs_rerender = False

    def update(self, *args, **kwargs):
        if not self.timer:
            self.timer.activate()
        self.timer.update()
        # Keeping variable args tuple and keyword arguments dict syntax for compatibility with base method
        if self._finished_advancing and self.image is not self._fin_img:
            self.image = self._fin_img
        elif not self._finished_advancing and self._txt_needs_rerender:
            self._prerender_text_ani()

    def __prepare_image(self):
        cname = self.font.render(self.name, True, color=pygame.Color("black"))
        cname_rect = cname.get_rect(center=self._CNAME_SURF_RECT.center)
        text_surf = self.font.render(self.text, True, color=pygame.Color("black"))
        text_rect = text_surf.get_rect(topleft=(15, 78))
        blit_list = [
            (self._TB_IMAGE, (0, 0)),
            (cname, cname_rect),
            (text_surf, text_rect)
        ]
        self.image.fblits(blit_list)
    
    def draw(self, display_surface: pygame.Surface, offset: pygame.Vector2):
        display_surface.blit(self.image, self.rect)


def prepare_tb_image(cname_surf: pygame.Surface, txt_surf: pygame.Surface):
    TextBox.prepare_base_tb_image(cname_surf, txt_surf)


class DialogueManager:
    """Dialogue manager object.
    This class will store all dialogues and has a method to show a dialogue on-screen."""
    def __init__(self, sprite_group: pygame.sprite.Group):
        self.spr_grp: pygame.sprite.Group = sprite_group
        # Open the dialogues file and dump all of its content in here,
        # while purging the raw file content from its comments.
        with open(resource_path("data/dialogues.json"), "r") as dialogue_file:
            self.dialogues: dict[str, list[list[str, str]]] = json.loads(jsmin(dialogue_file.read()))
        self._tb_list: list[TextBox] = []
        self._msg_index: int = 0
        self._showing_dialogue: bool = False
        self.font: pygame.Font = pygame.font.Font(resource_path("font/LycheeSoda.ttf"), 20)

    showing_dialogue = property(attrgetter("_showing_dialogue"))

    def _purge_tb_list(self):
        for tb in self._tb_list:
            tb.kill()
        self._tb_list.clear()
        self._msg_index = 0

    def _create_tb(self, cname: str, txt: str):
        self._tb_list.append(TextBox(cname, txt, self.font))

    def _push_current_tb_to_foreground(self):
        if not self._msg_index:
            self._tb_list[0].add(self.spr_grp)
            return
        self._tb_list[self._msg_index - 1].kill()
        self._tb_list[self._msg_index].add(self.spr_grp)

    def _get_current_tb(self):
        return self._tb_list[self._msg_index]

    def open_dialogue(self, dial: str):
        """Opens a text box with the current dialogue ID's first text showed on-screen.
        Does nothing if a text box is already on-screen.
        :param dial: The dialogue ID for which you want to open textboxes on the screen.
        :raise ValueError: if the given dialogue ID does not exist."""
        if self._showing_dialogue:
            return

        try:
            dial_info = self[dial]
        except LookupError as exc:
            raise ValueError(f"dialogue ID '{dial}' does not exist") from exc

        if self._msg_index:
            self._purge_tb_list()

        self._showing_dialogue = True

        for cname, portion in dial_info:
            self._create_tb(cname, portion)

        self._push_current_tb_to_foreground()

    def advance(self):
        """Show the next part of the current dialogue, or forces the current textbox to display
        the whole text before it finishes typing.
        If the end of the dialogue is reached, clears the textboxes away
        from the screen and returns control to the player."""
        if not self._get_current_tb().finished_advancing:
            # Textbox is still animating, forcing it to skip to the end
            self._get_current_tb().finished_advancing = True
            return
        self._msg_index += 1
        if self._msg_index >= len(self._tb_list):
            # Reached the end of the dialogue, clear everything away to make space for the next dialogue
            self._purge_tb_list()
            self._showing_dialogue = False
            return
        self._push_current_tb_to_foreground()

    def __getitem__(self, item):
        return self.dialogues[item]
    
