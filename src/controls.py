from collections.abc import Generator
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Self

import pygame


@dataclass(eq=False)
class Control:
    """
    Instances of this dataclass refer to an individual Control / Keybind and
    its respective type, text, value and state.

    Attributes:
        control_value: Integer value of this control.
               Should be set to one of the key / mouse button constants
               included in PyGame (see also https://pyga.me/docs/ref/key.html).
        text: Text to describe the control (e.g. in the Settings/Keybinds menu)

        _default_value: Default value of the Control
        _default_text: Default text of the Control

        click: Boolean value which indicates whether the key associated
               with this control has just been clicked or not.
        hold: Boolean value which indicates whether the key associated
              with this control is held down or not.
    """

    control_value: int
    text: str

    # These values cannot be set on initialisation but will be updated with
    # their respective value in __post_init__
    _default_value: int = field(init=False, metadata={"exclude": True})
    _default_text: str = field(init=False, metadata={"exclude": True})

    # Attributes that reflect the current control state are excluded from the
    # savestate and cannot be set on initialisation
    click: bool = field(init=False, default=False, metadata={"exclude": True})
    hold: bool = field(init=False, default=False, metadata={"exclude": True})

    def __post_init__(self):
        self._default_value = self.control_value
        self._default_text = self.text

    def get_default_value(self) -> int:
        return self._default_value

    def _control_as_dict(self) -> dict[str, str | int]:
        """
        Returns a dictionary representation of this Control instance, excluding
        attributes that describe the current state of the control
        (whether it has just been clicked or is held down)
        """
        return_dict = {}
        for _field in fields(self):
            if _field.metadata.get("exclude"):
                continue

            name = _field.name
            value = getattr(self, name)

            return_dict[name] = value

        return return_dict

    def _control_from_dict(self, d: dict[str, str | int]):
        """
        Loads a Control instance from a (partial) dictionary representation.
        Ignores entries that do not map to any field of the Control instance.
        """
        control_attribute_list = [i.name for i in fields(self)]

        for control_attr_name, control_attr_val in d.items():
            if control_attr_name in control_attribute_list:
                setattr(self, control_attr_name, control_attr_val)


class Controls(Control, Enum):
    """
    Enum which groups all Control instances of the game.
    """

    UP = (pygame.K_UP, "Move Up")
    DOWN = (pygame.K_DOWN, "Move Down")
    LEFT = (pygame.K_LEFT, "Move Left")
    RIGHT = (pygame.K_RIGHT, "Move Right")

    USE = (pygame.BUTTON_LEFT, "Use Tool")
    NEXT_TOOL = (pygame.K_TAB, "Cycle Tools")
    NEXT_SEED = (pygame.K_LSHIFT, "Cycle Seeds")
    PLANT = (pygame.BUTTON_RIGHT, "Plant Seed")
    INTERACT = (pygame.K_SPACE, "Interact")
    INVENTORY = (pygame.K_i, "Open Inventory")
    EMOTE_WHEEL = (pygame.K_e, "Toggle Emote Wheel")
    SHOW_HITBOXES = (pygame.K_h, "Show Hitboxes")
    SHOW_DIALOG = (pygame.K_t, "Show Dialog")
    ADVANCE_DIALOG = (pygame.K_SPACE, "Advance Dialog")

    @classmethod
    def as_dict(cls) -> dict[str, dict[str, str | int]]:
        """
        Maps the name of each member to the value returned by
        member._control_as_dict()
        :return: A dictionary representation of all Controls members.
        """
        return {i.name: cls[i.name]._control_as_dict() for i in cls}

    @classmethod
    def from_dict(cls, d: dict[str, dict[str, str | int]]):
        """
        Loads the attributes of all supplied Control dictionary
        representations.
        Ignores entries that do not map to any member of Controls.
        """
        control_name_list = [i.name for i in cls]

        for control_key, control_value in d.items():
            if control_key in control_name_list:
                cls[control_key]._control_from_dict(control_value)

    @classmethod
    def load_default_keybind(cls, control: Self, keybinds: dict[str, int] = None):
        """
        Loads a singular Control.value of the given Controls member from the
        supplied keybinds dictionary. The name of the given Controls member
        should correspond to the dictionary key of the keybind. If there is no
        corresponding key in the keybinds dictionary, the Control.value will be
        set to None. When no keybinds are supplied, the keybinds defined in
        DEFAULT_CONTROLS will be used.
        """
        if keybinds is None:
            control.control_value = control.get_default_value()
        else:
            control.control_value = keybinds.get(control.name)

    @classmethod
    def load_default_keybinds(cls, keybinds: dict[str, int] = None):
        """
        Loads the Control.value of all Controls members from the supplied
        keybinds dictionary. For each member of Controls that does not have a
        corresponding dictionary entry with the same key as the member's name,
        the member's Control value will be set to None.
        """
        for control in cls:
            cls.load_default_keybind(control, keybinds=keybinds)

    @classmethod
    def all_controls(cls) -> Generator[Control, None, None]:
        """:return: A generator which yields all Controls members."""
        return (getattr(cls, i.name) for i in cls)

    @classmethod
    def length(cls) -> int:
        return len(list(cls.all_controls()))
