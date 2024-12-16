# /// script
# dependencies = [
#  "pygame-ce",
#  "pytmx",
#  "pathfinding",
# ]
# ///

import asyncio
import copy
import random
import sys
from typing import Any

import pygame

from src.client import send_telemetry
from src import support
from src.enums import CustomCursor, GameState, ScriptedSequenceType, SelfAssessmentDimension
from src.events import DIALOG_ADVANCE, DIALOG_SHOW, OPEN_INVENTORY, SET_CURSOR
from src.groups import AllSprites
from src.gui.interface.dialog import DialogueManager
from src.gui.setup import setup_gui
from src.overlay.fast_forward import FastForward
from src.savefile import SaveFile
from src.screens.inventory import InventoryMenu, prepare_checkmark_for_buttons
from src.screens.level import Level
from src.screens.menu_main import MainMenu
from src.screens.menu_notification import NotificationMenu
from src.screens.menu_pause import PauseMenu
from src.screens.menu_round_end import RoundMenu
from src.screens.menu_settings import SettingsMenu
from src.screens.player_task import PlayerTask
from src.screens.self_assessment_menu import SelfAssessmentMenu
from src.screens.shop import ShopMenu
from src.screens.switch_to_outgroup_menu import OutgroupMenu
from src.settings import (
    DEBUG_MODE_VERSION,
    EMOTE_SIZE,
    RANDOM_SEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TB_SIZE,
    USE_SERVER,
    AniFrames,
    MapDict,
    SoundDict,
)
from src.sprites.setup import setup_entity_assets
from src.tutorial.tutorial import Tutorial

# set random seed. It has to be set first before any other random function is called.
random.seed(RANDOM_SEED)
_COSMETICS = frozenset({"goggles", "horn", "necklace", "hat"})
# Due to the unconventional sizes of the cosmetics' icons, different scale factors are needed
_COSMETIC_SCALE_FACTORS = {"goggles": 2, "horn": 4, "necklace": 2, "hat": 3}
_COSMETIC_SUBSURF_AREAS = {
    "goggles": pygame.Rect(0, 0, 27, 16),
    "horn": pygame.Rect(32, 0, 16, 16),
    "necklace": pygame.Rect(0, 16, 21, 22),
    "hat": pygame.Rect(24, 16, 20, 11),
}


