# /// script
# dependencies = [
#  "pygame-ce",
#  "pytmx",
#  "pathfinding",
# ]
# ///

import asyncio
import sys

import pygame

from src import support
from src.enums import GameState
from src.events import DIALOG_ADVANCE, DIALOG_SHOW, OPEN_INVENTORY
from src.groups import AllSprites
from src.gui.interface.dialog import DialogueManager
from src.gui.setup import setup_gui
from src.savefile import SaveFile
from src.screens.inventory import InventoryMenu, prepare_checkmark_for_buttons
from src.screens.level import Level
from src.screens.menu_main import MainMenu
from src.screens.menu_pause import PauseMenu
from src.screens.menu_settings import SettingsMenu
from src.screens.shop import ShopMenu
from src.screens.switch_to_outgroup_menu import OutgroupMenu
from src.settings import (
    EMOTE_SIZE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    AniFrames,
    MapDict,
    SoundDict,
)
from src.sprites.setup import setup_entity_assets

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
        self.overlay_frames: dict[str, pygame.Surface] | None = None
        self.cosmetic_frames: dict[str, pygame.Surface] = {}
        self.frames: dict[str, dict] | None = None

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

        # screens
        self.level = Level(
            self.switch_state, self.tmx_maps, self.frames, self.sounds, self.save_file
        )
        self.player = self.level.player

        self.token_status = False
        self.main_menu = MainMenu(self.switch_state, self.set_token_status)
        self.pause_menu = PauseMenu(self.switch_state, self.set_token_status)
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
        self.outgroup_menu = OutgroupMenu(self.player, self.switch_state)

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
            GameState.OUTGROUP_MENU: self.outgroup_menu,
        }
        self.current_state = GameState.MAIN_MENU

    def set_token_status(self, status: bool):
        """Update the token status."""
        self.token_status = status

    def switch_state(self, state: GameState):
        self.current_state = state
        if self.current_state == GameState.SAVE_AND_RESUME:
            self.save_file.set_soil_data(*self.level.soil_manager.all_soil_sprites())
            self.level.player.save()
            self.current_state = GameState.PLAY
        if self.current_state == GameState.INVENTORY:
            self.inventory_menu.refresh_buttons_content()
        if self.game_paused():
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
            "animations": support.animation_importer("images", "animations"),
            "soil": support.import_folder_dict("images/soil"),
            "soil water": support.import_folder_dict("images/soil water"),
            "tomato": support.import_folder("images/plants/tomato"),
            "corn": support.import_folder("images/plants/corn"),
            "rain drops": support.import_folder("images/rain/drops"),
            "rain floor": support.import_folder("images/rain/floor"),
            "objects": support.import_folder_dict("images/objects"),
            "drops": support.import_folder_dict("images/drops"),
        }
        self.overlay_frames = support.import_folder_dict("images/overlay")
        cosmetic_surf = pygame.image.load(
            support.resource_path("images/cosmetics.png")
        ).convert_alpha()
        for cosmetic in _COSMETICS:
            self.cosmetic_frames[cosmetic] = pygame.transform.scale_by(
                cosmetic_surf.subsurface(_COSMETIC_SUBSURF_AREAS[cosmetic]),
                _COSMETIC_SCALE_FACTORS[cosmetic],
            )
        self.frames = {
            "emotes": self.emotes,
            "level": self.level_frames,
            "overlay": self.overlay_frames,
            "cosmetics": self.cosmetic_frames,
            "checkmark": pygame.transform.scale_by(
                pygame.image.load(
                    support.resource_path("images/checkmark.png")
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
        return self.current_state != GameState.PLAY

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
        is_first_frame = True
        while self.running:
            dt = self.clock.tick() / 1000

            self.event_loop()
            if not self.game_paused() or is_first_frame:
                self.level.update(dt, self.current_state == GameState.PLAY)
                is_first_frame = False
            if self.game_paused():
                self.menus[self.current_state].update(dt)

            if self.level.cutscene_animation.active:
                self.all_sprites.update_blocked(dt)
            else:
                self.all_sprites.update(dt)
            self.all_sprites.draw(self.level.camera)

            # Apply blur effect only if the player has goggles equipped
            if self.player.has_goggles and self.current_state == GameState.PLAY:
                surface = pygame.transform.box_blur(self.display_surface, 2)
                self.display_surface.blit(surface, (0, 0))

            pygame.display.update()
            await asyncio.sleep(0)


if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())
