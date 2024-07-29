from enum import Enum, IntEnum, StrEnum, nonmember, auto  # noqa


class PlayerState(IntEnum):
    IDLE = 0
    WALK = 1


class ItemToUse(IntEnum):
    """Both available options for Player.use_tool. If any more have to be added, put them as members of this enum."""
    REGULAR_TOOL = 0
    SEED = 1


_FT_SERIALISED_STRINGS = (
    "none",
    "axe",
    "hoe",
    "water",
    "corn_seed",
    "tomato_seed"
)


class GameState(IntEnum):
    MAIN_MENU = 0
    LEVEL = 1
    PAUSE = 2
    SETTINGS = 3
    SHOP = 4
    EXIT = 5
    GAME_OVER = 6
    WIN = 7
    CREDITS = 8


# NOTE : DO NOT pay attention to anything the IDE might complain about in this class, as the enum generation mechanisms
# will ensure _SERIALISABLE_STRINGS is actually treated like a tuple of strings instead of an integer.
class _SerialisableEnum(IntEnum):
    _SERIALISABLE_STRINGS = nonmember(())  # This will be overridden in derived enums.

    def as_serialised_string(self):
        # We keep that method separate from the actual str dunder, so we can still get the original repr when debugging
        return self._SERIALISABLE_STRINGS[self]  # noqa

    @classmethod
    def from_serialised_string(cls, val: str):
        """Return an enum member from a serialised string.

        :param val: The serialised string.
        :return: The corresponding enum member.
        :raise LookupError: if no enum member matches this string."""
        try:
            return cls(cls._SERIALISABLE_STRINGS.index(val))  # noqa
        except IndexError as exc:
            raise LookupError(f"serialised string '{val}' does not match any member in enum '{cls.__name__}'") from exc


class InventoryResource(_SerialisableEnum):
    """All stored items in the inventory."""
    _SERIALISABLE_STRINGS = nonmember(
        (
            "wood",
            "apple",
            "corn",
            "tomato",
            "corn_seed",
            "tomato_seed"
        )
    )

    # All item worths in the game. When traders buy things off you, they pay you for half the worth.
    # If YOU buy something from THEM, then you have to pay the FULL worth, though.
    _ITEM_WORTHS = nonmember(
        (
            8,  # WOOD
            4,  # APPLE
            20,  # CORN
            40,  # TOMATO
            4,  # CORN_SEED
            5,  # TOMATO_SEED
        )
    )

    WOOD = 0
    APPLE = 1
    CORN = 2
    TOMATO = 3
    CORN_SEED = 4
    TOMATO_SEED = 5

    def get_worth(self):
        return self._ITEM_WORTHS[self]  # noqa

    def is_seed(self):
        return self >= self.CORN_SEED


class FarmingTool(_SerialisableEnum):
    """Notably used to distinguish the different farming tools (including seeds) in-code."""
    _SERIALISABLE_STRINGS = nonmember(
        (
            "none",
            "axe",
            "hoe",
            "water",
            "corn_seed",
            "tomato_seed"
        )
    )

    NONE = 0  # Possible placeholder value if needed somewhere
    AXE = 1
    HOE = 2
    WATERING_CAN = 3
    CORN_SEED = 4
    TOMATO_SEED = 5

    _AS_IR = nonmember(
        {
            CORN_SEED: InventoryResource.CORN,
            TOMATO_SEED: InventoryResource.TOMATO
        }
    )

    @property
    def _swinging_tools(self):
        return {self.HOE, self.AXE}

    def is_swinging_tool(self):
        return self in self._swinging_tools

    def is_seed(self):
        return self >= self.get_first_seed_id()

    @classmethod
    def get_first_tool_id(cls):
        """Return the first tool ID. This might change in the course of development."""
        return cls.AXE

    @classmethod
    def get_tool_count(cls):
        return cls.get_first_seed_id() - cls.get_first_tool_id()

    @classmethod
    def get_seed_count(cls):
        return len(cls) - cls.get_first_seed_id()

    @classmethod
    def get_first_seed_id(cls):
        """Same as get_first_tool_id, but for the seeds. Duh."""
        return cls.CORN_SEED

    def as_inventory_resource(self):
        """Converts self to InventoryResource type if possible.
        (Conversion is possible if self is considered a seed.)"""
        return self._AS_IR.get(self, self)


class SeedType(IntEnum):

    _AS_FTS = nonmember(
        (
            FarmingTool.CORN_SEED,
            FarmingTool.TOMATO_SEED
        )
    )

    _AS_IRS = nonmember(
        (
            InventoryResource.CORN_SEED,
            InventoryResource.TOMATO_SEED
        )
    )

    _AS_NS_IRS = nonmember(
        (
            InventoryResource.CORN,
            InventoryResource.TOMATO
        )
    )

    CORN = 0
    TOMATO = 1

    @classmethod
    def from_farming_tool(cls, val: FarmingTool):
        return cls(cls._AS_FTS.index(val))

    @classmethod
    def from_inventory_resource(cls, val: InventoryResource):
        return cls(cls._AS_IRS.index(val))

    def as_ir(self):
        return self._AS_IRS[self]

    def as_nonseed_ir(self):
        return self._AS_NS_IRS[self]

    def as_plant_name(self):
        return self._AS_FTS[self].as_serialised_string().removesuffix("_seed")


class Direction(IntEnum):
    UP = 0
    RIGHT = auto()
    DOWN = auto()
    LEFT = auto()


class EntityState(StrEnum):
    IDLE = "idle"
    WALK = "walk"

    AXE = "axe"
    HOE = "hoe"
    WATER = "water"


class Layer(IntEnum):
    WATER = 0
    LOWER_GROUND = auto()
    UPPER_GROUND = auto()
    SOIL = auto()
    SOIL_WATER = auto()
    RAIN_FLOOR = auto()
    PLANT = auto()
    MAIN = auto()
    FRUIT = auto()
    BORDER = auto()
    RAIN_DROPS = auto()
    PARTICLES = auto()
    EMOTES = auto()
    TEXT_BOX = auto()


class Map(StrEnum):
    FARM = "farm"
    FOREST = "forest"
