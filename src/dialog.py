from .support import resource_path
from .settings import CHARS_PER_LINE, TB_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
import pygame
import json
from jsmin import jsmin  # JSON minifier function (removes comments, notably)
from operator import attrgetter
import textwrap


class TextBox(pygame.sprite.Sprite):
    """Text box sprite that contains a part of text."""
    _TXT_SURF_EXTREMITIES: tuple[pygame.Rect, pygame.Rect] = (pygame.Rect(0, 0, 14, 202), pygame.Rect(373, 0, 18, 202))
    _TXT_SURF_REGULAR_AREA: pygame.Rect = pygame.Rect(14, 0, 1, 202)
    _CNAME_SURF_RECT: pygame.Rect = pygame.Rect(8, 0, 212, 67)
    _TXT_SURF_RECT: pygame.Rect = pygame.Rect(0, 64, TB_SIZE[0], TB_SIZE[1]-64)
    _TB_IMAGE: pygame.Surface | None = None

    @classmethod
    def prepare_base_tb_image(cls, cname_surf: pygame.Surface, txt_surf: pygame.Surface):
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

    def __init__(self, character_name: str, text: str, cname_surf: pygame.Surface, txt_surf: pygame.Surface, font: pygame.Font):
        super().__init__()
        self.z = 11
        self.font: pygame.Font = font
        self.cname: str = character_name
        self.text: str = textwrap.fill(text, width=CHARS_PER_LINE)
        self.image: pygame.Surface = pygame.Surface(TB_SIZE, flags=pygame.SRCALPHA)
        self.__prepare_image(cname_surf, txt_surf)
        self.rect: pygame.FRect = self.image.get_frect(bottom=SCREEN_HEIGHT, centerx=(SCREEN_WIDTH // 2))

    def __prepare_image(self, cname_surf: pygame.Surface, txt_surf: pygame.Surface):
        start = txt_surf.subsurface(self._TXT_SURF_EXTREMITIES[0])
        regular = txt_surf.subsurface(self._TXT_SURF_REGULAR_AREA)
        end = txt_surf.subsurface(self._TXT_SURF_EXTREMITIES[1])
        cname = self.font.render(self.cname, True, color=pygame.Color("black"))
        cname_rect = cname.get_rect(center=self._CNAME_SURF_RECT.center)
        text_surf = self.font.render(self.text, True, color=pygame.Color("black"))
        text_rect = text_surf.get_rect(topleft=(15, 78))
        txt_part_top = 64
        blit_list = [
            (start, pygame.Rect(0, txt_part_top, *start.size)),
            (end, pygame.Rect(373, txt_part_top, *end.size)),
            *((regular, pygame.Rect(x, txt_part_top, *regular.size)) for x in range(start.width, 373)),
            (cname_surf, self._CNAME_SURF_RECT),
            (cname, cname_rect),
            (text_surf, text_rect)
        ]
        self.image.fblits(blit_list)


class DialogueManager:
    """Dialogue manager object.
    This class will store all dialogues and has a method to show a dialogue on-screen."""
    def __init__(self, sprite_group: pygame.sprite.Group, cname_surf: pygame.Surface, txt_surf: pygame.Surface):
        self.spr_grp: pygame.sprite.Group = sprite_group
        self._cname_surf: pygame.Surface = cname_surf
        self._txt_surf: pygame.Surface = txt_surf
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
        self._tb_list.append(TextBox(cname, txt, self._cname_surf, self._txt_surf, self.font))

    def _push_current_tb_to_foreground(self):
        if not self._msg_index:
            self._tb_list[0].add(self.spr_grp)
            return
        self._tb_list[self._msg_index - 1].kill()
        self._tb_list[self._msg_index].add(self.spr_grp)

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
        """Show the next part of the current dialogue.
        If the end of the dialogue is reached, clears the textboxes away from the screen and returns control to the player."""
        self._msg_index += 1
        if self._msg_index >= len(self._tb_list):
            self._purge_tb_list()
            self._showing_dialogue = False
            return
        self._push_current_tb_to_foreground()

    def __getitem__(self, item):
        return self.dialogues[item]
