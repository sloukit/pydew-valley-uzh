from enum import Enum, IntEnum, StrEnum, nonmember, auto  # noqa
from random import randint


class ZoomState(IntEnum):
    NOT_ZOOMING = 0
    ZOOMING_IN = auto()
    ZOOMING_OUT = auto()
    ZOOM = auto()


class PlayerState(IntEnum):
    IDLE = 0
    WALK = 1


class ItemToUse(IntEnum):
    """Both available options for Player.use_tool. If any more have to be added, put them as members of this enum."""

    REGULAR_TOOL = 0
    SEED = 1


_FT_SERIALISED_STRINGS = ("none", "axe", "hoe", "water", "corn_seed", "tomato_seed")


class GameState(IntEnum):
    MAIN_MENU = 0
    PLAY = 1
    PAUSE = 2
    SETTINGS = 3
    SHOP = 4
    EXIT = 5
    GAME_OVER = 6
    WIN = 7
    CREDITS = 8
    # Special value: when switched to this value, the game
    # saves and then sets its current state back to PLAY
    SAVE_AND_RESUME = 9
    INVENTORY = 10
    ROUND_END = 11
    OUTGROUP_MENU = 12


# NOTE : DO NOT pay attention to anything the IDE might complain about in this class, as the enum generation mechanisms
# will ensure _SERIALISABLE_STRINGS is actually treated like a tuple of strings instead of an integer.
class _SerialisableEnum(IntEnum):
    _SERIALISABLE_STRINGS = nonmember(())  # This will be overridden in derived enums.

    def as_serialised_string(self):
        # We keep that method separate from the actual str dunder, so we can still get the original repr when debugging
        return self._SERIALISABLE_STRINGS[self]  # noqa

    def as_user_friendly_string(self):
        text = self.as_serialised_string()
        return text.replace("_", " ")

    @classmethod
    def from_serialised_string(cls, val: str):
        """Return an enum member from a serialised string.

        :param val: The serialised string.
        :return: The corresponding enum member.
        :raise LookupError: if no enum member matches this string."""
        try:
            return cls(cls._SERIALISABLE_STRINGS.index(val))  # noqa
        except IndexError as exc:
            raise LookupError(
                f"serialised string '{val}' does not match any member in enum '{cls.__name__}'"
            ) from exc


class InventoryResource(_SerialisableEnum):
    """All stored items in the inventory."""

    _SERIALISABLE_STRINGS = nonmember(
        (
            "wood",
            "apple",
            "blackberry",
            "blueberry",
            "raspberry",
            "orange",
            "peach",
            "pear",
            "corn",
            "tomato",
            "corn_seed",
            "tomato_seed",
        )
    )

    # All item worths in the game. When traders buy things off you, they pay you for half the worth.
    # If YOU buy something from THEM, then you have to pay the FULL worth, though.
    _ITEM_WORTHS = nonmember(
        (
            8,  # WOOD
            4,  # APPLE
            5,  # BLACKBERRY
            5,  # BLUEBERRY
            5,  # RASPBERRY
            20,  # ORANGE
            15,  # PEACH
            10,  # PEAR
            20,  # CORN
            40,  # TOMATO
            4,  # CORN_SEED
            5,  # TOMATO_SEED
        )
    )

    WOOD = 0
    APPLE = 1
    BLACKBERRY = 2
    BLUEBERRY = 3
    RASPBERRY = 4
    ORANGE = 5
    PEACH = 6
    PEAR = 7
    CORN = 8
    TOMATO = 9
    CORN_SEED = 10
    TOMATO_SEED = 11

    def get_worth(self):
        return self._ITEM_WORTHS[self]  # noqa

    def is_seed(self):
        return self >= self.CORN_SEED

    def is_fruit(self):
        return self.APPLE <= self <= self.PEAR


class FarmingTool(_SerialisableEnum):
    """Notably used to distinguish the different farming tools (including seeds) in-code."""

    _SERIALISABLE_STRINGS = nonmember(
        ("none", "axe", "hoe", "water", "corn_seed", "tomato_seed")
    )

    NONE = 0  # Possible placeholder value if needed somewhere
    AXE = 1
    HOE = 2
    WATERING_CAN = 3
    CORN_SEED = 4
    TOMATO_SEED = 5

    _AS_IRS = nonmember(
        {
            CORN_SEED: InventoryResource.CORN_SEED,
            TOMATO_SEED: InventoryResource.TOMATO_SEED,
        }
    )

    _AS_NS_IRS = nonmember(
        {CORN_SEED: InventoryResource.CORN, TOMATO_SEED: InventoryResource.TOMATO}
    )

    # Using frozenset to ensure this cannot change
    _swinging_tools = nonmember(frozenset({HOE, AXE}))

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
        return self._AS_IRS.get(self, self)  # noqa

    def as_nonseed_inventory_resource(self):
        """Converts self to non-seed InventoryResource type if possible.
        (Conversion is possible if self is considered a seed.)"""
        return self._AS_NS_IRS.get(self, self)  # noqa


