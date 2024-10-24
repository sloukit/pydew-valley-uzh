from dataclasses import dataclass
from typing import Type

import pygame
import pygame.gfxdraw
from pathfinding.core.grid import Grid

from src.controls import Controls
from src.enums import Direction
from src.exceptions import MinigameSetupError
from src.groups import PersistentSpriteGroup
from src.npc.behaviour.cow_behaviour_tree import CowConditionalBehaviourTree
from src.npc.cow import Cow
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
class CowHerdingState(MinigameState):
    game_map: GameMap
    player: Player
    all_sprites: PersistentSpriteGroup
    collision_sprites: PersistentSpriteGroup
    overlay: Overlay
    sounds: SoundDict


class CowHerding(Minigame):
    _state: CowHerdingState
    player_controls: Type[Controls]

    display_surface: pygame.Surface

    overlay: _CowHerdingOverlay

    scoreboard: _CowHerdingScoreboard

    # seconds until the countdown starts
    _ani_cd_start: int
    _ani_cd_ready_up_dur: int
    _ani_cd_dur: int
    _game_start: int

    _cows: list[Cow]
    _cows_initial_positions: list[tuple[int, int]]
    _cows_total: int
    _cows_herded_in: int

    # current minigame time (as seen on the minigame timer)
    _minigame_time: int

    # whether the Player has completed the minigame yet
    _complete: bool

    barn_entrance_collider: Sprite
    player_collision_sprites: PersistentSpriteGroup

    def __init__(self, state: CowHerdingState):
        super().__init__(state)

        self.player_controls = self._state.player.controls

        self.display_surface = pygame.display.get_surface()

        self.overlay = _CowHerdingOverlay()
        self.scoreboard = _CowHerdingScoreboard(self.finish)

        self._ani_cd_start = 5
        self._ani_cd_ready_up_dur = 2
        self._ani_cd_dur = 3
        self._game_start = (
            self._ani_cd_start + self._ani_cd_ready_up_dur + self._ani_cd_dur
        )

        self._cows = []
        self._cows_initial_positions = []
        self._cows_total = 0
        self._cows_herded_in = 0

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
            self.scoreboard.setup(self._minigame_time, self._cows_herded_in)
        else:
            self._state.player.blocked = False

        self.__finished = value

    def _setup(self):
        self.player_collision_sprites = self._state.collision_sprites.copy()

        if AIData.Matrix is None:
            raise MinigameSetupError("AI Pathfinding Matrix is not defined")

        barn_matrix = [row.copy() for row in AIData.Matrix]
        range_matrix = [row.copy() for row in AIData.Matrix]

        colliders = {}
        for obj in self._state.game_map.minigame_layer:
            if "COW" in obj.name:
                pos = (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR)
                cow = Cow(
                    pos=pos,
                    assets=ENTITY_ASSETS.COW,
                    groups=(self._state.all_sprites, self._state.collision_sprites),
                    collision_sprites=self._state.collision_sprites,
                )
                self._state.game_map.animals.append(cow)
                if obj.name == "L_COW":
                    cow.conditional_behaviour_tree = CowHerdingBehaviourTree.WanderRange
                    self._cows.append(cow)
                    self._cows_initial_positions.append(pos)
                elif obj.name == "R_COW":
                    cow.conditional_behaviour_tree = CowConditionalBehaviourTree.Wander
            else:
                colliders[obj.name] = obj

        obj = colliders["L_RANGE"]
        pf_add_matrix_collision(barn_matrix, (obj.x, obj.y), (obj.width, obj.height))

        obj = colliders["L_BARN_ENTRANCE"]
        pf_add_matrix_collision(range_matrix, (obj.x, obj.y), (obj.width, obj.height))

        pos = (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR)
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        self.barn_entrance_collider = Sprite(pos, image, name=obj.name)
        self.barn_entrance_collider.add(self.player_collision_sprites)

        obj = colliders["L_BARN_AREA"]
        pf_add_matrix_collision(range_matrix, (obj.x, obj.y), (obj.width, obj.height))

        CowHerdingContext.default_grid = AIData.Grid
        CowHerdingContext.barn_grid = Grid(matrix=barn_matrix)
        CowHerdingContext.range_grid = Grid(matrix=range_matrix)

        self._cows_total = len(self._cows)

    def start(self):
        super().start()

        self._cows_herded_in = 0
        self._minigame_time = 0
        self._complete = False

        # prepare player for minigame
        _set_player_controls(self.player_controls, True)
        self._state.player.facing_direction = Direction.UP
        self._state.player.blocked = True
        self._state.player.direction.update((0, 0))
        self._state.player.collision_sprites = self.player_collision_sprites

        self._state.overlay.visible = False

    def finish(self):
        _set_player_controls(self.player_controls, False)
        self._state.player.blocked = False
        self._state.player.collision_sprites = self._state.collision_sprites

        self._state.overlay.visible = True

        super().finish()

    def check_cows(self):
        for cow in self._cows:
            if cow.continuous_behaviour_tree is None:
                continue
            if cow.hitbox_rect.colliderect(self.barn_entrance_collider.rect):
                cow.conditional_behaviour_tree = CowHerdingBehaviourTree.WanderBarn
                cow.continuous_behaviour_tree = None
                self._state.sounds["success"].play()
                self._cows_herded_in += 1

    def handle_event(self, event: pygame.Event):
        if self._complete:
            return self.scoreboard.handle_event(event)
        else:
            return False

    def update(self, dt: float):
        super().update(dt)

        if not self._complete:
            self._minigame_time = self._ctime - self._game_start

            if self._game_start < self._ctime:
                self.check_cows()
                if self._cows_total == self._cows_herded_in:
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
                for i in range(len(self._cows)):
                    self._cows[i].teleport(self._cows_initial_positions[i])
                    self._cows[i].conditional_behaviour_tree = None
                    self._cows[i].abort_path()

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
                for cow in self._cows:
                    cow.conditional_behaviour_tree = CowHerdingBehaviourTree.WanderRange
                    cow.continuous_behaviour_tree = CowHerdingBehaviourTree.Flee

    def draw(self):
        if self._ctime <= self._ani_cd_start:
            self.overlay.draw_description()
        else:
            self.overlay.draw_objective(self._cows_total, self._cows_herded_in)

        if self._ani_cd_start < self._ctime < self._game_start + 1:
            self.overlay.draw_countdown(
                self._ctime - self._ani_cd_start,
                self._ani_cd_ready_up_dur,
                self._ani_cd_dur,
            )

        self.overlay.draw_timer(self._minigame_time)

        if self._complete:
            self.scoreboard.draw()
