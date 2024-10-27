# /// script
# dependencies = [
#  "pygame-ce",
#  "pytmx",
#  "pathfinding",
# ]
# ///

import asyncio
import random
import sys

import pygame

from src import support
from src.enums import GameState
from src.events import DIALOG_ADVANCE, DIALOG_SHOW, OPEN_INVENTORY
from src.gui.interface.dialog import DialogueManager
from src.gui.setup import setup_gui
from src.overlay.fast_forward import FastForward
from src.savefile import SaveFile
from src.screens.inventory import InventoryMenu, prepare_checkmark_for_buttons
from src.screens.level import Level
from src.screens.menu_main import MainMenu
from src.screens.menu_pause import PauseMenu
from src.screens.menu_round_end import RoundMenu
from src.screens.menu_settings import SettingsMenu
from src.screens.player_task import PlayerTask
from src.screens.shop import ShopMenu
from src.screens.switch_to_outgroup_menu import OutgroupMenu
from src.settings import (
    EMOTE_SIZE,
    RANDOM_SEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    AniFrames,
    MapDict,
    SoundDict,
)
from src.sprites.chunk_system.render_chunks import AllSprites
from src.sprites.setup import setup_entity_assets

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
    def __init__(self):
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

        self.save_file = SaveFile.load()

        # main setup
        self.running = True
        self.clock = pygame.time.Clock()
        self.load_assets()

        # level info
        self.ROUND_END_TIME_IN_MINUTES = 15
        self.round_end_timer = 0.0
        self.round = 1
        self.get_round = lambda: self.round

        # screens
        self.level = Level(
            self.switch_state,
            (self.get_round, self.set_round),
            self.tmx_maps,
            self.frames,
            self.sounds,
            self.save_file,
            self.clock,
        )
        self.player = self.level.player

        self.token_status = False
        self.main_menu = MainMenu(self.switch_state)
        self.pause_menu = PauseMenu(self.switch_state)
        self.task_menu = PlayerTask(self.switch_state, self.level)
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
            self.switch_state, self.player, self.increment_round
        )
        self.outgroup_menu = OutgroupMenu(
            self.player,
            self.switch_state,
        )

        # dialog
        self.all_sprites = AllSprites()
        self.dialogue_manager = DialogueManager(self.all_sprites)

        # screens
        self.menus = {
            GameState.MAIN_MENU: self.main_menu,
            GameState.PAUSE: self.pause_menu,
            GameState.SETTINGS: self.settings_menu,
            GameState.SHOP: self.shop_menu,
            GameState.INVENTORY: self.inventory_menu,
            GameState.PLAYER_TASK: self.task_menu,
            GameState.ROUND_END: self.round_menu,
            GameState.OUTGROUP_MENU: self.outgroup_menu,
        }
        self.current_state = GameState.MAIN_MENU
        self.next_state = GameState.MAIN_MENU

        # intro to in-group msg.
        self.intro_txt_shown = False

    def set_round(self, round):
        self.round = round

    def increment_round(self):
        if self.round < 12:
            self.round += 1

    def switch_state(self, state: GameState):
        self.next_state = state
        if self.next_state == GameState.SAVE_AND_RESUME:
            self.save_file.set_soil_data(*self.level.soil_manager.all_soil_sprites())
            self.level.player.save()
            self.next_state = GameState.PLAY
        if self.next_state == GameState.INVENTORY:
            self.inventory_menu.refresh_buttons_content()
        if self.next_state == GameState.ROUND_END:
            self.round_menu.reset_menu()
            self.round_menu.generate_items()
        if self.game_will_pause():
            self.player.blocked = True
            self.player.direction.update((0, 0))
        else:
            self.player.blocked = False

    def load_assets(self):
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

        setup_entity_assets()

        setup_gui()

        # sounds
        self.sounds = support.sound_importer("audio", default_volume=0.25)

        self.font = support.import_font(30, "font/LycheeSoda.ttf")

    def game_paused(self):
        """:return: Whether the game is currently paused"""
        return self.current_state != GameState.PLAY

    def game_will_pause(self):
        """:return: Whether the game will pause on the next frame"""
        return not self.game_paused() and self.next_state != GameState.PLAY

    def show_intro_msg(self):
        # A Message At The Starting Of The Game Giving Introduction To InGroup.
        if not self.intro_txt_shown:
            if not self.game_paused():
                self.dialogue_manager.open_dialogue(dial="intro_to_ingroup")
                self.intro_txt_shown = True

    # events
    def event_loop(self):
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
        if event.type == OPEN_INVENTORY:
            self.switch_state(GameState.INVENTORY)
            return True
        elif event.type == DIALOG_SHOW:
            if self.dialogue_manager.showing_dialogue:
                pass
            else:
                self.dialogue_manager.open_dialogue(event.dial)
                self.player.blocked = True
                self.player.direction.update((0, 0))
            return True
        elif event.type == DIALOG_ADVANCE:
            if self.dialogue_manager.showing_dialogue:
                self.dialogue_manager.advance()
                if not self.dialogue_manager.showing_dialogue:
                    self.player.blocked = False
            return True
        return False

    async def run(self):
        pygame.mouse.set_visible(False)
        mouse = pygame.image.load(support.resource_path("images/ui/Cursor.png"))
        is_first_frame = True
        while self.running:
            dt = self.clock.tick() / 1000

            self.event_loop()
            if not self.game_paused() or is_first_frame:
                if self.level.cutscene_animation.active:
                    event = pygame.key.get_pressed()
                    if event[pygame.K_RSHIFT]:
                        self.level.update(dt * 5, self.current_state == GameState.PLAY)
                    else:
                        self.level.update(dt, self.current_state == GameState.PLAY)
                else:
                    self.level.update(dt, self.current_state == GameState.PLAY)

            if self.game_paused() and not is_first_frame:
                self.display_surface.blit(self.previous_frame, (0, 0))
                self.menus[self.current_state].update(dt)
            else:
                self.round_end_timer += dt
                if self.round_end_timer > self.ROUND_END_TIME_IN_MINUTES * 60:
                    self.round_end_timer = 0
                    self.switch_state(GameState.ROUND_END)

            if self.level.cutscene_animation.active:
                self.all_sprites.update_blocked(dt)
                if self.current_state == GameState.PLAY:
                    event = pygame.key.get_pressed()
                    self.fast_forward.draw_option(self.display_surface)
                    if event[pygame.K_RSHIFT]:
                        self.fast_forward.draw_overlay(self.display_surface)
            else:
                self.all_sprites.update(dt)
            self.all_sprites.draw(self.level.camera, self.level.player.rect.center)

            # Apply blur effect only if the player has goggles equipped
            if self.player.has_goggles and self.current_state == GameState.PLAY:
                surface = pygame.transform.box_blur(self.display_surface, 2)
                self.display_surface.blit(surface, (0, 0))

            self.show_intro_msg()
            mouse_pos = pygame.mouse.get_pos()
            if self.game_will_pause() or is_first_frame:
                self.previous_frame = self.display_surface.copy()
            self.display_surface.blit(mouse, mouse_pos)
            is_first_frame = False
            self.current_state = self.next_state
            pygame.display.update()
            await asyncio.sleep(0)


if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())
