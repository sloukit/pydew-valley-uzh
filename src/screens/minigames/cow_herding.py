import glob
import random

# from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Type

import pygame
import pygame.gfxdraw
from pathfinding.core.grid import Grid  # type: ignore[import-untyped]

from src.controls import Controls
from src.enums import Direction, StudyGroup
from src.exceptions import MinigameSetupError
from src.groups import PersistentSpriteGroup
from src.npc.cow import Cow
from src.npc.npc import NPC
from src.npc.path_scripting import AIScriptedPath, Waypoint
from src.npc.setup import AIData
from src.npc.utils import pf_add_matrix_collision
from src.overlay.overlay import Overlay
from src.screens.game_map import GameMap
from src.screens.minigames.base import Minigame, MinigameState
from src.screens.minigames.cow_herding_behaviour import (
    CowHerdingBehaviourTree,
    CowHerdingContext,
)
from src.screens.minigames.cow_herding_overlay import (
    _CowHerdingOverlay,
    _CowHerdingScoreboard,
)
from src.settings import SCALE_FACTOR, SoundDict
from src.sprites.base import Sprite
from src.sprites.entities.player import Player
from src.sprites.setup import ENTITY_ASSETS
from src.support import resource_path
from src.utils import json_load


def _set_player_controls(controls: Type[Controls], value: bool):
    # movement is not disabled
    controls.USE.disabled = value
    controls.NEXT_TOOL.disabled = value
    controls.NEXT_SEED.disabled = value
    controls.PLANT.disabled = value
    # interact is not disabled
    controls.INVENTORY.disabled = value
    controls.EMOTE_WHEEL.disabled = value
    # overlays are not disabled
    controls.DEBUG_SHOW_DIALOG.disabled = value
    controls.ADVANCE_DIALOG.disabled = value


@dataclass
class CowHerdingScriptedPath:
    """
    Contains all paths followed by the entities on the opponent's side

    Attributes:
        random_seed: Seed used to create the path
        total_time: Time the opponent should need to herd all his cows into the barn
        paths: Maps the ID (the entity's object ID on the tilemap) of all controlled entities to their paths
    """

    random_seed: float
    total_time: float
    paths: dict[int, AIScriptedPath]

    @classmethod
    def from_file(cls, path: str):
        with open(resource_path(path)) as file:
            data = json_load(file)

        random_seed = data["random_seed"]
        total_time = data["total_time"]
        paths = {}
        for eid, entity in data["paths"].items():
            waypoints = []
            for waypoint in entity["waypoints"]:
                waypoints.append(
                    Waypoint(
                        waypoint["pos"], waypoint["speed"], waypoint["waiting_duration"]
                    )
                )
            paths[int(eid)] = AIScriptedPath(
                start_pos=entity["start_pos"], waypoints=waypoints
            )

        return cls(random_seed=random_seed, total_time=total_time, paths=paths)


@dataclass
class CowHerdingState(MinigameState):
    game_map: GameMap
    player: Player
    all_sprites: PersistentSpriteGroup
    collision_sprites: PersistentSpriteGroup
    overlay: Overlay
    sounds: SoundDict


@dataclass
class CowHerdingSideState:
    """
    Attributes:
        prefix: The string prefix of all objects associated with this side ("L" or "R")
        contestant: The player or their NPC opponent
        cows: Maps the ID (the entity's object ID on the tilemap) of all cows to the corresponding Cow object
        initial_positions: Maps the ID of all cows to their initial positions as specified on the tilemap
        barn_entrance_collider: Collider separating the inside of the barn from the range

        cows_herded_in: Amount of cows on this side that have already been herded into the barn
        finished_time: First time at which all cows were in the barn (-1 if it has not yet occurred)
    """

    prefix: str
    contestant: Player | NPC
    cows: dict[int, Cow] = field(default_factory=dict)
    initial_positions: dict[int, tuple[float, float]] = field(default_factory=dict)
    barn_entrance_collider: Sprite = None

    cows_herded_in: int = field(default=0, init=False)
    finished_time: float = field(default=-1, init=False)

    @property
    def cows_total(self) -> int:
        return len(self.cows)

    @property
    def finished(self) -> bool:
        return self.cows_herded_in == self.cows_total


class DummySprite:
    rect: pygame.FRect

    def __init__(self, rect: pygame.FRect):
        self.rect = rect


