"""Expansion over Pygame's event management system."""

from types import NoneType, UnionType
from typing import NoReturn, Self, Type, Union

import pygame

SpecialForm = type(NoReturn)


class _EventDefinition:
    """Additional information about a specific event type.

    This allows us to ensure that all required arguments are given
    when posting an event of a certain type (namely, by raising errors if they
    aren't given)."""

    _EDEF_CACHE = {}  # INTERNAL USAGE!
    _EDEF_NAMES = set()
    __slots__ = ("name", "__name__", "code", "_attrs", "default_values_for_attrs")

    @classmethod
    def from_code(cls, code: int) -> Self:
        """Return the corresponding event definition for a given code."""
        try:
            return cls._EDEF_CACHE[code]
        except LookupError as exc:
            raise ValueError(
                f"given code ({code}) is not linked to a registered event type"
            ) from exc

    @classmethod
    def from_name(cls, name: str) -> Self:
        """Return the corresponding event definition for a given name."""
        for edef in cls._EDEF_CACHE.values():
            if edef.__name__ == name:
                return edef
        raise ValueError(f"given name '{name}' does not match an existing event type")

    @classmethod
    def add_to_edef_cache(cls, edef: Self):
        """Add the given event definition to the cache."""
        cls._EDEF_CACHE[edef.code] = edef
        cls._EDEF_NAMES.add(edef.__name__)

    @classmethod
    def _check_not_registered(cls, name: str):
        """Checks that an event type name is available for registration,
        and raises an error if it isn't.

        :param name: The name to check for.
        :raise ValueError: if the given name is not available for registering."""
        if name in cls._EDEF_NAMES:
            raise ValueError(f"event type '{name}' already exists")

    def __init__(
        self,
        name: str,
        code: int,
        **attrs: Union[Type, SpecialForm],
    ):
        self.__name__ = self.name = name
        self._attrs = attrs
        self.default_values_for_attrs = {}
        self.code = code

    def __repr__(self):
        return f"<EventDefinition(name='{self.__name__}', code={self.code}, {', '.join((f'{attr}:{value}' for attr, value in self.attrs.items()))}>"

    def __hash__(self):
        return hash(
            (self.__name__, self.code) + tuple(itm for itm in self.attrs.items())
        )

    @property
    def attrs(self):
        return self._attrs

    def set_default_for_attr(self, attr: str, value):
        """Set the default value for an attribute required by this event type.

        :param attr: The attribute to set a default for.
        :param value: The corresponding default value.
        :raise TypeError: if the value does not match the type for this attribute
        given when creating the event type.
        :raise ValueError: if the attribute does not exist for this event type."""
        if attr not in self.attrs:
            raise ValueError(
                f"invalid attribute for event type {self.__name__} : '{attr}'"
            )
        else:
            attr_type = self.attrs[attr]
            if not isinstance(value, getattr(attr_type, "__args__", attr_type)):
                typenames = ",".join(
                    (tp.__name__ for tp in getattr(attr_type, "__args__", (attr_type,)))
                )
                raise TypeError(
                    f"given value ({value}) for attribute {attr}"
                    f" in event type '{self.__name__}' is an instance of"
                    f"{type(value).__name__}, expected "
                    f"one of these types: {typenames}"
                )
            self.default_values_for_attrs[attr] = value

    def __call__(self, **attrs):
        if self.attrs:
            for attr in attrs:
                try:
                    assert attr in self.attrs
                except AssertionError as err:
                    raise TypeError(
                        f"unexpected attributes for event type '{self.__name__}'"
                    ) from err
            for attr, attr_type in self.attrs.items():
                if attr in attrs:
                    # Raise an error if argument is given, but not an instance of
                    # the expected type(s)
                    if not isinstance(
                        attrs[attr], getattr(attr_type, "__args__", attr_type)
                    ):
                        typenames = ",".join(
                            (
                                tp.__name__
                                for tp in getattr(attr_type, "__args__", (attr_type,))
                            )
                        )
                        raise TypeError(
                            f"given value ({attrs[attr]}) for attribute {attr}"
                            f" in event type '{self.__name__}' is an instance of"
                            f"{type(attrs[attr]).__name__}, expected "
                            f"one of these types: {typenames}"
                        )
                    continue
                else:
                    if "Optional" in repr(attr_type):
                        pass
                    elif (
                        isinstance(attr_type, UnionType)
                        and NoneType in attr_type.__args__
                    ):
                        pass
                    elif attr in self.default_values_for_attrs:
                        attrs[attr] = self.default_values_for_attrs[attr]
                    else:
                        raise TypeError(
                            f"missing argument for event type '{self.__name__}' : '{attr}'"
                        )
        else:
            if attrs:
                raise TypeError(
                    f"event type '{self.__name__}' does not take any attributes"
                )
        return pygame.event.Event(self.code, **attrs)


def get_event_def(code: int) -> _EventDefinition:
    """Return the corresponding event type specification for the given code.

    :param code: The code you wish to retrive the event specs of.
    :return: The corresponding definition."""
    return _EventDefinition.from_code(code)


def get_event_def_from_name(name: str) -> _EventDefinition:
    """Return the corresponding event type specification for the given name.

    :param name: The name to search for in the existing event types.
    :return: The corresponding definition."""
    return _EventDefinition.from_name(name)


def create_custom_event_type(
    name: str, **attributes: Union[Type, SpecialForm, UnionType]
) -> int:
    """Register a new event type and its specifications.

    :param name: The definition name (will be used in mostly error messages).
    :param attributes: The event's required attributes. If empty,
    trying to add any attributes to an event of this type will result in
    a TypeError being raised.
    :raise pygame.error: if no more event types can be registered.
    :raise ValueError: if the given name is already associated
    to an existing event type."""
    _EventDefinition._check_not_registered(name)
    created_code = pygame.event.custom_type()
    edef = _EventDefinition(name, created_code, **attributes)
    _EventDefinition.add_to_edef_cache(edef)
    return created_code


def post_event(code: int, **attrs: Type | SpecialForm):
    """Create and post an event of the given type with attributes listed
    as keyword arguments.

    :param code: The event code to give.
    :param attrs: The attributes the event will have.
    :raise TypeError: if required attributes are missing,
    have been provided a value of the wrong type, or if
    some attributes that don't exist in the current event type
    have been given.
    :raise ValueError: if the given code is not a valid event type."""
    edef = _EventDefinition.from_code(code)
    pygame.event.post(edef(**attrs))


# Custom Events:

# Adding this to the event definition cache so we can easily post quit events
_EventDefinition.add_to_edef_cache(_EventDefinition("Quit", pygame.QUIT))

OPEN_INVENTORY = create_custom_event_type("OpenInventory")

DIALOG_SHOW = create_custom_event_type("DIALOG_SHOW", dial=str)
DIALOG_ADVANCE = create_custom_event_type("DIALOG_ADVANCE")

START_QUAKE = create_custom_event_type("StartQuake", duration=float)

PLAYER_TASK = create_custom_event_type("PlayerTask")
