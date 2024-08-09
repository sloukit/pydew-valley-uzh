from collections.abc import Callable
from dataclasses import dataclass
from typing import Type

import pygame
import pygame.gfxdraw
from pathfinding.core.grid import Grid

from src.controls import Controls
from src.enums import Direction
from src.groups import PersistentSpriteGroup
from src.npc.cow import Cow
from src.npc.setup import AIData
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
from src.support import add_pf_matrix_collision, import_font


@dataclass
class CowHerdingState(MinigameState):
    all_sprites: PersistentSpriteGroup
    collision_sprites: PersistentSpriteGroup
    player: Player
    game_map: GameMap
    overlay: Overlay
    get_camera_center: Callable[[], pygame.Vector2 | tuple[float, float]]
    sounds: SoundDict


class CowHerding(Minigame):
    _state: CowHerdingState
    player_controls: Type[Controls]

    def __init__(self, state: CowHerdingState):
        super().__init__(state)

        self.player_controls = self._state.player.controls

        self.display_surface = pygame.display.get_surface()
        self.font_countdown = import_font(128, "font/LycheeSoda.ttf")

        self.overlay = _CowHerdingOverlay()
        self.scoreboard = _CowHerdingScoreboard(self.finish)

        self._ani_countdown_start = 5

        self._cows = []
        self._cows_original_positions = []
        self._cows_total = 0
        self._cows_herded_in = 0

        self._minigame_time = 0
        self._finished = False

        self._setup()

    @property
    def _finished(self):
        return self.__finished

    @_finished.setter
    def _finished(self, value: bool):
        if value:
            self._state.player.blocked = True
            self._state.player.direction.update((0, 0))
            self.scoreboard.setup(self._minigame_time, self._cows_herded_in)
        else:
            self._state.player.blocked = False

        self.__finished = value

    def _setup(self):
        self.player_collision_sprites = self._state.collision_sprites.copy()

        self.barn_entrance_collider = None

        barn_matrix = [row.copy() for row in AIData.Matrix]
        range_matrix = [row.copy() for row in AIData.Matrix]

        colliders = {}
        cows = []
        for i in self._state.game_map.minigame_layer:
            if i.name == "L_COW":
                cows.append(i)
            else:
                colliders[i.name] = i

        obj = colliders["L_RANGE"]
        add_pf_matrix_collision(barn_matrix, (obj.x, obj.y), (obj.width, obj.height))

        obj = colliders["L_BARN_ENTRANCE"]
        add_pf_matrix_collision(range_matrix, (obj.x, obj.y), (obj.width, obj.height))
        pos = (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR)
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        self.barn_entrance_collider = Sprite(pos, image, name=obj.name)
        self.barn_entrance_collider.add(self.player_collision_sprites)

        obj = colliders["L_BARN_AREA"]
        add_pf_matrix_collision(range_matrix, (obj.x, obj.y), (obj.width, obj.height))

        CowHerdingContext.default_grid = AIData.Grid
        CowHerdingContext.barn_grid = Grid(matrix=barn_matrix)
        CowHerdingContext.range_grid = Grid(matrix=range_matrix)

        for obj in cows:
            pos = (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR)
            cow = Cow(
                pos=pos,
                assets=ENTITY_ASSETS.COW,
                groups=(self._state.all_sprites, self._state.collision_sprites),
                collision_sprites=self._state.collision_sprites,
            )
            cow.conditional_behaviour_tree = CowHerdingBehaviourTree.WanderRange
            self._cows.append(cow)
            self._cows_original_positions.append(pos)

        self._cows_total = len(self._cows)

    def start(self):
        super().start()

        _set_player_controls(self.player_controls, True)
        self._state.player.facing_direction = Direction.UP
        self._state.player.blocked = True
        self._state.player.direction.update((0, 0))
        self._state.player.collision_sprites = self.player_collision_sprites

        self._state.overlay.visible = False

    def finish(self):
        super().finish()
        _set_player_controls(self.player_controls, False)
        self._state.player.blocked = False
        self._state.overlay.visible = True
        self._state.player.collision_sprites = self._state.collision_sprites

    def check_cows(self):
        cows_herded_in = []
        for cow in self._cows:
            if cow.hitbox_rect.colliderect(self.barn_entrance_collider.rect):
                cow.conditional_behaviour_tree = CowHerdingBehaviourTree.WanderBarn
                cow.continuous_behaviour_tree = None
                cows_herded_in.append(cow)
                self._state.sounds["success"].play()

        for cow in cows_herded_in:
            self._cows.remove(cow)
            self._cows_herded_in += 1

    def handle_event(self, event: pygame.Event):
        if self._finished:
            return self.scoreboard.handle_event(event)
        else:
            return False

    def update(self, dt: float):
        super().update(dt)

        if not self._finished:
            self._minigame_time = self._ctime - (self._ani_countdown_start + 3)

            if (self._ani_countdown_start + 3) < self._ctime:
                self.check_cows()
                if self._cows_total == self._cows_herded_in:
                    self._finished = True
        else:
            self.scoreboard.update(dt)

        # FIXME: Since map transitions / menus also access player.blocked, this is
        #  needed to make sure that the player remains blocked during the entire
        #  cutscene.
        #  This should not be a permanent solution, since currently the Player can still
        #  move by a tiny bit on the frame they get unblocked from somewhere else.
        if self._ctime < self._ani_countdown_start + 3:
            self._state.player.blocked = True
            self._state.player.direction.update((0, 0))

        if int(self._ctime - dt) != int(self._ctime):
            # Countdown starts, preparing minigame
            if int(self._ctime) == self._ani_countdown_start:
                for i in range(len(self._cows)):
                    self._cows[i].teleport(self._cows_original_positions[i])
                    self._cows[i].conditional_behaviour_tree = None
                    self._cows[i].abort_path()

            # Countdown counting
            if int(self._ctime) in [self._ani_countdown_start + i for i in range(3)]:
                self._state.sounds["countdown_count"].play()

            # Countdown finished, minigame starts
            elif int(self._ctime) == self._ani_countdown_start + 3:
                self._state.player.blocked = False
                self._state.sounds["countdown_end"].play()
                for cow in self._cows:
                    cow.conditional_behaviour_tree = CowHerdingBehaviourTree.WanderRange
                    cow.continuous_behaviour_tree = CowHerdingBehaviourTree.Flee

    def draw(self):
        if self._ctime <= self._ani_countdown_start:
            self.overlay.draw_description()
        else:
            self.overlay.draw_objective(self._cows_total, self._cows_herded_in)

        if self._ani_countdown_start < self._ctime < self._ani_countdown_start + 4:
            self.overlay.draw_countdown(self._minigame_time)

        self.overlay.draw_timer(self._minigame_time)

        if self._finished:
            self.scoreboard.draw()


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
    controls.SHOW_DIALOG.disabled = value
    controls.ADVANCE_DIALOG.disabled = value
