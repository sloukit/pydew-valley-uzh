import math
from abc import ABC
from collections.abc import Callable

import pygame
import pygame.gfxdraw

from src.colors import SL_ORANGE_BRIGHT, SL_ORANGE_BRIGHTEST, SL_ORANGE_DARK
from src.enums import Layer
from src.groups import PersistentSpriteGroup
from src.gui.interface.emotes_base import EmoteBoxBase, EmoteManagerBase, EmoteWheelBase
from src.settings import EMOTE_SIZE
from src.support import draw_aa_line
from src.timer import Timer


class EmoteBox(EmoteBoxBase):
    EMOTE_DIALOG_BOX = None

    def __init__(
        self,
        pos: tuple[int, int],
        emote: list[pygame.Surface],
        duration: int,
        *groups: pygame.sprite.Group,
    ):
        """
        Displays an emote in a small speech bubble.
        :param pos: Position where the emote should first be drawn
        :param emote: List of all frames of the Emote animation
        """
        super().__init__(pos, emote[0], groups, z=Layer.EMOTES)

        self.image = EmoteBox.EMOTE_DIALOG_BOX

        self.emote = emote
        self._current_emote_image = self.emote[0]

        self.pos = self.rect.topleft

        self._ani_frame_count = len(self.emote)
        self._ani_cframe = -1
        self._ani_frame_length = self._ani_frame_count / 4
        self._ani_length = self._ani_frame_count * 2
        if duration:
            self._ani_total_frames = duration
        else:
            self._ani_total_frames = int(self._ani_length / self._ani_frame_length)

        self.ani_finished = False
        self.__on_finish_animation_funcs = []

        # load first animation frame
        self._ani_next_frame()

        self.timer = Timer(
            self._ani_frame_length * 1000,
            repeat=True,
            autostart=False,
            func=self._ani_next_frame,
        )

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: tuple[float, float]):
        self._pos = value
        self.rect.update(self._pos, self.rect.size)

    def on_finish_animation(self, func: Callable[[], None]):
        self.__on_finish_animation_funcs.append(func)

    def _ani_next_frame(self):
        """
        Advances one frame of the Emote animation.
        """
        self._ani_cframe += 1
        if self._ani_cframe >= self._ani_total_frames:
            self.ani_finished = True
            for func in self.__on_finish_animation_funcs:
                func()
            return

        self._current_emote_image = self.emote[self._ani_cframe % self._ani_frame_count]

        # update image
        self.image = EmoteBox.EMOTE_DIALOG_BOX.copy()
        self.image.blit(
            self._current_emote_image,
            (
                EmoteBox.EMOTE_DIALOG_BOX.width / 2
                - self._current_emote_image.width / 2,
                EmoteBox.EMOTE_DIALOG_BOX.height / 2
                - self._current_emote_image.height / 2
                - 8,
            ),
        )

    def update(self, *args, **kwargs):
        if not self.timer:
            self.timer.activate()
        self.timer.update()


class EmoteManager(EmoteManagerBase, ABC):
    _emote_boxes: dict[int, EmoteBox]

    def __init__(
        self, emotes: dict[str, list[pygame.Surface]], *groups: pygame.sprite.Group
    ):
        """
        Base class for all EmoteManagers
        :param groups: Sprite groups the emotes should belong to
        :param emotes: Dictionary of all emote names mapped to a list of their
                       animation frames
        """
        self.groups = groups

        self.emotes = emotes

        self._emote_boxes = {}

    def _check_obj(self, obj_id: int) -> bool:
        """
        :return: Whether the Emote animation attached to a given object is
                 still playing or not.
        """
        if obj_id in self._emote_boxes.keys():
            return True
        return False

    def show_emote(self, obj: object, emote: str):
        """
        Attaches a new Emote with the given name to the given object.
        Raises KeyError if there is no Emote with the given name.
        """
        if emote not in self.emotes.keys():
            raise KeyError(
                f'There is no Emote named "{emote}". '
                f"Available emotes: {list(self.emotes.keys())}"
            )

        if self._check_obj(id(obj)):
            self._remove_emote_box(id(obj))

        if emote == "sad_ani":
            self[id(obj)] = EmoteBox((0, 0), self.emotes[emote], 30, *self.groups)
        else:
            self[id(obj)] = EmoteBox((0, 0), self.emotes[emote], 15, *self.groups)

        @self[id(obj)].on_finish_animation
        def on_finish_animation():
            self._remove_emote_box(id(obj))

    def update_obj(self, obj: object, pos: tuple[float, float]):
        """
        Updates the position of the Emote attached to the given object.
        """
        if not self._check_obj(id(obj)):
            return
        self[id(obj)].pos = pos

    def _remove_emote_box(self, obj_id: int):
        self[obj_id].kill()
        del self[obj_id]

    def _clear_emote_boxes(self):
        for obj_id in self._emote_boxes.keys():
            self._remove_emote_box(obj_id)

    def __setitem__(self, obj: object, value: EmoteBox):
        if isinstance(obj, int):
            self._emote_boxes[obj] = value
        else:
            self._emote_boxes[id(obj)] = value

    def __getitem__(self, obj: object) -> EmoteBox:
        if isinstance(obj, int):
            return self._emote_boxes[obj]
        else:
            return self._emote_boxes[id(obj)]

    def __delitem__(self, obj: object):
        if isinstance(obj, int):
            del self._emote_boxes[obj]
        else:
            del self._emote_boxes[id(obj)]