class CowHerding(Minigame):
    _state: CowHerdingState
    player_controls: Type[Controls]
    camera_target: DummySprite
    display_surface: pygame.Surface

    overlay: _CowHerdingOverlay

    scoreboard: _CowHerdingScoreboard

    _player_side: CowHerdingSideState
    _opponent_side: CowHerdingSideState
    _opponent_side_script: CowHerdingScriptedPath

    _opponent_id: int

    # seconds until the countdown starts
    _ani_cd_start: int
    _ani_cd_ready_up_dur: int
    _ani_cd_dur: int
    _game_start: int

    # current minigame time (as seen on the minigame timer)
    _minigame_time: int

    # whether the Player has completed the minigame yet
    _complete: bool

    # collision sprites for the minigame contestants (i.e. the Player and their opponent)
    contestant_collision_sprites: PersistentSpriteGroup

    def __init__(self, state: CowHerdingState, round_config: dict[str, Any]):
        super().__init__(state)
        self.round_config = round_config
        self.camera_target = DummySprite(self._state.player.rect.copy())
        self.player_controls = self._state.player.controls

        self.display_surface = pygame.display.get_surface()

        self.overlay = _CowHerdingOverlay()
        self.scoreboard = _CowHerdingScoreboard(self.finish)
        opponent_study_group = (
            StudyGroup.OUTGROUP
            if self._state.player.study_group == StudyGroup.INGROUP
            else StudyGroup.INGROUP
        )
        opponent = NPC(
            pos=(0, 0),
            assets=ENTITY_ASSETS.RABBIT,
            groups=(self._state.all_sprites, self._state.collision_sprites),
            collision_sprites=self._state.collision_sprites,
            study_group=opponent_study_group,
            apply_tool=lambda _, __, ___: None,
            plant_collision=lambda _: None,
            soil_manager=self._state.game_map.soil_manager,
            emote_manager=self._state.game_map.npc_emote_manager,
            tree_sprites=pygame.sprite.Group(),
            sickness_allowed=self.round_config.get("sickness", False),
            has_hat=False,
            has_necklace=False,
            special_features=None,
        )
        opponent.probability_to_get_sick = 1
        self._state.game_map.npcs.append(opponent)
        side_map = {StudyGroup.INGROUP: "L", StudyGroup.OUTGROUP: "R"}

        self._player_side = CowHerdingSideState(
            side_map[self._state.player.study_group], self._state.player
        )
        self._opponent_side = CowHerdingSideState(
            side_map[opponent_study_group], opponent
        )
        script_group = {StudyGroup.INGROUP: "ingroup", StudyGroup.OUTGROUP: "outgroup"}

        script_path = resource_path(
            "data/npc_scripted_paths/cow_herding/"
            + script_group[opponent_study_group]
            + "/"
        )

        self._opponent_side_script = CowHerdingScriptedPath.from_file(
            random.choice(glob.glob(glob.escape(script_path) + "*.json"))
        )

        self._ani_cd_start = 5
        self._ani_cd_ready_up_dur = 2
        self._ani_cd_dur = 3
        self._game_start = (
            self._ani_cd_start + self._ani_cd_ready_up_dur + self._ani_cd_dur
        )

        self._minigame_time = 0
        self._complete = False

        self._setup()

    @property
    def _complete(self):
        return self.__finished

    @_complete.setter
    def _complete(self, value: bool):
        if value:
            self._state.player.blocked = True
            self._state.player.direction.update((0, 0))
            if self._minigame_time < self._opponent_side_script.total_time:
                self._state.player.money += 200
            elif self._state.player.money > 200:
                self._state.player.money -= 200
            else:
                self._state.player.money = 0  # make sure we do not go below 0
            self.scoreboard.setup(
                self._minigame_time,
                self._player_side.cows_herded_in,
                self._opponent_side_script.total_time,
            )
        else:
            self._state.player.blocked = False

        self.__finished = value

    def _side_from_string(self, s: str):
        if s.startswith(self._player_side.prefix):
            return self._player_side
        else:
            return self._opponent_side

    def _setup(self):
        self.contestant_collision_sprites = self._state.collision_sprites.copy()

        if AIData.Matrix is None:
            raise MinigameSetupError("AI Pathfinding Matrix is not defined")

        barn_matrix = [row.copy() for row in AIData.Matrix]
        range_matrix = [row.copy() for row in AIData.Matrix]

        colliders = {}
        for obj in self._state.game_map.minigame_layer:
            pos = (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR)
            if "COW" in obj.name:
                cow = Cow(
                    pos=pos,
                    assets=ENTITY_ASSETS.COW,
                    groups=(self._state.all_sprites, self._state.collision_sprites),
                    collision_sprites=self._state.collision_sprites,
                )
                self._state.game_map.animals.append(cow)
                cow.conditional_behaviour_tree = CowHerdingBehaviourTree.WanderRange

                side = self._side_from_string(obj.name)
                side.cows[obj.id] = cow
                side.initial_positions[obj.id] = pos

            elif "SPAWN" in obj.name:
                side = self._side_from_string(obj.name)
                side.contestant.teleport(pos)
                if side == self._opponent_side:
                    self._opponent_id = obj.id
            else:
                colliders[obj.name] = obj

        for side_prefix in (self._player_side.prefix, self._opponent_side.prefix):
            obj = colliders[side_prefix + "_RANGE"]
            pf_add_matrix_collision(
                barn_matrix, (obj.x, obj.y), (obj.width, obj.height)
            )

            obj = colliders[side_prefix + "_BARN_AREA"]
            pf_add_matrix_collision(
                range_matrix, (obj.x, obj.y), (obj.width, obj.height)
            )

            obj = colliders[side_prefix + "_BARN_ENTRANCE"]
            pf_add_matrix_collision(
                range_matrix, (obj.x, obj.y), (obj.width, obj.height)
            )

            pos = (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR)
            size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
            image = pygame.Surface(size)

            side = self._side_from_string(side_prefix)
            side.barn_entrance_collider = Sprite(pos, image, name=obj.name)
            side.barn_entrance_collider.add(self.contestant_collision_sprites)

        CowHerdingContext.default_grid = AIData.Grid
        CowHerdingContext.barn_grid = Grid(matrix=barn_matrix)
        CowHerdingContext.range_grid = Grid(matrix=range_matrix)

    def start(self):
        super().start()

        for side in (self._player_side, self._opponent_side):
            side.cows_herded_in = 0
        self._minigame_time = 0
        self._complete = False

        # prepare player for minigame
        _set_player_controls(self.player_controls, True)
        self._state.player.facing_direction = Direction.UP
        self._state.player.blocked = True
        self._state.player.direction.update((0, 0))
        self._state.player.collision_sprites = self.contestant_collision_sprites

        self._state.overlay.visible = False

    def finish(self):
        _set_player_controls(self.player_controls, False)
        self._state.player.blocked = False
        self._state.player.collision_sprites = self._state.collision_sprites

        self._state.overlay.visible = True

        # check if the player achieved task "go to the minigame area and play"
        self._state.player.minigame_finished = True

        super().finish()

    def check_cows(self):
        for side in (self._player_side, self._opponent_side):
            for cow in side.cows.values():
                if side == self._player_side:
                    if cow.continuous_behaviour_tree is None:
                        continue
                elif side == self._opponent_side:
                    if cow.conditional_behaviour_tree is not None:
                        continue
                if cow.hitbox_rect.colliderect(side.barn_entrance_collider.rect):
                    cow.conditional_behaviour_tree = CowHerdingBehaviourTree.WanderBarn
                    cow.continuous_behaviour_tree = None
                    side.cows_herded_in += 1
                    if side == self._player_side:
                        self._state.sounds["success"].play()

    def handle_event(self, event: pygame.Event) -> bool:
        if self._complete:
            return self.scoreboard.handle_event(event)
        else:
            return False

    def update(self, dt: float):
        super().update(dt)
        if self._state.player.study_group == StudyGroup.INGROUP:
            offset = 300
        else:
            offset = -150
        self.camera_target.rect = self._state.player.rect.move(offset, 0)

        if not self._complete:
            self._minigame_time = self._ctime - self._game_start

            if self._game_start < self._ctime:
                self.check_cows()
                if self._player_side.finished:
                    self._complete = True
        else:
            self.scoreboard.update(dt)

        # FIXME: Since map transitions / menus also access player.blocked, this is
        #  needed to make sure that the player remains blocked during the entire
        #  cutscene.
        #  This should not be a permanent solution, since currently the Player can still
        #  move by a tiny bit on the frame they get unblocked from somewhere else.
        if self._ctime < self._game_start:
            self._state.player.blocked = True
            self._state.player.direction.update((0, 0))

        if int(self._ctime - dt) != int(self._ctime):
            # Countdown starts, preparing minigame
            if int(self._ctime) == self._ani_cd_start:
                for side in (self._player_side, self._opponent_side):
                    for eid, cow in side.cows.items():
                        cow.teleport(side.initial_positions[eid])
                        cow.conditional_behaviour_tree = None
                        cow.abort_path()

            # Countdown counting
            if int(self._ctime) in (
                self._ani_cd_start + self._ani_cd_ready_up_dur + i
                for i in range(self._ani_cd_dur)
            ):
                self._state.sounds["countdown_count"].play()

            # Countdown finished, minigame starts
            elif int(self._ctime) == self._game_start:
                self._state.player.blocked = False
                self._state.sounds["countdown_end"].play()
                for cow in self._player_side.cows.values():
                    cow.conditional_behaviour_tree = CowHerdingBehaviourTree.WanderRange
                    cow.continuous_behaviour_tree = CowHerdingBehaviourTree.Flee
                for eid, cow in self._opponent_side.cows.items():
                    cow_script = self._opponent_side_script.paths[eid]
                    cow.teleport(cow_script.start_pos)
                    cow.run_script(cow_script)
                opponent_script = self._opponent_side_script.paths[self._opponent_id]
                self._opponent_side.contestant.teleport(opponent_script.start_pos)
                self._opponent_side.contestant.run_script(opponent_script)

    def draw(self):
        if self._ctime <= self._ani_cd_start:
            self.overlay.draw_description()
        else:
            self.overlay.draw_objective(
                self._player_side.cows_total,
                self._player_side.cows_herded_in,
                self._opponent_side.cows_total,
                self._opponent_side.cows_herded_in,
            )

        if self._ani_cd_start < self._ctime < self._game_start + 1:
            self.overlay.draw_countdown(
                self._ctime - self._ani_cd_start,
                self._ani_cd_ready_up_dur,
                self._ani_cd_dur,
            )

        self.overlay.draw_timer(self._minigame_time)

        if self._complete:
            self.scoreboard.draw()
