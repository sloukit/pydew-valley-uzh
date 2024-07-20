"""Expansion over Pygame's event management system."""
import pygame
from typing import Union, Type, NoReturn, Self
from types import UnionType, NoneType

type SpecialForm = NoReturn


class _EventDefinition:
    """Additional information about a specific event type.

    This allows us to ensure that all required arguments are given
    when posting an event of a certain type (namely, by raising errors if they
    aren't given)."""

    _EDEF_CACHE = {}  # INTERNAL USAGE!
    _EDEF_NAMES = set()
    __slots__ = (
        "name",
        "__name__",
        "code",
        "_attrs",
        "default_values_for_attrs"
    )

    @classmethod
    def from_code(cls, code: int) -> Self:
        """Return the corresponding event definition for a given code."""
        try:
            return cls._EDEF_CACHE[code]
        except LookupError as exc:
            err = f"given code '{code}' does not match an existing event type"
            raise ValueError(err) from exc

    @classmethod
    def from_name(cls, name: str) -> Self:
        """Return the corresponding event definition for a given name."""
        for edef in cls._EDEF_CACHE.values():
            if edef.__name__ == name:
                return edef
        err = f"given name '{name}' does not match an existing event type"
        raise ValueError(err)

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
        :raise ValueError: if the given name is not
        available for registering."""
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
        attrs_str = ', '.join(
            f'{attr}:{value}' for attr, value in self.attrs.items()
        )
        return (
            f"""<EventDefinition(name='{self.__name__}',
            code={self.code},
            {attrs_str})>"""
        )

    def __hash__(self):
        return hash(
            (self.__name__, self.code) + tuple(self.attrs.items())
        )

    @property
    def attrs(self):
        return self._attrs

    def set_default_for_attr(self, attr: str, value):
        """Set the default value for an attribute required by this event type.

        :param attr: The attribute to set a default for.
        :param value: The corresponding default value.
        :raise TypeError: if the value does not match the type
        for this attribute given when creating the event type.
        :raise ValueError: if the attribute does not exist
        for this event type."""

        if attr not in self.attrs:
            raise ValueError(
                f"invalid attribute for event type {self.__name__} : '{attr}'"
            )
        else:
            attr_type = self.attrs[attr]
            if not isinstance(
                    value,
                    getattr(
                        attr_type,
                        "__args__",
                        attr_type
                    )
            ):
                typenames = ",".join(
                    map(
                        lambda tp: tp.__name__,
                        getattr(
                            attr_type,
                            "__args__",
                            (attr_type,)
                        )
                    )
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
            self.validate_attrs(attrs)
            self.check_and_set_attr_types(attrs)
        else:
            self.handle_no_attrs(attrs)
        return pygame.event.Event(self.code, **attrs)

    def validate_attrs(self, attrs):
        """Validate that all provided attributes are expected."""
        for attr in attrs:
            if attr not in self.attrs:
                raise TypeError(
                    f"Unexpected attributes for event type '{self.__name__}'"
                )

    def check_and_set_attr_types(self, attrs):
        """Check the type of each attribute and
        set default values if needed."""
        for attr, attr_type in self.attrs.items():
            if attr in attrs:
                self.validate_attr_type(attr, attrs[attr], attr_type)
            else:
                self.handle_missing_attr(attr, attr_type, attrs)

    def validate_attr_type(self, attr, value, attr_type):
        """Validate the type of a specific attribute."""
        if not isinstance(value, getattr(attr_type, "__args__", attr_type)):
            typenames = ",".join(
                map(
                    lambda tp: tp.__name__,
                    getattr(attr_type, "__args__", (attr_type,))
                )
            )
            message = (
                f"Given value ({value}) for attribute {attr} "
                f"in event type '{self.__name__}' is an instance "
                f"of {type(value).__name__},"
                f"expected one of these types: {typenames}"
            )
            raise TypeError(message)

    def handle_missing_attr(self, attr, attr_type, attrs):
        """Handle missing attributes and set default values if applicable."""
        is_optional = "Optional" in repr(attr_type)
        is_union_with_none = (
            isinstance(attr_type, UnionType) and NoneType in attr_type.__args__
        )

        if is_optional or is_union_with_none:
            return
        elif attr in self.default_values_for_attrs:
            attrs[attr] = self.default_values_for_attrs[attr]
        else:
            raise TypeError(
                f"Missing argument for event type '{self.__name__}' : '{attr}'"
            )

    def handle_no_attrs(self, attrs):
        """Handle the case when no attributes are expected."""
        if attrs:
            raise TypeError(
                f"Event type '{self.__name__}' does not take any attributes"
            )


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
        name: str,
        **attributes: Union[Type, SpecialForm, UnionType]
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