class Game:
    def __init__(self) -> None:
        # main setup
        pygame.init()
        screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.display_surface = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Clear Skies")

        # frames
        self.level_frames: dict | None = None
        self.item_frames: dict[str, pygame.Surface] | None = None
        self.cosmetic_frames: dict[str, pygame.Surface] = {}
        self.frames: dict[str, dict] | None = None
        self.previous_frame = ""
        self.fast_forward = FastForward()
        # assets
        self.tmx_maps: MapDict | None = None

        self.emotes: AniFrames | None = None

        self.font: pygame.font.Font | None = None
        self.sounds: SoundDict | None = None

        self._available_cursors: list[pygame.Surface] = []
        self._cursor: int = CustomCursor.ARROW
        self._cursor_img: pygame.Surface | None = None

        self.save_file = SaveFile.load()

        # main setup
        self.running = True
        self.clock = pygame.time.Clock()
        self.load_assets()

        # config of all game versions and all rounds: rounds_config[game_version][round_no][feature_name] = value
        self.rounds_config: list[list[dict[str, Any]]] = support.load_data("rounds_config.json")
        # config of current game version of a current round: round_config[feature_name] = value
        self.round_config: dict[str, Any] = {}
        # copy first config (for round 1) and use it as a base for the debug version (all features enabled)
        debug_config = copy.deepcopy(self.rounds_config[0])

        for level in debug_config:
            for key, value in level.items():
                # turn on all feature flags
                if type(value) is bool:
                    level[key] = True
        # add debug config to the start of list (DEBUG_MODE_VERSION == 0)
        # print(debug_config)
        # with open("test.json", "w") as file:
        #     json.dump(debug_config, file, indent=4)  # Writing with pretty-printing

        self.rounds_config.insert(DEBUG_MODE_VERSION, debug_config)

        self.get_round = lambda: self.round
        self.game_version: int = -1
        self.round: int = -1
        self.token: str = ""
        self.jwt: str = ""
        if not USE_SERVER:
            self.set_token({"token": "000", "jwt": "dummy_token", "game_version": 0})
        self.round_end_timer: float = 0.0
        self.ROUND_END_TIME_IN_MINUTES: float = 99999999.0

        # screens
        self.level = Level(
            self.switch_state,
            (self.get_round, self.set_round),
            self.round_config,
            lambda: self.game_version,
            self.tmx_maps,
            self.frames,
            self.sounds,
            self.save_file,
            self.clock,
        )
        self.player = self.level.player

        self.token_status = False
        self.allocation_task = PlayerTask(self.send_resource_allocation)
        self.main_menu = MainMenu(self.switch_state, self.set_token)
        self.pause_menu = PauseMenu(self.switch_state)
        self.settings_menu = SettingsMenu(
            self.switch_state, self.sounds, self.player.controls
        )
        self.shop_menu = ShopMenu(self.player, self.switch_state, self.font)
        self.inventory_menu = InventoryMenu(
            self.player,
            self.frames,
            self.switch_state,
            self.player.assign_tool,
            self.player.assign_seed,
        )
        self.round_menu = RoundMenu(
            self.switch_state, self.player, self.increment_round, self.get_round
        )
        self.outgroup_menu = OutgroupMenu(
            self.player,
            self.switch_state,
        )

        self.self_assessment_menu = SelfAssessmentMenu(
            self.send_self_assessment,
            (
                SelfAssessmentDimension.VALENCE,
                SelfAssessmentDimension.AROUSAL,
                SelfAssessmentDimension.DOMINANCE,
            ),
        )

        self.notification_menu = NotificationMenu(
            self.switch_state,
            "This is a very long Test Message with German characters: üß",
        )

        # dialog
        self.all_sprites = AllSprites()
        self.dialogue_manager = DialogueManager(
            self.all_sprites, "data/textboxes/dialogues.json"
        )

        # dialogue text box positions
        self.msg_left = SCREEN_WIDTH / 2 - TB_SIZE[0] / 2
        self.msg_top = SCREEN_HEIGHT - TB_SIZE[1]

        # screens
        self.menus = {
            GameState.MAIN_MENU: self.main_menu,
            GameState.PAUSE: self.pause_menu,
            GameState.SETTINGS: self.settings_menu,
            GameState.SHOP: self.shop_menu,
            GameState.INVENTORY: self.inventory_menu,
            GameState.PLAYER_TASK: self.allocation_task,
            GameState.ROUND_END: self.round_menu,
            GameState.OUTGROUP_MENU: self.outgroup_menu,
            GameState.SELF_ASSESSMENT: self.self_assessment_menu,
            GameState.NOTIFICATION_MENU: self.notification_menu,
        }
        self.current_state = GameState.MAIN_MENU

        # tutorial
        self.tutorial = Tutorial(self.all_sprites, self.player, self.level)

        # intro to game and in-group msg.
        self.intro_txt_is_rendering = False
        self.intro_txt_rendered = False

    def send_self_assessment(self, assessment: dict[str, int]) -> None:
        telemetry = {
            "self_assessment": assessment,
            "game_version": self.game_version,
            "game_round": self.round,
            "round_timer": round(self.round_end_timer, 2),
        }
        send_telemetry(self.jwt, telemetry)
        self.switch_state(GameState.PLAY)

    def send_resource_allocation(self, resource_allocation: dict[str, Any]) -> None:
        telemetry = {
            "resource_allocation": resource_allocation,
            "game_version": self.game_version,
            "game_round": self.round,
            "round_timer": round(self.round_end_timer, 2),
        }
        send_telemetry(self.jwt, telemetry)
        self.switch_state(GameState.PLAY)

    def set_token(self, response: dict[str, Any]) -> None:
        # print(f"Got token '{response["token"]}'")
        self.token = response["token"]
        self.jwt = response["jwt"]
        self.game_version = response["game_version"]

        if not USE_SERVER:
            # token 100-349 triggers game version 1,
            # token 350-599 triggers game version 2,
            # token 600-849 triggers game version 3
            # token 0 or 999 triggers game in debug mode (all features enabled)
            try:
                token_int = int(self.token)
            except ValueError:
                raise ValueError("Invalid token value")
            if token_int in range(100, 350):
                self.game_version = 1
            elif token_int in range(350, 600):
                self.game_version = 2
            elif token_int in range(600, 850):
                self.game_version = 3
            elif token_int in [0, 999]:
                self.game_version = DEBUG_MODE_VERSION
            else:
                raise ValueError("Invalid token value")

        print(f"Game version {self.game_version}")
        self.set_round(1)

    def set_round(self, round: int) -> None:
        self.round = round
        # if config for given round number not found, use first one as fall back
        # TODO: fix volcano eruption (`m`) debug which switched round to not existing value of 7
        if self.game_version < 0:
            self.game_version = DEBUG_MODE_VERSION

        if round < len(self.rounds_config[self.game_version]):
            self.round_config = self.rounds_config[self.game_version][round - 1]
        else:
            print(f"ERROR: No config found for round {round}! Using config for round 1.")
            self.round_config = self.rounds_config[self.game_version][0]
        self.level.round_config_changed(self.round_config)
        self.round_end_timer = 0.0
        self.ROUND_END_TIME_IN_MINUTES = self.round_config["level_duration"] / 60  # 15
        print(self.round_config["level_name_text"])

    def increment_round(self) -> None:
        if self.round < 12:
            self.set_round(self.round + 1)

    def switch_state(self, state: GameState) -> None:
        self.set_cursor(CustomCursor.ARROW)
        self.current_state = state
        if self.current_state == GameState.SAVE_AND_RESUME:
            self.save_file.set_soil_data(*self.level.soil_manager.all_soil_sprites())
            self.level.player.save()
            self.current_state = GameState.PLAY
        if self.current_state == GameState.INVENTORY:
            self.inventory_menu.refresh_buttons_content()
        if self.current_state == GameState.ROUND_END:
            self.round_menu.reset_menu()
            self.round_menu.generate_items()
        # if self.current_state == GameState.PLAYER_TASK:
        #     self.allocation_task.round = self.get_round()
        if self.game_paused():
            self.player.blocked = True
            self.player.direction.update((0, 0))
        else:
            self.player.blocked = False

    def set_cursor(self, cursor: CustomCursor, override: bool = False) -> None:
        if self._cursor != cursor:
            # ensure the cursor does not get switched back to CustomCursor.POINT during
            # click animation
            if (
                self._cursor != CustomCursor.CLICK
                or cursor != CustomCursor.POINT
                or override
            ):
                self._cursor = cursor
                self._cursor_img = self._available_cursors[self._cursor]

    def load_assets(self) -> None:
        self.tmx_maps = support.tmx_importer("data/maps")

        # frames
        self.emotes = support.animation_importer(
            "images/ui/emotes/sprout_lands", frame_size=EMOTE_SIZE, resize=EMOTE_SIZE
        )

        self.level_frames = {
            "animations": support.animation_importer("images", "misc"),
            "soil": support.import_folder_dict("images/tilesets/soil"),
            "soil water": support.import_folder_dict("images/tilesets/soil/soil water"),
            "tomato": support.import_folder("images/tilesets/plants/tomato"),
            "corn": support.import_folder("images/tilesets/plants/corn"),
            "rain drops": support.import_folder("images/rain/drops"),
            "rain floor": support.import_folder("images/rain/floor"),
            "objects": support.import_folder_dict("images/objects"),
            "drops": support.import_folder_dict("images/drops"),
        }
        self.item_frames = support.import_folder_dict("images/objects/items")
        cosmetic_surf = pygame.image.load(
            support.resource_path("images/ui/cosmetics.png")
        ).convert_alpha()
        for cosmetic in _COSMETICS:
            self.cosmetic_frames[cosmetic] = pygame.transform.scale_by(
                cosmetic_surf.subsurface(_COSMETIC_SUBSURF_AREAS[cosmetic]),
                _COSMETIC_SCALE_FACTORS[cosmetic],
            )
        self.frames = {
            "emotes": self.emotes,
            "level": self.level_frames,
            "items": self.item_frames,
            "cosmetics": self.cosmetic_frames,
            "checkmark": pygame.transform.scale_by(
                pygame.image.load(
                    support.resource_path("images/ui/checkmark.png")
                ).convert_alpha(),
                4,
            ),
        }
        prepare_checkmark_for_buttons(self.frames["checkmark"])

        for member in CustomCursor:
            cursor = pygame.image.load(
                support.resource_path(f"images/ui/cursor/{member.value}.png")
            ).convert_alpha()
            cursor = pygame.transform.scale_by(cursor, 4)
            self._available_cursors.append(cursor)

        self._cursor_img = self._available_cursors[CustomCursor.ARROW]

        setup_entity_assets()

        setup_gui()

        # sounds
        self.sounds = support.sound_importer("audio", default_volume=0.25)

        self.font = support.import_font(30, "font/LycheeSoda.ttf")

    def game_paused(self) -> bool:
        return self.current_state != GameState.PLAY

    def show_intro_msg(self) -> None:
        # A Message At The Starting Of The Game Giving Introduction To The Game And The InGroup.
        if not self.intro_txt_is_rendering:
            if not self.game_paused():
                # TODO revert, this only for debug
                if self.round_config.get("character_introduction_text", "") \
                        and self.round_config["character_introduction_timestamp"] \
                        and self.round_end_timer > self.round_config["character_introduction_timestamp"][0]:
                    label = "press <Space> to continue"
                    self.dialogue_manager.set_item(
                        "intro_to_game",
                        [
                            ["Clear Skies", f"{self.round_config["character_introduction_text"]}\t\t\t\t\t\t\t{label}"],
                            ["Clear Skies", f"{self.round_config["ingroup_introduction_text"]}\t\t\t\t\t\t\t{label}"]
                        ]
                    )
                    self.dialogue_manager.open_dialogue(
                        "intro_to_game", self.msg_left, self.msg_top
                    )
                self.intro_txt_is_rendering = True
                self.intro_txt_rendered = True
        elif not self.level.cutscene_animation.active:
            if (
                self.dialogue_manager.showing_dialogue
            ):  # prepare text box to switch to tutorial
                if self.intro_txt_rendered:
                    self.dialogue_manager.advance()
                    self.intro_txt_rendered = False
            elif not self.player.save_file.is_tutorial_completed:
                try:
                    self.tutorial.dialogue_manager._get_current_tb()  # to execute ready() only at the beginning
                except Exception:
                    self.tutorial.ready()

    # events
    def event_loop(self) -> None:
        for event in pygame.event.get():
            if self.handle_event(event):
                continue

            if self.game_paused():
                if self.menus[self.current_state].handle_event(event):
                    continue

            if self.level.handle_event(event):
                continue

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                if self._cursor == CustomCursor.POINT:
                    self.set_cursor(CustomCursor.CLICK)
            return False  # allow UI elements to handle this event as well

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == pygame.BUTTON_LEFT:
                if self._cursor == CustomCursor.CLICK:
                    self.set_cursor(CustomCursor.POINT, override=True)
            return False

        elif event.type == OPEN_INVENTORY:
            self.switch_state(GameState.INVENTORY)
            return True
        elif event.type == DIALOG_SHOW:
            if self.dialogue_manager.showing_dialogue:
                pass
            else:
                self.dialogue_manager.open_dialogue(
                    event.dial, self.msg_left, self.msg_top
                )
                self.player.blocked = True
                self.player.direction.update((0, 0))
            return True
        elif event.type == DIALOG_ADVANCE:
            if self.dialogue_manager.showing_dialogue:
                self.dialogue_manager.advance()
                if not self.dialogue_manager.showing_dialogue:
                    self.player.blocked = False
            return True
        elif event.type == SET_CURSOR:
            self.set_cursor(event.cursor)
            return True
        return False

    async def run(self) -> None:
        pygame.mouse.set_visible(False)
        is_first_frame = True
        while self.running:
            dt = self.clock.tick() / 1000

            self.event_loop()

            is_game_paused = self.game_paused()

            if not is_game_paused or is_first_frame:
                if self.level.cutscene_animation.active:
                    event = pygame.key.get_pressed()
                    if event[pygame.K_RSHIFT]:
                        self.level.update(dt * 5, self.current_state == GameState.PLAY)
                    else:
                        self.level.update(dt, self.current_state == GameState.PLAY)
                else:
                    self.level.update(dt, self.current_state == GameState.PLAY)

            if is_game_paused and not is_first_frame:
                self.display_surface.blit(self.previous_frame, (0, 0))
                self.menus[self.current_state].update(dt)
            else:
                self.round_end_timer += dt
                if self.round_end_timer > self.ROUND_END_TIME_IN_MINUTES * 60:
                    self.round_end_timer = 0
                    self.switch_state(GameState.ROUND_END)
                # elif self.round_config.get("character_introduction_text", "") \
                #         and self.round_config["character_introduction_timestamp"] \
                #         and self.round_end_timer > self.round_config["character_introduction_timestamp"][0]:
                #     # make a copy of a string
                #     message = self.round_config["character_introduction_text"][:]
                #     self.notification_menu.message = message
                #     self.switch_state(GameState.NOTIFICATION_MENU)
                #     # set to empty to not repeat
                #     self.round_config["character_introduction_text"] = ""
                #     self.round_config["character_introduction_timestamp"] = []
                elif self.round_config.get("notify_new_crop_text", "") \
                        and self.round_config["notify_new_crop_timestamp"] \
                        and self.round_end_timer > self.round_config["notify_new_crop_timestamp"][0]:
                    # make a copy of a string
                    message = self.round_config["notify_new_crop_text"][:]
                    self.notification_menu.message = message
                    self.switch_state(GameState.NOTIFICATION_MENU)
                    # set to empty to not repeat
                    self.round_config["notify_new_crop_text"] = ""
                    self.round_config["notify_new_crop_timestamp"] = []
                elif len(self.round_config.get("self_assessment_timestamp", [])) > 0 \
                        and self.round_end_timer > self.round_config["self_assessment_timestamp"][0]:
                    # remove first timestamp from list not to repeat infinitely
                    self.round_config["self_assessment_timestamp"] = self.round_config["self_assessment_timestamp"][1:]
                    self.switch_state(GameState.SELF_ASSESSMENT)
                elif len(self.round_config.get("player_hat_sequence_timestamp", [])) > 0 \
                        and self.round_end_timer > self.round_config["player_hat_sequence_timestamp"][0]:
                    # remove first timestamp from list not to repeat infinitely
                    self.round_config["player_hat_sequence_timestamp"] = \
                        self.round_config["player_hat_sequence_timestamp"][1:]
                    self.level.start_scripted_sequence(ScriptedSequenceType.PLAYER_RECEIVES_HAT)
                elif len(self.round_config.get("ingroup_necklace_sequence_timestamp", [])) > 0 \
                        and self.round_end_timer > self.round_config["ingroup_necklace_sequence_timestamp"][0]:
                    # remove first timestamp from list not to repeat infinitely
                    self.round_config["ingroup_necklace_sequence_timestamp"] = \
                        self.round_config["ingroup_necklace_sequence_timestamp"][1:]
                    self.level.start_scripted_sequence(ScriptedSequenceType.NPC_RECEIVES_NECKLACE)
                elif len(self.round_config.get("player_necklace_sequence_timestamp", [])) > 0 \
                        and self.round_end_timer > self.round_config["player_necklace_sequence_timestamp"][0]:
                    # remove first timestamp from list not to repeat infinitely
                    self.round_config["player_necklace_sequence_timestamp"] = \
                        self.round_config["player_necklace_sequence_timestamp"][1:]
                    self.level.start_scripted_sequence(ScriptedSequenceType.PLAYER_RECEIVES_NECKLACE)
                elif len(self.round_config.get("player_birthday_sequence_timestamp", [])) > 0 \
                        and self.round_end_timer > self.round_config["player_birthday_sequence_timestamp"][0]:
                    # remove first timestamp from list not to repeat infinitely
                    self.round_config["player_birthday_sequence_timestamp"] = \
                        self.round_config["player_birthday_sequence_timestamp"][1:]
                    self.level.start_scripted_sequence(ScriptedSequenceType.PLAYERS_BIRTHDAY)
                elif self.round_config.get("resource_allocation_text", "") \
                        and self.round_config["resource_allocation_timestamp"] \
                        and self.round_end_timer > self.round_config["resource_allocation_timestamp"][0]:
                    # make a copy of a string
                    allocations_text = self.round_config["resource_allocation_text"][:]
                    # self.allocation_task.title = message
                    self.allocation_task.allocations_text = allocations_text
                    self.allocation_task.parse_allocation_items(self.round_config["resource_allocation_item_text"])
                    self.switch_state(GameState.PLAYER_TASK)
                    # set to empty not to repeat infinitely
                    self.round_config["resource_allocation_text"] = ""
                    self.round_config["resource_allocation_timestamp"] = []

            if self.level.cutscene_animation.active:
                self.all_sprites.update_blocked(dt)
                if self.current_state == GameState.PLAY:
                    event = pygame.key.get_pressed()
                    self.fast_forward.draw_option(self.display_surface)
                    if event[pygame.K_RSHIFT]:
                        self.fast_forward.draw_overlay(self.display_surface)
            else:
                self.all_sprites.update(dt)
            # self.all_sprites.draw(self.level.camera, is_game_paused)

            # Apply blur effect only if the player has goggles equipped
            if self.player.has_goggles and self.current_state == GameState.PLAY:
                surface = pygame.transform.box_blur(self.display_surface, 3)
                self.display_surface.blit(surface, (0, 0))

            # Into and Tutorial
            self.show_intro_msg()
            if not self.player.save_file.is_tutorial_completed:
                self.tutorial.update(is_game_paused)

            mouse_pos = pygame.mouse.get_pos()
            if not is_game_paused or is_first_frame:
                self.previous_frame = self.display_surface.copy()
            self.display_surface.blit(self._cursor_img, mouse_pos)
            is_first_frame = False
            pygame.display.update()
            await asyncio.sleep(0)


if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())
