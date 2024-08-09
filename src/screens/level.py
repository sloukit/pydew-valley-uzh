import warnings
from collections.abc import Callable
from functools import partial
from random import randint

import pygame

from src.enums import FarmingTool, GameState, Map
from src.events import DIALOG_ADVANCE, DIALOG_SHOW, post_event
from src.groups import AllSprites, PersistentSpriteGroup
from src.gui.interface.emotes import NPCEmoteManager, PlayerEmoteManager
from src.gui.scene_animation import SceneAnimation
from src.npc.setup import AIData
from src.overlay.game_time import GameTime
from src.overlay.overlay import Overlay
from src.overlay.sky import Rain, Sky
from src.overlay.soil import SoilLayer
from src.overlay.transition import Transition
from src.screens.game_map import GameMap
from src.settings import (
    GAME_MAP,
    SCALED_TILE_SIZE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    MapDict,
    SoundDict,
)
from src.sprites.character import Character
from src.sprites.drops import DropsManager
from src.sprites.entities.player import Player
from src.sprites.particle import ParticleSprite
from src.sprites.setup import ENTITY_ASSETS
from src.support import load_data, map_coords_to_tile, resource_path


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

    # sprite groups
    all_sprites: AllSprites
    collision_sprites: PersistentSpriteGroup
    tree_sprites: PersistentSpriteGroup
    bush_sprites: PersistentSpriteGroup
    interaction_sprites: PersistentSpriteGroup
    drop_sprites: pygame.sprite.Group
    player_exit_warps: pygame.sprite.Group

    # farming
    soil_layer: SoilLayer

    # emotes
    _emotes: dict
    player_emote_manager: PlayerEmoteManager
    npc_emote_manager: NPCEmoteManager

    player: Player

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

    def __init__(
        self,
        switch: Callable[[GameState], None],
        tmx_maps: MapDict,
        frames: dict[str, dict],
        sounds: SoundDict,
    ):
        # main setup
        self.display_surface = pygame.display.get_surface()
        self.switch_screen = switch

        # cutscene
        target_points = [(100, 100), (200, 200), (300, 100), (800, 900)]
        speeds = [100, 150, 200]  # Different speeds for each segment
        pauses = [0, 1, 0.5, 2]  # Pauses at each point in seconds
        self.cut_scene_animation = SceneAnimation(target_points, speeds, pauses)

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

        self.soil_layer = SoilLayer(self.all_sprites, self.frames["level"])

        self._emotes = self.frames["emotes"]
        self.player_emote_manager = PlayerEmoteManager(self._emotes, self.all_sprites)
        self.npc_emote_manager = NPCEmoteManager(self._emotes, self.all_sprites)

        self.player = Player(
            pos=(0, 0),
            assets=ENTITY_ASSETS.RABBIT,
            groups=(),
            collision_sprites=self.collision_sprites,
            apply_tool=self.apply_tool,
            plant_collision=self.plant_collision,
            interact=self.interact,
            emote_manager=self.player_emote_manager,
            sounds=self.sounds,
        )
        self.all_sprites.add_persistent(self.player)
        self.collision_sprites.add_persistent(self.player)

        # drops manager
        self.drops_manager = DropsManager(
            self.all_sprites, self.drop_sprites, self.frames["level"]["drops"]
        )
        self.drops_manager.player = self.player

        # weather
        self.game_time = GameTime()
        self.sky = Sky(self.game_time)
        self.rain = Rain(self.all_sprites, self.frames["level"])
        self.raining = False

        self.load_map(GAME_MAP)
        self.map_transition = Transition(
            lambda: self.switch_to_map(self.current_map),
            self.finish_transition,
            dur=2400,
        )

        self.activate_music()

        # day night cycle
        self.day_transition = Transition(self.reset, self.finish_transition, dur=3200)
        self.current_day = 0

        # overlays
        self.overlay = Overlay(self.player, frames["overlay"], self.game_time)
        self.show_hitbox_active = False

    def load_map(self, game_map: Map, from_map: str = None):
        # prepare level state for new map
        # clear all sprite groups
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.interaction_sprites.empty()
        self.tree_sprites.empty()
        self.bush_sprites.empty()
        self.player_exit_warps.empty()

        # clear existing soil_layer
        self.soil_layer.reset()

        self.game_map = GameMap(
            tilemap=self.tmx_maps[game_map],
            all_sprites=self.all_sprites,
            collision_sprites=self.collision_sprites,
            interaction_sprites=self.interaction_sprites,
            tree_sprites=self.tree_sprites,
            bush_sprites=self.bush_sprites,
            player_exit_warps=self.player_exit_warps,
            player=self.player,
            player_emote_manager=self.player_emote_manager,
            npc_emote_manager=self.npc_emote_manager,
            drops_manager=self.drops_manager,
            soil_layer=self.soil_layer,
            apply_tool=self.apply_tool,
            plant_collision=self.plant_collision,
            frames=self.frames,
        )

        player_spawn = None

        # search for player entry warp depending on which map they came from
        if from_map:
            player_spawn = self.game_map.player_entry_warps.get(from_map)
            if not player_spawn:
                warnings.warn(
                    f'No valid entry warp found for "{game_map}" '
                    f'from: "{self.current_map}"'
                )

        # use default spawnpoint if no origin map is specified,
        # or if no entry warp for the player's origin map is found
        if not player_spawn:
            if self.game_map.player_spawnpoint:
                player_spawn = self.game_map.player_spawnpoint
            else:
                warnings.warn(f"No default spawnpoint found on {game_map}")
                # fallback to the first player entry warp
                player_spawn = next(iter(self.game_map.player_entry_warps.values()))

        self.player.teleport(player_spawn)

        self.rain.set_floor_size(self.game_map.get_size())

        self.current_map = game_map

    def activate_music(self):
        volume = 0.1
        try:
            sound_data = load_data("volume.json")
            volume = sound_data["music"]
            # sfx = sound_data['sfx']
        except FileNotFoundError:
            pass
        self.sounds["music"].set_volume(min((volume / 1000), 0.4))
        self.sounds["music"].play(-1)

    # plant collision
    def plant_collision(self, character: Character):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites:
                if plant.rect.colliderect(character.hitbox_rect):
                    x, y = map_coords_to_tile(plant.rect.center)
                    self.soil_layer.harvest(
                        (x, y), character.add_resource, self.create_particle
                    )

    def switch_to_map(self, map_name: Map):
        if self.tmx_maps.get(map_name):
            self.load_map(map_name, from_map=self.current_map)
        else:
            if map_name == "bathhouse":
                self.overlay.health_bar.apply_health(9999999)
                self.reset()
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

    def apply_tool(self, tool: FarmingTool, pos: tuple[int, int], entity: Character):
        match tool:
            case FarmingTool.AXE:
                for tree in pygame.sprite.spritecollide(
                    entity,
                    self.tree_sprites,
                    False,
                    lambda spr, tree_spr: spr.axe_hitbox.colliderect(
                        tree_spr.hitbox_rect
                    ),
                ):
                    tree.hit(entity)
                    self._play_playeronly_sound("axe", entity)
            case FarmingTool.HOE:
                if self.soil_layer.hoe(pos):
                    self._play_playeronly_sound("hoe", entity)
            case FarmingTool.WATERING_CAN:
                self.soil_layer.water(pos)
                self._play_playeronly_sound("water", entity)
            case _:  # All seeds
                if self.soil_layer.plant(pos, tool, entity.remove_resource):
                    self._play_playeronly_sound("plant", entity)
                else:
                    self._play_playeronly_sound("cant_plant", entity)

    def interact(self):
        collided_interactions = pygame.sprite.spritecollide(
            self.player, self.interaction_sprites, False
        )
        if collided_interactions:
            if collided_interactions[0].name == "Bed":
                self.start_day_transition()
            if collided_interactions[0].name == "Trader":
                self.switch_screen(GameState.SHOP)
            if collided_interactions[0] in self.bush_sprites.sprites():
                if self.player.axe_hitbox.colliderect(
                    collided_interactions[0].hitbox_rect
                ):
                    collided_interactions[0].hit(self.player)

    def handle_event(self, event: pygame.event.Event) -> bool:
        hitbox_key = self.player.controls.SHOW_HITBOXES.control_value
        dialog_key = self.player.controls.SHOW_DIALOG.control_value
        advance_dialog_key = self.player.controls.ADVANCE_DIALOG.control_value

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PAUSE)
                return True
            if event.key == hitbox_key:
                self.show_hitbox_active = not self.show_hitbox_active
                return True
            if event.key == dialog_key:
                post_event(DIALOG_SHOW, dial="test")
                return True
            if event.key == advance_dialog_key:
                post_event(DIALOG_ADVANCE)
                return True

        return False

    def get_camera_center(self):
        if self.cut_scene_animation:
            return self.cut_scene_animation.get_current_position()

        return self.player.rect.center

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
        self.soil_layer.update()

        self.raining = randint(0, 10) > 7
        self.soil_layer.raining = self.raining

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
        self.sky.set_time(6, 0)  # set to 0600 hours upon sleeping

    def start_map_transition(self):
        self.map_transition.activate()
        self.start_transition()

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
    def draw_hitboxes(self):
        if self.show_hitbox_active:
            offset = pygame.Vector2(0, 0)
            offset.x = -(self.get_camera_center()[0] - SCREEN_WIDTH / 2)
            offset.y = -(self.get_camera_center()[1] - SCREEN_HEIGHT / 2)

            if AIData.setup:
                for y in range(len(AIData.Matrix)):
                    for x in range(len(AIData.Matrix[y])):
                        if not AIData.Matrix[y][x]:
                            surf = pygame.Surface(
                                (SCALED_TILE_SIZE, SCALED_TILE_SIZE), pygame.SRCALPHA
                            )
                            surf.fill((255, 128, 128))
                            pygame.draw.rect(
                                surf,
                                (0, 0, 0),
                                (0, 0, SCALED_TILE_SIZE, SCALED_TILE_SIZE),
                                2,
                            )
                            surf.set_alpha(92)

                            self.display_surface.blit(
                                surf,
                                (
                                    x * SCALED_TILE_SIZE + offset.x,
                                    y * SCALED_TILE_SIZE + offset.y,
                                ),
                            )

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

    def draw_overlay(self):
        self.sky.display()
        self.overlay.display()

    def draw(self, dt):
        self.display_surface.fill((130, 168, 132))
        camera_center = self.get_camera_center()
        self.all_sprites.draw(camera_center)
        self.sky.display()
        self.draw_overlay()
        self.day_transition.draw()
        self.map_transition.draw()

    # update
    def update_rain(self):
        if self.raining:
            self.rain.update()

    def update_cut_scene(self, dt):
        if self.cut_scene_animation:
            self.cut_scene_animation.update(dt)
            if self.cut_scene_animation.is_finished:
                self.cut_scene_animation = None

    def update(self, dt: float):
        # update
        self.game_time.update()
        self.check_map_exit()
        self.update_rain()
        self.day_transition.update()
        self.map_transition.update()
        self.all_sprites.update(dt)
        self.drops_manager.update()
        self.update_cut_scene(dt)

        # draw
        self.draw(dt)
        self.draw_hitboxes()
