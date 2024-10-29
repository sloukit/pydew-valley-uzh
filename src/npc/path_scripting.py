from dataclasses import dataclass, field

from src.enums import AIState


@dataclass
class Waypoint:
    pos: tuple[int, int]
    speed: int
    waiting_duration: float


@dataclass
class AIScriptedPath:
    waypoints: list[Waypoint]

    start_pos: tuple[float, float]

    previous_speed: int = field(default=0, init=False)

    running: bool = field(default=False, init=False)
    index: int = field(default=0, init=False)
    next_state: AIState = field(default=AIState.IDLE, init=False)