class SeedType(IntEnum):
    _AS_FTS = nonmember((FarmingTool.CORN_SEED, FarmingTool.TOMATO_SEED))

    _AS_IRS = nonmember((InventoryResource.CORN_SEED, InventoryResource.TOMATO_SEED))

    _AS_NS_IRS = nonmember((InventoryResource.CORN, InventoryResource.TOMATO))

    CORN = 0
    TOMATO = 1

    @classmethod
    def from_farming_tool(cls, val: FarmingTool):
        return cls(cls._AS_FTS.index(val))  # noqa

    @classmethod
    def from_inventory_resource(cls, val: InventoryResource):
        return cls(cls._AS_IRS.index(val))  # noqa

    def as_fts(self):
        return self._AS_FTS[self]  # noqa

    def as_ir(self):
        return self._AS_IRS[self]  # noqa

    def as_nonseed_ir(self):
        return self._AS_NS_IRS[self]  # noqa

    def as_plant_name(self):
        return self._AS_FTS[self].as_serialised_string().removesuffix("_seed")  # noqa


class Direction(IntEnum):
    UP = 0
    RIGHT = auto()
    DOWN = auto()
    LEFT = auto()
    UPLEFT = auto()
    UPRIGHT = auto()
    DOWNRIGHT = auto()
    DOWNLEFT = auto()

    @classmethod
    def random(cls):
        return Direction(randint(0, Direction.DOWNLEFT.value))

    def get_opposite(self):
        return _OPPOSITES[self]  # noqa


_OPPOSITES = (
    Direction.DOWN,
    Direction.LEFT,
    Direction.UP,
    Direction.RIGHT,
    Direction.DOWNRIGHT,
    Direction.DOWNLEFT,
    Direction.UPLEFT,
    Direction.UPRIGHT,
)


class EntityState(StrEnum):
    IDLE = "idle"
    WALK = "walk"

    AXE = "axe"
    HOE = "hoe"
    WATER = "water"

    # Special values for equipment rendering

    GOGGLES_AXE = "goggles_axe"
    GOGGLES_HOE = "goggles_hoe"
    GOGGLES_IDLE = "goggles_idle"
    GOGGLES_WALK = "goggles_walk"
    GOGGLES_WATER = "goggles_water"

    OUTGROUP_AXE = "outgroup_axe"
    OUTGROUP_HOE = "outgroup_hoe"
    OUTGROUP_IDLE = "outgroup_idle"
    OUTGROUP_WALK = "outgroup_walk"
    OUTGROUP_WATER = "outgroup_water"

    HAT_AXE = "hat_axe"
    HAT_HOE = "hat_hoe"
    HAT_IDLE = "hat_idle"
    HAT_WALK = "hat_walk"
    HAT_WATER = "hat_water"

    HORN_AXE = "horn_axe"
    HORN_HOE = "horn_hoe"
    HORN_IDLE = "horn_idle"
    HORN_WALK = "horn_walk"
    HORN_WATER = "horn_water"

    NECKLACE_AXE = "necklace_axe"
    NECKLACE_HOE = "necklace_hoe"
    NECKLACE_IDLE = "necklace_idle"
    NECKLACE_WALK = "necklace_walk"
    NECKLACE_WATER = "necklace_water"


class Layer(IntEnum):
    WATER = 0
    GROUND = auto()
    GROUND_OBJECTS = auto()
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


class SpecialObjectLayer(StrEnum):
    INTERACTIONS = "Interactions"
    COLLISIONS = "Collisions"
    TREES = "Trees"
    PLAYER = "Player"
    NPCS = "NPCs"
    ANIMALS = "Animals"
    CAMERA_TARGETS = "Camera Targets"
    ZOOM_AREAS = "Zoom Areas"
    MINIGAME = "Minigame"


class Map(StrEnum):
    FARM = "farm"
    NEW_FARM = "farm_new"
    FOREST = "forest"
    TOWN = "town"
    MINIGAME = "minigame"


class StudyGroup(IntEnum):
    """The group in which a certain character belongs to."""

    NO_GROUP = 0  # Set at the beginning of the game.
    INGROUP = auto()
    OUTGROUP = auto()


class ClockVersion(IntEnum):
    ANALOG = 0
    DIGITAL = auto()


class ScriptedSequenceType(StrEnum):
    PLAYER_RECEIVES_HAT = "player_receives_hat"
    PLAYER_RECEIVES_NECKLACE = "player_receives_necklace"
    NPC_RECEIVES_NECKLACE = "npc_receives_necklace"
