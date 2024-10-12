"""Camera targets for a possible cutscene in a map."""

from dataclasses import dataclass, field

from src.settings import DEFAULT_ANIMATION_NAME, Coordinate


@dataclass
class CameraTarget:
    """A target the camera will move towards during cutscenes."""

    _pos: Coordinate
    _targ_id: int
    _animation_name: str = field(default=DEFAULT_ANIMATION_NAME)
    _speed: int = field(default=200)
    _pause: float = field(default=0)

    def __post_init__(self):
        if self._speed <= 0:
            raise ValueError("speed must be stricly positive")
        if self._pause < 0:
            raise ValueError("pause duration must be positive")
        if not self._targ_id:
            # Special case: the first camera target has no speed, because the camera will start there
            self._speed = 0

    def __iter__(self):
        return iter(self._pos)

    @property
    def animation_name(self):
        """The name of particular animation sequence."""
        return self._animation_name

    @property
    def speed(self):
        """The speed the camera will go at to reach this target."""
        return self._speed

    @property
    def pause(self):
        """The amount of time the camera will stay on the target upon reaching it, in seconds."""
        return self._pause

    @property
    def pos(self):
        return self._pos

    def targ_id(self):
        """The target ID. The camera will move through all targets for a cutscene
        in ascending order, depending on this value."""
        return self._targ_id

    @classmethod
    def get_null_target(cls):
        """Return the null target.
        This constant is used when initialising
        SceneAnimation objects for the first time."""
        return _NULL_TARGET


_NULL_TARGET = CameraTarget((0, 0), 0, DEFAULT_ANIMATION_NAME, 1, 0)
