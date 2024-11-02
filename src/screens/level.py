import copy
import random
import time
import warnings
from collections.abc import Callable
from functools import partial
from typing import cast

import pygame

from src.camera import Camera
from src.camera.camera_target import CameraTarget
from src.camera.quaker import Quaker
from src.camera.zoom_manager import ZoomManager
from src.controls import Controls
from src.enums import FarmingTool, GameState, Map, ScriptedSequenceType, StudyGroup
from src.events import DIALOG_ADVANCE, DIALOG_SHOW, START_QUAKE, post_event
from src.exceptions import GameMapWarning
from src.groups import AllSprites, PersistentSpriteGroup
from src.gui.interface.emotes import NPCEmoteManager, PlayerEmoteManager
from src.gui.scene_animation import SceneAnimation
from src.npc.npc import NPC
from src.npc.setup import AIData
from src.overlay.game_time import GameTime
from src.overlay.overlay import Overlay
from src.overlay.sky import Rain, Sky
from src.overlay.soil import SoilManager
from src.overlay.transition import Transition
from src.savefile import SaveFile
from src.screens.game_map import GameMap
from src.screens.minigames.base import Minigame
from src.screens.minigames.cow_herding import CowHerding, CowHerdingState
from src.settings import (
    DEFAULT_ANIMATION_NAME,
    EMOTES_LIST,
    GAME_MAP,
    HEALTH_DECAY_VALUE,
    SCALED_TILE_SIZE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TOMATO_OR_CORN_LIST,
    MapDict,
    SoundDict,
)
from src.sprites.base import Sprite
from src.sprites.entities.character import Character
from src.sprites.entities.player import Player
from src.sprites.particle import ParticleSprite
from src.sprites.setup import ENTITY_ASSETS
from src.support import load_data, map_coords_to_tile, resource_path, save_data

_TO_PLAYER_SPEED_INCREASE_THRESHOLD = 200