class NPCEmoteManager(EmoteManager):
    def __init__(
        self, emotes: dict[str, list[pygame.Surface]], *groups: pygame.sprite.Group
    ):
        """
        EmoteManager for all NPCs
        """
        super().__init__(emotes, *groups)


class EmoteWheel(EmoteWheelBase):
    def __init__(
        self,
        emote_manager: EmoteManagerBase,
        emotes_list: list[str],
        *groups: PersistentSpriteGroup,
    ):
        """
        The Player's emote selection wheel
        :param emote_manager: The EmoteManager of the Player
        """
        self._emote_manager = emote_manager

        self._emotes = emotes_list
        self.emote_index = 0
        self.emotes_count = len(self._emotes)
        self._current_emote = self._emotes[self.emote_index]
        self._last_emote_index = None

        self._emote_separator_width = 4
        self._selected_emote_separator_width = 6
        self._background_alpha = 192

        self._inner_radius = 48
        self._outer_radius = 128
        self._center = (self._outer_radius + self._inner_radius) / 2

        self._image = pygame.Surface(
            (self._outer_radius * 2, self._outer_radius * 2), flags=pygame.SRCALPHA
        )

        self._setup_image()

        super().__init__((0, 0), self._image.copy(), z=Layer.TEXT_BOX)
        for group in groups:
            group.add_persistent(self)

        self.visible = False

    def _setup_image(self):
        background_surface = pygame.Surface(
            (self._outer_radius * 2, self._outer_radius * 2), flags=pygame.SRCALPHA
        )
        pygame.draw.circle(
            background_surface,
            SL_ORANGE_BRIGHT,
            (self._outer_radius, self._outer_radius),
            self._outer_radius - 2,
            int(self._outer_radius - self._inner_radius),
        )
        background_surface.set_alpha(self._background_alpha)

        self._image.blit(background_surface, (0, 0))

        for i in range(len(self._emotes)):
            # draw lines as separators between the different emotes on the
            # selector wheel
            deg = math.pi * 2 * i / len(self._emotes) - math.pi / 2
            thickness = self._emote_separator_width

            # center_pos and length have to be slightly adjusted to be neither
            # to short, nor to extend beyond the edge of the selector wheel
            center_pos = (
                self._outer_radius + math.cos(deg) * (self._center - 2),
                self._outer_radius + math.sin(deg) * (self._center - 2),
            )
            length = self._outer_radius - self._inner_radius - 2

            draw_aa_line(
                self._image, center_pos, thickness, length, deg, SL_ORANGE_DARK
            )

            # increase degree by half the distance to the next emote,
            #  to get the center of the current emote in the selector wheel
            deg = math.pi * 2 * (i + 0.5) / len(self._emotes) - math.pi / 2

            # blit first frame of the emote as preview onto the selector wheel
            self._image.blit(
                self._emote_manager.emotes[self._emotes[i]][0],
                (
                    self._outer_radius - EMOTE_SIZE / 2 + math.cos(deg) * self._center,
                    self._outer_radius - EMOTE_SIZE / 2 + math.sin(deg) * self._center,
                ),
            )

        # draw emote wheel outlines
        pygame.draw.circle(
            self._image,
            SL_ORANGE_DARK,
            (self._outer_radius, self._outer_radius),
            self._inner_radius,
            self._emote_separator_width,
        )
        pygame.draw.circle(
            self._image,
            SL_ORANGE_DARK,
            (self._outer_radius, self._outer_radius),
            self._outer_radius - 1,
            self._emote_separator_width,
        )

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: tuple[float, float]):
        self._pos = value
        self.rect.update(
            (self._pos[0] - self.rect.width / 2, self._pos[1] - self.rect.height / 2),
            self.rect.size,
        )

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        if value:
            self.z = Layer.TEXT_BOX
            self._visible = True
        else:
            self.z = -1
            self._visible = False

    def toggle_visibility(self):
        self.visible = not self.visible

    def update(self, *args, **kwargs):
        if self.z < 0 or self._last_emote_index == self.emote_index:
            return

        self._last_emote_index = self.emote_index
        self._current_emote = self._emotes[self.emote_index % self.emotes_count]

        self.image = self._image.copy()

        current_emote_index = self.emote_index % self.emotes_count

        # draw thicker and brighter lines around the currently selected emote
        deg = math.pi * 2 * current_emote_index / self.emotes_count - math.pi / 2

        # center_pos and length have to be slightly adjusted to be neither to
        # short, nor to extend beyond the edge of the selector wheel
        center_pos = (
            self._outer_radius + math.cos(deg) * (self._center - 3),
            self._outer_radius + math.sin(deg) * (self._center - 3),
        )
        thickness = self._selected_emote_separator_width
        length = self._outer_radius - self._inner_radius + 5

        draw_aa_line(
            self.image, center_pos, thickness, length, deg, SL_ORANGE_BRIGHTEST
        )

        deg = (
            math.pi * 2 * (current_emote_index + 1) / self.emotes_count
        ) - math.pi / 2
        center_pos = (
            self._outer_radius + math.cos(deg) * (self._center - 3),
            self._outer_radius + math.sin(deg) * (self._center - 3),
        )

        draw_aa_line(
            self.image, center_pos, thickness, length, deg, SL_ORANGE_BRIGHTEST
        )

        start_deg = (
            -(math.pi * 2 * current_emote_index / self.emotes_count) + math.pi / 2
        )
        stop_deg = (
            -(math.pi * 2 * (current_emote_index + 1) / self.emotes_count) + math.pi / 2
        )

        pygame.draw.arc(
            self.image,
            SL_ORANGE_BRIGHTEST,
            (0, 0, self._outer_radius * 2, self._outer_radius * 2),
            stop_deg,
            start_deg,
            thickness,
        )

        pygame.draw.arc(
            self.image,
            SL_ORANGE_BRIGHTEST,
            (
                self._outer_radius - self._inner_radius - 1,
                self._outer_radius - self._inner_radius - 1,
                self._inner_radius * 2 + 2,
                self._inner_radius * 2 + 2,
            ),
            stop_deg,
            start_deg,
            thickness,
        )


