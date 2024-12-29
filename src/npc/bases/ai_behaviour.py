import random
import warnings
from abc import ABC
from collections.abc import Callable

import pygame
from pathfinding.core.grid import Grid  # type: ignore[import-untyped]

from src.enums import AIState
from src.npc.bases.ai_behaviour_base import AIBehaviourBase
from src.npc.behaviour.ai_behaviour_tree_base import ContextType, NodeWrapper
from src.npc.path_scripting import AIScriptedPath
from src.settings import SCALED_TILE_SIZE


class AIBehaviour(AIBehaviourBase, ABC):
    def __init__(self, behaviour_tree_context: ContextType):  # noqa
        """
        !IMPORTANT! AIBehaviour doesn't call Entity.__init__ while still
        relying on it. Be aware that when inheriting from AIBehaviour you
        should first inherit from Entity itself, or inherit from another class
        that has Entity as base.
        """
        # AI-controlled Entities will idle for 1-4s on game start
        self.pf_state = AIState.IDLE
        self.pf_state_duration = 1 + random.random() * 3

        self.pf_path = []

        self._script = None

        self.behaviour_tree_context = behaviour_tree_context
        self.conditional_behaviour_tree = None
        self.continuous_behaviour_tree = None

        self.__on_path_abortion_funcs = []
        self.__on_path_completion_funcs = []

        self.__on_stop_moving_funcs = []

        self.__on_script_finish_funcs = []

    @property
    def conditional_behaviour_tree(self):
        return self._conditional_behaviour_tree

    @conditional_behaviour_tree.setter
    def conditional_behaviour_tree(self, value: NodeWrapper | None):
        self._conditional_behaviour_tree = value

    @property
    def continuous_behaviour_tree(self):
        return self._continuous_behaviour_tree

    @continuous_behaviour_tree.setter
    def continuous_behaviour_tree(self, value: NodeWrapper | None):
        self._continuous_behaviour_tree = value

    def on_path_abortion(self, func: Callable[[], None]):
        self.__on_path_abortion_funcs.append(func)
        return

    def abort_path(self):
        self.pf_state = AIState.IDLE
        self.direction.update((0, 0))
        self.pf_state_duration = 1 + random.random() * 1

        for func in self.__on_path_abortion_funcs:
            func()

        self.stop_moving()
        return

    def on_path_completion(self, func: Callable[[], None]):
        self.__on_path_completion_funcs.append(func)
        return

    def complete_path(self):
        self.pf_state = AIState.IDLE
        self.direction.update((0, 0))
        self.pf_state_duration = 2 + random.random() * 3

        for func in self.__on_path_completion_funcs:
            func()

        self.stop_moving()
        return

    def exit_idle(self):
        if self._script and self._script.running:
            self._progress_script()

        if self.conditional_behaviour_tree is not None:
            self.conditional_behaviour_tree.run(self.behaviour_tree_context)

    def on_stop_moving(self, func: Callable[[], None]):
        self.__on_stop_moving_funcs.append(func)
        return

    def stop_moving(self):
        if self._script and self._script.running:
            self._progress_script()

        for func in self.__on_stop_moving_funcs:
            func()

        self.__on_path_abortion_funcs.clear()
        self.__on_path_completion_funcs.clear()
        self.__on_stop_moving_funcs.clear()
        return

    def on_script_finish(self, func: Callable[[], None]):
        self.__on_script_finish_funcs.append(func)
        return

    def finish_script(self):
        self._script.running = False
        self.speed = self._script.previous_speed

        for func in self.__on_script_finish_funcs:
            func()
        return

    def run_script(self, script: AIScriptedPath):
        self._script = script
        self._script.previous_speed = self.speed
        self._script.running = True
        self._progress_script()

    def _progress_script(self):
        try:
            waypoint = self._script.waypoints[self._script.index]
        except IndexError:
            self.finish_script()
            return

        if self._script.next_state == AIState.IDLE:
            if self.pf_state == AIState.MOVING:
                self.abort_path()
            self.pf_state_duration = waypoint.waiting_duration
            self._script.next_state = AIState.MOVING
        else:
            self.create_path_to_tile(waypoint.pos)
            self.speed = waypoint.speed
            self._script.next_state = AIState.IDLE
            self._script.index += 1

    def create_path_to_tile(self, coord: tuple[int, int], pf_grid: Grid = None) -> bool:
        """
        Initiates the AI-controlled Entity to move to the specified tile.

        Note: Path generation has a high performance impact,
        calling it too often at once will cause the game to stutter

        :param coord: Coordinate of the tile the Entity should move to.
        :param pf_grid: (Optional) pathfinding grid to use. Defaults to self.pf_grid
        :return: Whether the path has successfully been created.
        """

        if pf_grid is None:
            pf_grid = self.pf_grid

        if not pf_grid.walkable(coord[0], coord[1]):
            return False

        # current NPC position on the tilemap
        tile_coord = (
            pygame.Vector2(self.hitbox_rect.centerx, self.hitbox_rect.centery)
            / SCALED_TILE_SIZE
        )

        self.pf_state = AIState.MOVING
        self.pf_state_duration = 0

        pf_grid.cleanup()

        try:
            start = pf_grid.node(int(tile_coord.x), int(tile_coord.y))
        except IndexError as e:
            # FIXME: Occurs when NPCs get stuck inside each other at the edge
            #  of the map and one of them gets pushed out of the walkable area
            warnings.warn(f"NPC is at invalid location {tile_coord}\nFull error: {e}")
            return False
        end = pf_grid.node(*[int(i) for i in coord])

        path_raw = self.pf_finder.find_path(start, end, pf_grid)

        # The first position in the path will always be removed as it is the
        # same coordinate the NPC is already standing on. Otherwise, if the NPC
        # is just standing a little bit off the center of its current
        # coordinate, it may turn around quickly once it reaches it, if the
        # second coordinate of the path points in the same direction as where
        # the NPC was just standing.
        self.pf_path = [(i.x + 0.5, i.y + 0.5) for i in path_raw[0][1:]]

        if not self.pf_path:
            return False

        return True

    def create_step_to_coord(self, coord: tuple[float, float]) -> bool:
        self.pf_path.append((coord[0] / SCALED_TILE_SIZE, coord[1] / SCALED_TILE_SIZE))
        return True

    def move(self, dt: float):
        self.hitbox_rect.update(
            (
                self.rect.x + self._current_hitbox.x,
                self.rect.y + self._current_hitbox.y,
            ),
            self._current_hitbox.size,
        )

        if self.pf_state == AIState.IDLE:
            self.update_idle(dt)

        if self.pf_state == AIState.MOVING:
            self.update_moving(dt)

        self.rect.update(
            (
                self.hitbox_rect.x - self._current_hitbox.x,
                self.hitbox_rect.y - self._current_hitbox.y,
            ),
            self.rect.size,
        )

    def update_idle(self, dt: float):
        self.pf_state_duration -= dt

        if self.pf_state_duration <= 0:
            self.exit_idle()

    def update_moving(self, dt: float):
        if not self.pf_path:
            # runs in case the path has been emptied in the meantime
            #  (e.g. NPCBehaviourMethods.wander_to_interact created a path
            #   to a tile adjacent to the NPC)
            self.complete_path()
            return

        # Get the next point in the path
        next_point = self.pf_path[0]
        # current exact NPC position on the tilemap
        current_point = (
            self.hitbox_rect.centerx / SCALED_TILE_SIZE,
            self.hitbox_rect.centery / SCALED_TILE_SIZE,
        )

        # remaining distance the NPC moves in the current frame
        remaining_distance = self.speed * dt / SCALED_TILE_SIZE

        while remaining_distance:
            if current_point == next_point:
                # the NPC reached its current target position
                self.pf_path.pop(0)

            if not self.pf_path:
                # the NPC has completed its path
                self.complete_path()
                break

            next_point = self.pf_path[0]

            # x- and y-distances from the NPCs current position to its
            # target position
            dx = next_point[0] - current_point[0]
            dy = next_point[1] - current_point[1]

            distance = (dx**2 + dy**2) ** 0.5

            if remaining_distance >= distance:
                # the NPC reaches its current target position in the
                # current frame
                current_point = next_point
                remaining_distance -= distance
            else:
                # the NPC does not reach its current target position in the
                # current frame, so it continues to move towards it
                current_point = (
                    current_point[0] + dx * remaining_distance / distance,
                    current_point[1] + dy * remaining_distance / distance,
                )
                remaining_distance = 0

                # Rounding the direction leads to smoother animations,
                #  e.g. if the distance vector was (-0.99, -0.01), the NPC
                #  would face upwards, although it moves much more to the
                #  left than upwards, as the get_facing_direction method
                #  favors vertical movement
                self.direction.update((round(dx / distance), round(dy / distance)))

        self.hitbox_rect.update(
            (
                current_point[0] * SCALED_TILE_SIZE - self.hitbox_rect.width / 2,
                current_point[1] * SCALED_TILE_SIZE - self.hitbox_rect.height / 2,
            ),
            self.hitbox_rect.size,
        )

        self.check_collision()

        if self.is_colliding:
            self.abort_path()

    def update(self, dt: float):
        if self.continuous_behaviour_tree is not None:
            self.continuous_behaviour_tree.run(self.behaviour_tree_context)

        super().update(dt)