class Level:
    display_surface: pygame.Surface
    switch_screen: Callable[[GameState], None]

    # assets
    font: pygame.Font
    frames: dict
    sounds: SoundDict
    tmx_maps: MapDict
    current_map: Map | None
    game_map: GameMap | None
    save_file: SaveFile

    current_minigame: Minigame | None

    # sprite groups
    all_sprites: AllSprites
    collision_sprites: PersistentSpriteGroup
    tree_sprites: PersistentSpriteGroup
    bush_sprites: PersistentSpriteGroup
    interaction_sprites: PersistentSpriteGroup
    drop_sprites: pygame.sprite.Group
    player_exit_warps: pygame.sprite.Group

    # farming
    soil_manager: SoilManager

    # emotes
    _emotes: dict
    player_emote_manager: PlayerEmoteManager
    backup_emote_mgr: PlayerEmoteManager
    npc_emote_manager: NPCEmoteManager

    player: Player
    prev_player_pos: tuple[int, int]
    # weather
    sky: Sky
    rain: Rain
    raining: bool

    # transitions
    map_transition: Transition
    day_transition: Transition
    current_day: int

    # overlay
    overlay: Overlay
    show_hitbox_active: bool

    intro_shown: dict[str, bool]

    def __init__(
        self,
        switch: Callable[[GameState], None],
        get_set_round: tuple[Callable[[], int], Callable[[int], []]],
        tmx_maps: MapDict,
        frames: dict[str, dict],
        sounds: SoundDict,
        save_file: SaveFile,
        clock: pygame.time.Clock,
    ):
        # main setup
        self.display_surface = pygame.display.get_surface()
        self.switch_screen = switch
        self.save_file = save_file

        # cutscene
        # target_points = [(100, 100), (200, 200), (300, 100), (800, 900)]
        # speeds = [100, 150, 200]  # Different speeds for each segment
        # pauses = [0, 1, 0.5, 2]  # Pauses at each point in seconds
        self.cutscene_animation = SceneAnimation([CameraTarget.get_null_target()])
        self.intro_shown = {}

        self.zoom_manager = ZoomManager()

        # assets
        self.font = pygame.font.Font(resource_path("font/LycheeSoda.ttf"), 30)
        self.frames = frames
        self.sounds = sounds
        self.tmx_maps = tmx_maps
        self.current_map = None
        self.game_map = None

        self.all_sprites = AllSprites()
        self.collision_sprites = PersistentSpriteGroup()
        self.tree_sprites = PersistentSpriteGroup()
        self.bush_sprites = PersistentSpriteGroup()
        self.interaction_sprites = PersistentSpriteGroup()
        self.drop_sprites = pygame.sprite.Group()
        self.player_exit_warps = pygame.sprite.Group()

        self.camera = Camera(0, 0)
        self.quaker = Quaker(self.camera)

        self.soil_manager = SoilManager(self.all_sprites, self.frames["level"])

        self._emotes = self.frames["emotes"]
        # add additional sprites for scripted sequence "decide_tomato_or_corn"
        # extra sprites are fine, which sprites are actually shown on the wheel depends on emote_list param
        for frame in TOMATO_OR_CORN_LIST:
            self._emotes[frame] = [self.frames["items"][frame]]

        self.player_emote_manager = PlayerEmoteManager(
            self._emotes, EMOTES_LIST, self.all_sprites
        )
        self.backup_emote_mgr = self.player_emote_manager
        self.npc_emote_manager = NPCEmoteManager(self._emotes, self.all_sprites)

        self.controls = Controls

        self.player = Player(
            pos=(0, 0),
            assets=copy.deepcopy(ENTITY_ASSETS.RABBIT),
            groups=(),
            collision_sprites=self.collision_sprites,
            controls=self.controls,
            apply_tool=self.apply_tool,
            plant_collision=self.plant_collision,
            interact=self.interact,
            emote_manager=self.player_emote_manager,
            sounds=self.sounds,
            hp=0,
            bathstat=False,
            bath_time=0,
            save_file=self.save_file,
        )
        self.prev_player_pos = (0, 0)
        self.all_sprites.add_persistent(self.player)
        self.collision_sprites.add_persistent(self.player)

        # weather
        self.game_time = GameTime()
        self.sky = Sky(self.game_time)
        self.rain = Rain(self.all_sprites, self.frames["level"])
        self.raining = False

        self.activate_music()

        # day night cycle
        self.day_transition = Transition(self.reset, self.finish_transition, dur=3200)
        self.current_day = 0

        # overlays
        self.overlay = Overlay(self.player, frames["items"], self.game_time, clock)
        self.show_hitbox_active = False
        self.show_pf_overlay = False
        self.setup_pf_overlay()

        # minigame
        self.current_minigame = None

        # switch to outgroup farm
        self.outgroup_farm_entered = False
        self.outgroup_farm_time_entered = None
        self.outgroup_message_received = False
        self.start_become_outgroup = False
        self.start_become_outgroup_time = None
        self.finish_become_outgroup = False

        # map
        self.load_map(GAME_MAP)
        self.map_transition = Transition(
            lambda: self.switch_to_map(self.current_map),
            self.finish_transition,
            dur=2400,
        )

        # level interactions
        self.get_round = get_set_round[0]
        self.set_round = get_set_round[1]

        # watch the player behaviour in achieving tutorial tasks
        self.tile_farmed = False
        self.crop_planted : set = set()
        self.crop_watered = False
        self.hit_tree = False

    def load_map(self, game_map: Map, from_map: str = None):
        # prepare level state for new map
        # clear all sprite groups
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.interaction_sprites.empty()
        self.tree_sprites.empty()
        self.bush_sprites.empty()
        self.player_exit_warps.empty()

        # clear existing soil_layer (not done due to the fact we need to keep hoed tiles in memory)
        # self.soil_layer.reset()
        self.quaker.reset()

        self.game_map = GameMap(
            selected_map=game_map,
            tilemap=self.tmx_maps[game_map],
            scene_ani=self.cutscene_animation,
            zoom_man=self.zoom_manager,
            all_sprites=self.all_sprites,
            collision_sprites=self.collision_sprites,
            interaction_sprites=self.interaction_sprites,
            tree_sprites=self.tree_sprites,
            bush_sprites=self.bush_sprites,
            player_exit_warps=self.player_exit_warps,
            player=self.player,
            player_emote_manager=self.player_emote_manager,
            npc_emote_manager=self.npc_emote_manager,
            soil_manager=self.soil_manager,
            apply_tool=self.apply_tool,
            plant_collision=self.plant_collision,
            frames=self.frames,
            save_file=self.save_file,
        )

        self.camera.change_size(*self.game_map.size)

        player_spawn = None

        # search for player entry warp depending on which map they came from
        if from_map and not game_map == Map.MINIGAME:
            player_spawn = self.game_map.player_entry_warps.get(from_map)
            if not player_spawn:
                warnings.warn(
                    f'No valid entry warp found for "{game_map}" '
                    f'from: "{self.current_map}"',
                    GameMapWarning,
                )

        # use default spawnpoint if no origin map is specified,
        # or if no entry warp for the player's origin map is found
        if not player_spawn:
            if self.game_map.player_spawnpoint:
                player_spawn = self.game_map.player_spawnpoint
            else:
                warnings.warn(
                    f"No default spawnpoint found on {game_map}", GameMapWarning
                )
                # fallback to the first player entry warp
                player_spawn = next(iter(self.game_map.player_entry_warps.values()))

        self.player.teleport(player_spawn)

        if self.cutscene_animation.has_animation_name(DEFAULT_ANIMATION_NAME):
            def_animation_targets = self.cutscene_animation.animations[
                DEFAULT_ANIMATION_NAME
            ]
            last_target = def_animation_targets[-1]
            last_targ_pos = pygame.Vector2(last_target.pos)
            center = pygame.Vector2(self.player.rect.center)
            movement = center - last_targ_pos
            speed = (
                max(round(movement.length()) // _TO_PLAYER_SPEED_INCREASE_THRESHOLD, 2)
                * 100
            )
            def_animation_targets.append(
                CameraTarget(self.player.rect.center, len(def_animation_targets), speed)
            )

            self.cutscene_animation.set_current_animation(DEFAULT_ANIMATION_NAME)
        self.rain.set_floor_size(self.game_map.get_size())

        self.current_map = game_map

        # show intro scripted sequence only once
        if not self.intro_shown.get(game_map, False):
            self.intro_shown[game_map] = True
            self.cutscene_animation.start()

        if game_map == Map.MINIGAME:
            self.current_minigame = CowHerding(
                CowHerdingState(
                    game_map=self.game_map,
                    player=self.player,
                    all_sprites=self.all_sprites,
                    collision_sprites=self.collision_sprites,
                    overlay=self.overlay,
                    sounds=self.sounds,
                )
            )

            @self.current_minigame.on_finish
            def on_finish():
                self.current_minigame = None
                self.map_transition.reset = partial(self.switch_to_map, Map.TOWN)
                self.start_map_transition()

            self.current_minigame.start()

    def activate_music(self):
        volume = 0.1
        try:
            sound_data = load_data("volume.json")
        except FileNotFoundError:
            sound_data = {
                "music": 50,
                "sfx": 50,
            }
            save_data(sound_data, "volume.json")
        volume = sound_data["music"]
        # sfx = sound_data['sfx']
        self.sounds["music"].set_volume(min((volume / 1000), 0.4))
        self.sounds["music"].play(-1)

    # plant collision
    def plant_collision(self, character: Character):
        area = self.soil_manager.get_area(character.study_group)
        if area.plant_sprites:
            for plant in area.plant_sprites:
                if plant.hitbox_rect.colliderect(character.hitbox_rect):
                    x, y = map_coords_to_tile(plant.hitbox_rect.midbottom)
                    area.harvest((x, y), character.add_resource, self.create_particle)

    def switch_to_map(self, map_name: Map):
        if self.tmx_maps.get(map_name):
            self.load_map(map_name, from_map=self.current_map)
        else:
            if map_name == "bathhouse" and self.player.hp < 80:
                self.overlay.health_bar.apply_health(9999999)
                self.player.bathstat = True
                self.player.bath_time = time.time()
                self.player.emote_manager.show_emote(self.player, "sad_ani")
                self.load_map(self.current_map, from_map=map_name)
            elif map_name == "bathhouse":
                # this is to prevent warning in the console
                self.load_map(self.current_map, from_map=map_name)
                self.player.emote_manager.show_emote(self.player, "sad_ani")
            else:
                warnings.warn(f'Error loading map: Map "{map_name}" not found')

                # fallback which reloads the current map and sets the player to the
                # entry warp of the map that should have been switched to
                self.load_map(self.current_map, from_map=map_name)

    def create_particle(self, sprite: pygame.sprite.Sprite):
        ParticleSprite(sprite.rect.topleft, sprite.image, self.all_sprites)

    def _play_playeronly_sound(self, sound: str, entity: Character):
        if isinstance(entity, Player):
            self.sounds[sound].play()

    def apply_tool(self, tool: FarmingTool, pos: tuple[int, int], character: Character):
        match tool:
            case FarmingTool.AXE:
                for tree in pygame.sprite.spritecollide(
                    character,
                    self.tree_sprites,
                    False,
                    lambda spr, tree_spr: spr.axe_hitbox.colliderect(
                        tree_spr.hitbox_rect
                    ),
                ):
                    tree.hit(character)

                    # check if player achieved task "go to the forest and hit a tree"
                    if isinstance(character, Player):
                        self.hit_tree = True

                    self._play_playeronly_sound("axe", character)
            case FarmingTool.HOE:
                if self.soil_manager.hoe(character, pos):
                    self._play_playeronly_sound("hoe", character)
                    
                    # check if the player achieved task "farm with your hoe"
                    if isinstance(character, Player):
                            self.tile_farmed = True
            case FarmingTool.WATERING_CAN:
                if self.soil_manager.water(character, pos) :
                    # check if the player achieved task "water the crop"
                    if isinstance(character, Player) and True in self.crop_planted and pos in self.crop_planted:
                        self.crop_watered = True

                self._play_playeronly_sound("water", character)
            case _:  # All seeds
                if self.soil_manager.plant(
                    character, pos, tool, character.remove_resource
                ):
                    self._play_playeronly_sound("plant", character)

                    # check if the player achieved task "plant a crop"
                    if isinstance(character, Player):
                        self.crop_planted.add(True)
                        self.crop_planted.add(pos)
                else:
                    self._play_playeronly_sound("cant_plant", character)

    def interact(self):
        collided_interactions = pygame.sprite.spritecollide(
            self.player, self.interaction_sprites, False
        )
        if collided_interactions:
            if collided_interactions[0].name == "Bed":
                self.start_day_transition()
            if collided_interactions[0].name == "sign":
                self.show_sign(collided_interactions[0])
            if collided_interactions[0].name == "Trader":
                self.switch_screen(GameState.SHOP)
            if collided_interactions[0] in self.bush_sprites.sprites():
                if self.player.axe_hitbox.colliderect(
                    collided_interactions[0].hitbox_rect
                ):
                    collided_interactions[0].hit(self.player)

    def show_sign(self, sign: Sprite) -> None:
        label_key = sign.custom_properties.get("label", "label_not_available")
        post_event(DIALOG_SHOW, dial=label_key)

    def check_outgroup_logic(self):
        collided_with_outgroup_farm = pygame.sprite.spritecollide(
            self.player,
            [i for i in self.interaction_sprites if i.name == "Outgroup Farm"],
            False,
        )

        # Starts timer for 60 seconds when player is in outgroup farm
        if collided_with_outgroup_farm:
            if not self.outgroup_farm_entered:
                self.outgroup_farm_time_entered = pygame.time.get_ticks()
                self.outgroup_farm_entered = True

        # Resets the timer when player exits the farm
        else:
            self.outgroup_farm_entered = False
            self.outgroup_farm_time_entered = None
            self.outgroup_message_received = False

        # If the player is in the farm and 60 seconds (currently 30s) have passed
        if (
            self.outgroup_farm_entered
            and pygame.time.get_ticks() - self.outgroup_farm_time_entered >= 30000
        ):
            # Checks if player has already received the message and is not part of the outgroup
            if (
                not self.outgroup_message_received
                and self.player.study_group != StudyGroup.OUTGROUP
            ):
                self.outgroup_message_received = True
                self.switch_screen(GameState.OUTGROUP_MENU)

        # Resets so that message can be displayed again if player exits and reenters farm
        if not self.outgroup_farm_entered:
            self.outgroup_message_receieved = False

        # checks 60 seconds and 120 seconds after player joins outgroup to convert appearance
        if self.player.study_group == StudyGroup.OUTGROUP:
            if not self.start_become_outgroup:
                self.start_become_outgroup_time = pygame.time.get_ticks()
                self.start_become_outgroup = True
            elif self.finish_become_outgroup:
                pass
            elif pygame.time.get_ticks() - self.start_become_outgroup_time > 120000:
                self.player.has_outgroup_skin = True
                self.finish_become_outgroup = True
            elif pygame.time.get_ticks() - self.start_become_outgroup_time > 60000:
                self.player.has_horn = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.current_minigame and self.current_minigame.running:
            if self.current_minigame.handle_event(event):
                return True

        if event.type == START_QUAKE:
            self.quaker.start(event.duration)
            if event.debug:
                self.set_round(7)
            return True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PAUSE)
                return True
            self.controls.update_control_state(event.key, True)
        elif event.type == pygame.KEYUP:
            self.controls.update_control_state(event.key, False)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.controls.update_control_state(event.button, True)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.controls.update_control_state(event.button, False)

        return False

    def handle_controls(self):
        if self.controls.ADVANCE_DIALOG.click:
            post_event(DIALOG_ADVANCE)

        if self.controls.DEBUG_QUAKE.click:
            post_event(START_QUAKE, duration=2.0, debug=True)

        if self.controls.DEBUG_PLAYER_TASK.click:
            self.switch_screen(GameState.PLAYER_TASK)

        if self.controls.DEBUG_END_ROUND.click:
            self.switch_screen(GameState.ROUND_END)

        if self.controls.DEBUG_PLAYER_RECEIVES_HAT.click:
            self.start_scripted_sequence(ScriptedSequenceType.PLAYER_RECEIVES_HAT)

        if self.controls.DEBUG_PLAYER_RECEIVES_NECKLACE.click:
            self.start_scripted_sequence(ScriptedSequenceType.PLAYER_RECEIVES_NECKLACE)

        if self.controls.DEBUG_PLAYERS_BIRTHDAY.click:
            self.start_scripted_sequence(ScriptedSequenceType.PLAYERS_BIRTHDAY)

        if self.controls.DEBUG_NPC_RECEIVES_NECKLACE.click:
            self.start_scripted_sequence(ScriptedSequenceType.NPC_RECEIVES_NECKLACE)

        if self.controls.DEBUG_DECIDE_TOMATO_OR_CORN.click:
            self.start_scripted_sequence(ScriptedSequenceType.DECIDE_TOMATO_OR_CORN)

        if self.controls.DEBUG_SHOW_HITBOXES.click:
            self.show_hitbox_active = not self.show_hitbox_active

        if self.controls.DEBUG_SHOW_PF_OVERLAY.click:
            self.show_pf_overlay = not self.show_pf_overlay

        if self.controls.DEBUG_SHOW_DIALOG.click:
            post_event(DIALOG_SHOW, dial="test")

    def start_scripted_sequence(self, sequence_type: ScriptedSequenceType):
        # do not start new scripted sequence when one is already running
        if self.cutscene_animation.active:
            return

        active_group = self.player.study_group
        if active_group == StudyGroup.INGROUP:
            animation_name = "ingroup_gathering"
        else:
            animation_name = "outgroup_gathering"

        if self.cutscene_animation.has_animation_name(animation_name):
            npcs: list[Player | NPC] = []
            if self.game_map:
                npcs = [
                    npc
                    for npc in self.game_map.npcs
                    if npc.study_group == active_group and not npc.is_dead
                ]
            if sequence_type == ScriptedSequenceType.NPC_RECEIVES_NECKLACE:
                npc_in_center = random.choice(npcs)
                npcs.remove(npc_in_center)
                npcs.append(self.player)
            else:
                npc_in_center = self.player
            self.cutscene_animation.set_current_animation(animation_name)
            self.cutscene_animation.is_end_condition_met = partial(
                self.end_scripted_sequence, sequence_type, npc_in_center
            )
            if self.player.rect:
                self.prev_player_pos = cast(
                    tuple[int, int], self.player.rect.center
                )  # else (0, 0)
            meeting_pos = self.cutscene_animation.targets[0].pos
            # move player other npc_in_center to the meeting point and make him face to the east (right)
            npc_in_center.teleport(meeting_pos)
            # npc_in_center.direction = pygame.Vector2(1, 0)
            npc_in_center.direction.update((1, 0))
            npc_in_center.get_facing_direction()
            npc_in_center.direction.update((0, 0))

            # spread all ingroup npc in half-circle of 2 * SCALED_TILE_SIZE diameter
            # from north to south clockwise or counterclockwise (depends on group)
            # and make them face the player in the center
            distance = pygame.Vector2(0, -2 * SCALED_TILE_SIZE)
            rot_by = (180) / (len(npcs) - 1)
            # the outgroup circle is layed out counterclockwise
            if active_group == StudyGroup.OUTGROUP:
                rot_by = -rot_by
            angle = 0.0

            for npc in npcs:
                new_pos = meeting_pos + distance.rotate(angle)
                npc.direction.update(-distance.rotate(angle))
                npc.get_facing_direction()
                npc.direction.update((0, 0))

                npc.teleport(new_pos)
                angle += rot_by
            self.cutscene_animation.reset()
            self.cutscene_animation.start()

            dialog_name = f"scripted_sequence_{sequence_type.value}"
            post_event(DIALOG_SHOW, dial=dialog_name)

    def end_scripted_sequence(
        self, sequence_type: ScriptedSequenceType, npc: NPC | Player
    ) -> bool:
        # prevent the scripted sequence from ending
        if self.player.blocked:
            return False

        if sequence_type == ScriptedSequenceType.PLAYER_RECEIVES_HAT:
            npc.has_hat = True
        elif sequence_type == ScriptedSequenceType.PLAYER_RECEIVES_NECKLACE:
            npc.has_necklace = True
        elif sequence_type == ScriptedSequenceType.PLAYERS_BIRTHDAY:
            pass
        elif sequence_type == ScriptedSequenceType.NPC_RECEIVES_NECKLACE:
            npc.has_necklace = True
        elif sequence_type == ScriptedSequenceType.DECIDE_TOMATO_OR_CORN:
            buy_list = TOMATO_OR_CORN_LIST
            self.end_scripted_sequence_decide(buy_list)
            return False

        self.scripted_sequence_cleanup()

        return True

    def end_scripted_sequence_decide(self, buy_list: list[str]) -> None:
        # just to make linter happy (game_map could be None)
        if not self.game_map:
            return

        if buy_list[0] not in self.player_emote_manager.emote_wheel._emotes:
            # check if emote was already displayed
            # store current EmoteManager
            self.backup_emote_mgr = self.player.emote_manager
            # create and assign new EmoteManager with only 2 options to select from
            self.player_emote_manager = PlayerEmoteManager(
                self._emotes, buy_list, self.all_sprites
            )
            self.player.emote_manager = self.player_emote_manager
            self.game_map.player_emote_manager = self.player_emote_manager
            self.game_map._setup_emote_interactions()
            # show EmoteWheel
            # self.player.blocked = True
            self.player_emote_manager.toggle_emote_wheel()
            # still block the Scripted Sequence from finishing, until user makes selection
        else:
            if self.player_emote_manager.emote_wheel.visible:
                # EmoteWheel is still displayed, waiting for his vote
                return
            else:
                # Player has voted
                # self.player.blocked = False
                total_votes = 1
                # how many Characters voted for the first option
                first_item_votes = 0
                players_vote = self.player_emote_manager.emote_wheel._current_emote
                if players_vote == buy_list[0]:
                    first_item_votes += 1

                for npc in self.game_map.npcs:
                    if npc.study_group == self.player.study_group and not npc.is_dead:
                        # each NPC needs to vote
                        total_votes += 1
                        buy_item = random.choice(buy_list)
                        if buy_item == buy_list[0]:
                            first_item_votes += 1
                        npc.emote_manager.show_emote(npc, buy_item)
                # check which option has the majority of votes
                # in case of draw, Player vote decides
                if first_item_votes == total_votes / 2:
                    total_votes += 1
                    if players_vote == buy_list[0]:
                        first_item_votes += 1
                winner_item = (
                    buy_list[0] if first_item_votes > total_votes / 2 else buy_list[1]
                )
                # restore backup EmoteManager
                self.player_emote_manager = self.backup_emote_mgr
                self.player.emote_manager = self.player_emote_manager
                self.game_map.player_emote_manager = self.player_emote_manager
                self.game_map._setup_emote_interactions()

                # immediately switch to a new dialog with vote results
                dialog_name = f"scripted_sequence_buy_{winner_item}"
                post_event(DIALOG_SHOW, dial=dialog_name)
                # start ending Scripted Sequence with a new end condition
                if self.player.study_group == StudyGroup.INGROUP:
                    animation_name = "ingroup_gathering_end"
                else:
                    animation_name = "outgroup_gathering_end"

                self.cutscene_animation.set_current_animation(animation_name)
                self.cutscene_animation.is_end_condition_met = (
                    self.end_scripted_sequence_decision_result
                )
                self.cutscene_animation.reset()
                self.cutscene_animation.start()

    def end_scripted_sequence_decision_result(self) -> bool:
        # prevent the scripted sequence from ending
        # while dialog is still opened
        if self.player.blocked:
            return False

        self.scripted_sequence_cleanup()

        return True

    def scripted_sequence_cleanup(self):
        self.player.teleport(self.prev_player_pos)
        self.cutscene_animation.set_current_animation(DEFAULT_ANIMATION_NAME)
        self.cutscene_animation.is_end_condition_met = lambda: True

    def get_camera_pos(self):
        return self.camera.state.topleft

    def start_transition(self):
        self.player.blocked = True
        self.player.direction = pygame.Vector2(0, 0)

    def finish_transition(self):
        self.player.blocked = False

    def start_day_transition(self):
        self.day_transition.activate()
        self.start_transition()

    # reset
    def reset(self):
        self.current_day += 1

        # plants + soil
        if self.current_map == Map.NEW_FARM:
            self.soil_manager.update()

        self.raining = random.randint(0, 10) > 7
        self.soil_manager.raining = self.raining

        # apples on the trees

        # No need to iterate using explicit sprites() call.
        # Iterating over a sprite group normally will do the same thing
        for tree in self.tree_sprites:
            for fruit in tree.fruit_sprites:
                fruit.kill()
            if tree.alive:
                tree.create_fruit()
        for bush in self.bush_sprites:
            for fruit in bush.fruit_sprites:
                fruit.kill()
                bush.create_fruit()

        # sky
        self.sky.start_color = [255, 255, 255]
        self.game_time.set_time(6, 0)  # set to 0600 hours upon sleeping

    def start_map_transition(self):
        self.map_transition.activate()
        self.start_transition()

    def decay_health(self):
        if self.player.hp > 10:
            if not self.player.bathstat and not self.player.has_goggles:
                self.overlay.health_bar.apply_damage(HEALTH_DECAY_VALUE)
            elif not self.player.has_goggles and self.player.bathstat:
                self.overlay.health_bar.apply_damage((HEALTH_DECAY_VALUE / 2))

    def check_map_exit(self):
        if not self.map_transition:
            for warp_hitbox in self.player_exit_warps:
                if self.player.hitbox_rect.colliderect(warp_hitbox.rect):
                    self.map_transition.reset = partial(
                        self.switch_to_map, warp_hitbox.name
                    )
                    self.start_map_transition()
                    return

    # draw
    # region debug-overlays
    def draw_hitboxes(self):
        if self.show_hitbox_active:
            offset = pygame.Vector2(self.get_camera_pos())

            for sprite in self.collision_sprites:
                rect = sprite.rect.copy()
                rect.topleft += offset
                pygame.draw.rect(self.display_surface, "red", rect, 2)

                hitbox = sprite.hitbox_rect.copy()
                hitbox.topleft += offset
                pygame.draw.rect(self.display_surface, "blue", hitbox, 2)

                if isinstance(sprite, Character):
                    hitbox = sprite.axe_hitbox.copy()
                    hitbox.topleft += offset
                    pygame.draw.rect(self.display_surface, "green", hitbox, 2)
            for drop in self.drop_sprites:
                pygame.draw.rect(
                    self.display_surface, "red", drop.rect.move(*offset), 2
                )
                pygame.draw.rect(
                    self.display_surface, "blue", drop.hitbox_rect.move(*offset), 2
                )

    def setup_pf_overlay(self):
        self.pf_overlay_non_walkable = pygame.Surface(
            (SCALED_TILE_SIZE, SCALED_TILE_SIZE), pygame.SRCALPHA
        )
        self.pf_overlay_non_walkable.fill((255, 128, 128))
        pygame.draw.rect(
            self.pf_overlay_non_walkable,
            (0, 0, 0),
            (0, 0, SCALED_TILE_SIZE, SCALED_TILE_SIZE),
            2,
        )
        self.pf_overlay_non_walkable.set_alpha(92)

    def draw_pf_overlay(self):
        if self.show_pf_overlay:
            offset = pygame.Vector2(self.get_camera_pos())

            if AIData.setup:
                for y in range(len(AIData.Matrix)):
                    for x in range(len(AIData.Matrix[y])):
                        if not AIData.Matrix[y][x]:
                            self.display_surface.blit(
                                self.pf_overlay_non_walkable,
                                (
                                    x * SCALED_TILE_SIZE + offset.x,
                                    y * SCALED_TILE_SIZE + offset.y,
                                ),
                            )

            for npe in self.game_map.animals + self.game_map.npcs:
                if npe.pf_path:
                    offset = pygame.Vector2(0, 0)
                    offset.x = -(self.player.rect.centerx - SCREEN_WIDTH / 2)
                    offset.y = -(self.player.rect.centery - SCREEN_HEIGHT / 2)
                    for i in range(len(npe.pf_path)):
                        start_pos = (
                            (npe.pf_path[i][0]) * SCALED_TILE_SIZE + offset.x,
                            (npe.pf_path[i][1]) * SCALED_TILE_SIZE + offset.y,
                        )
                        if i == 0:
                            end_pos = (
                                npe.hitbox_rect.centerx + offset.x,
                                npe.hitbox_rect.centery + offset.y,
                            )
                        else:
                            end_pos = (
                                (npe.pf_path[i - 1][0]) * SCALED_TILE_SIZE + offset.x,
                                (npe.pf_path[i - 1][1]) * SCALED_TILE_SIZE + offset.y,
                            )
                        pygame.draw.aaline(
                            self.display_surface, (0, 0, 0), start_pos, end_pos
                        )

    # endregion

    def draw_overlay(self):
        self.sky.display(self.get_round())
        self.overlay.display()

    def draw(self, dt: float, move_things: bool):
        self.player.hp = self.overlay.health_bar.hp
        self.display_surface.fill((130, 168, 132))
        self.all_sprites.draw(self.camera, False)

        self.draw_pf_overlay()
        self.draw_hitboxes()

        self.zoom_manager.apply_zoom()
        if move_things:
            self.sky.display(self.get_round())

        self.draw_overlay()

        if self.current_minigame and self.current_minigame.running:
            self.current_minigame.draw()

        # transitions
        self.day_transition.draw()
        self.map_transition.draw()

    # update
    def update_rain(self):
        if self.raining:
            self.rain.update()

    def update_cutscene(self, dt):
        if self.cutscene_animation.active:
            self.cutscene_animation.update(dt)

    def update(self, dt: float, move_things: bool = True):
        # update
        self.handle_controls()

        self.game_time.update()
        self.check_map_exit()
        self.check_outgroup_logic()

        if self.current_minigame and self.current_minigame.running:
            self.current_minigame.update(dt)

        self.update_rain()
        self.day_transition.update()
        self.map_transition.update()
        if move_things:
            if self.cutscene_animation.active:
                self.all_sprites.update_blocked(dt)
            else:
                self.all_sprites.update(dt)
            self.update_cutscene(dt)
            self.quaker.update_quake(dt)

            self.camera.update(
                self.cutscene_animation
                if self.cutscene_animation.active
                else self.player
            )

            self.zoom_manager.update(
                (
                    self.cutscene_animation
                    if self.cutscene_animation.active
                    else self.player
                ),
                dt,
            )

            self.decay_health()
        self.draw(dt, move_things)

        for control in self.controls:
            control.click = False