class PlayerEmoteManager(EmoteManager):
    emote_wheel: EmoteWheel

    __on_show_emote_funcs: list[Callable[[str], None]]
    __on_emote_wheel_opened_funcs: list[Callable[[], None]]
    __on_emote_wheel_closed_funcs: list[Callable[[], None]]

    def __init__(
        self,
        emotes: dict[str, list[pygame.Surface]],
        emotes_list: list[str],
        *groups: PersistentSpriteGroup,
    ):
        super().__init__(emotes, *groups)

        self.emote_wheel = EmoteWheel(self, emotes_list, *groups)

        self.reset()

    def reset(self):
        self.__on_show_emote_funcs = []
        self.__on_emote_wheel_opened_funcs = []
        self.__on_emote_wheel_closed_funcs = []

    def on_show_emote(self, func: Callable[[str], None]):
        """
        Attach the given function to the EmoteManager so that it is called when
        show_emote is called.
        """
        self.__on_show_emote_funcs.append(func)

    def show_emote(self, obj: object, emote: str):
        super().show_emote(obj, emote)
        for func in self.__on_show_emote_funcs:
            func(emote)

    def on_emote_wheel_opened(self, func: Callable[[], None]):
        """
        Attach the given function to the EmoteManager so that it is called when
        the EmoteWheel is opened.
        """
        self.__on_emote_wheel_opened_funcs.append(func)

    def on_emote_wheel_closed(self, func: Callable[[], None]):
        """
        Attach the given function to the EmoteManager so that it is called when
        the EmoteWheel is closed.
        """
        self.__on_emote_wheel_closed_funcs.append(func)

    def update_emote_wheel(self, pos: tuple[float, float]):
        self.emote_wheel.pos = pos

    def toggle_emote_wheel(self):
        self.emote_wheel.toggle_visibility()

        if self.emote_wheel.visible:
            for func in self.__on_emote_wheel_opened_funcs:
                func()
        else:
            for func in self.__on_emote_wheel_closed_funcs:
                func()
