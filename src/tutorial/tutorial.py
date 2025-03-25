from typing import Any

import pygame

from src.enums import StudyGroup
from src.gui.interface.dialog import DialogueManager
from src.screens.level import Level
from src.settings import GAME_LANGUAGE, TUTORIAL_TB_LEFT, TUTORIAL_TB_TOP
from src.sprites.entities.player import Player


class Tutorial:
    """Tutorial object.
    This class will be used to display the tutorial section to the player.
    Notice: after completing the tutorial and saving the game,
            it will not be displayed after relaunching the game."""

    def __init__(
        self,
        sprite_group: pygame.sprite.Group,
        player: Player,
        level: Level,
        round_config: dict[str, Any],
    ):
        self.dialogue_manager = DialogueManager(
            sprite_group, f"data/textboxes/{GAME_LANGUAGE}/tutorial.json"
        )
        self.player = player
        self.level = level
        self.round_config = round_config
        self.game_version = 1

        # position of the tutorial text box
        self.left_pos = TUTORIAL_TB_LEFT
        self.top_pos = TUTORIAL_TB_TOP
        # check if the player moved in the four directions
        self.movement_axis = [0, 0, 0, 0]

        self.instructions = {
            0: self.move,
            1: self.interact_with_ingroup_member,
            2: self.farm_tile,
            3: self.plant_crop,
            4: self.water_crop,
            5: self.go_to_bed,
            6: self.go_to_forest_and_hit_tree,
            7: self.go_to_market_and_buy_sell_something_v1_v2,
            8: self.go_to_market_and_buy_sell_something_v3,
            9: self.go_to_minigame_map_and_play,
            10: self.interact_with_outgroup_member,
            11: self.walk_around_outgroup_farm_and_switch_to_outgroup,
        }
        self.tasks_achieved = -1
        self.n_tasks = max(self.instructions.keys()) + 1

    # show instructions text boxes

    def set_game_version(self, game_version: int):
        self.game_version = game_version

    def farm_tile(self):
        self.dialogue_manager.open_dialogue("Farm_tile", self.left_pos, self.top_pos)

    def get_hat_ingroup(self):
        self.dialogue_manager.open_dialogue(
            "Get_hat_from_ingroup", self.left_pos, self.top_pos
        )

    def get_necklace_ingroup(self):
        self.dialogue_manager.open_dialogue(
            "Get_necklace_from_ingroup", self.left_pos, self.top_pos
        )

    def go_to_bed(self):
        self.dialogue_manager.open_dialogue("Go_to_bed", self.left_pos, self.top_pos)

    def go_to_forest_and_hit_tree(self):
        self.dialogue_manager.open_dialogue(
            "Go_to_forest_and_hit_tree", self.left_pos, self.top_pos
        )

    def go_to_market_and_buy_sell_something_v1_v2(self):
        self.dialogue_manager.open_dialogue(
            "Go_to_market_and_buy/sell_something_v1v2", self.left_pos, self.top_pos
        )

    def go_to_market_and_buy_sell_something_v3(self):
        self.dialogue_manager.open_dialogue(
            "Go_to_market_and_buy/sell_something_v3", self.left_pos, self.top_pos
        )

    def go_to_minigame_map_and_play(self):
        self.dialogue_manager.open_dialogue(
            "Go_to_minigame_map_and_play", self.left_pos, self.top_pos
        )

    def move(self):
        self.dialogue_manager.open_dialogue(
            "Basic_movement", self.left_pos, self.top_pos
        )

    def interact_with_ingroup_member(self):
        self.dialogue_manager.open_dialogue(
            "Interact_with_ingroup_member", self.left_pos, self.top_pos
        )

    def interact_with_outgroup_member(self):
        self.dialogue_manager.open_dialogue(
            "Interact_with_outgroup_member", self.left_pos, self.top_pos
        )

    def plant_crop(self):
        self.dialogue_manager.open_dialogue("Plant_crop", self.left_pos, self.top_pos)

    def walk_around_outgroup_farm_and_switch_to_outgroup(self):
        self.dialogue_manager.open_dialogue(
            "Walk_around_outgroup_farm_and_switch_to_outgroup",
            self.left_pos,
            self.top_pos,
        )

    def water_crop(self):
        self.dialogue_manager.open_dialogue("Water_crop", self.left_pos, self.top_pos)

    def show_tutorial_end(self):
        self.dialogue_manager.advance()
        self.dialogue_manager.open_dialogue("Tutorial_end", self.left_pos, self.top_pos)

    def switch_to_task(self, index: int):
        if index < self.n_tasks:
            if len(self.dialogue_manager._tb_list):
                self.dialogue_manager.advance()
                self.instructions[index]()
            else:
                self.instructions[index]()

    def check_tasks(self, game_paused):
        match self.tasks_achieved:
            case -1:  # tutorial has not been started yet
                return
            case 0:
                # check if the player achieved task "Basic movement"
                if (
                    0 not in self.movement_axis
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    self.switch_to_task(1)
                    self.tasks_achieved += 1

                if self.player.direction.x < 0:
                    self.movement_axis[0] = self.player.direction.x
                elif self.player.direction.x > 0:
                    self.movement_axis[1] = self.player.direction.x
                if self.player.direction.y < 0:
                    self.movement_axis[2] = self.player.direction.y
                elif self.player.direction.y > 0:
                    self.movement_axis[3] = self.player.direction.y

            case 1:
                # check if the player achieved task "interact with an ingroup member"
                if (
                    self.dialogue_manager._get_current_tb().finished_advancing
                    and self.player.ingroup_member_interacted
                ):
                    self.switch_to_task(2)
                    self.tasks_achieved += 1

            case 2:
                # check if the player achieved task "farm with your hoe"
                if (
                    self.dialogue_manager._get_current_tb().finished_advancing
                    and self.level.tile_farmed
                ):
                    self.switch_to_task(3)
                    self.tasks_achieved += 1

            case 3:
                # check if the player achieved task "plant a crop"
                if (
                    self.level.crop_planted
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    self.switch_to_task(4)
                    self.tasks_achieved += 1

            case 4:
                # check if the player achieved task "water the crop"
                if (
                    self.level.crop_watered
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    self.switch_to_task(5)
                    self.tasks_achieved += 1

            case 5:
                # check if the player achieved task "go to bed"
                if (
                    self.level.had_slept
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    self.switch_to_task(6)
                    self.tasks_achieved += 1
            case 6:
                # check if the player achieved task "go to the forest and hit a tree"
                if (
                    self.level.hit_tree
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    if self.game_version in [1, 2]:
                        self.switch_to_task(7)
                        self.tasks_achieved += 1
                    else:
                        self.switch_to_task(8)
                        self.tasks_achieved += 1

            case 7:
                # check if the player achieved task "go to the marketplace and buy or sell something"
                if (
                    self.player.bought_sold
                    and not game_paused
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    if self.game_version in [1, 2]:
                        self.player.blocked_from_market = True
                    self.switch_to_task(9)
                    self.tasks_achieved += 1

            case 8:
                # check if the player achieved task "go to the marketplace and buy or sell something" in version 3
                if (
                    self.player.bought_sold
                    and not game_paused
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    self.switch_to_task(9)
                    self.tasks_achieved += 1

            case 9:
                # check if the player achieved task "go to the minigame area and play "
                if (
                    self.player.minigame_finished
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    self.switch_to_task(10)
                    self.tasks_achieved += 1

            case 10:
                # check if the player achieved task "interact with an outgroup member"
                if (
                    self.player.outgroup_member_interacted
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    if self.round_config.get("playable_outgroup", False):
                        self.switch_to_task(11)
                        self.tasks_achieved += 1

                        self.player.outgroup_member_interacted = False
                    else:
                        self.show_tutorial_end()
                        self.tasks_achieved = self.n_tasks
                        self.player.blocked = True

            case 11:
                # check if the player achieved task "walk around the outgroup farm and switch to the outgroup"
                if (
                    self.player.study_group == StudyGroup.OUTGROUP
                    and self.dialogue_manager._get_current_tb().finished_advancing
                ):
                    self.show_tutorial_end()
                    self.tasks_achieved += 1
                    self.player.blocked = True

            case self.n_tasks:  # wait for space pressed to end the tutorial
                # check if the player interacted to complete the tutorial
                if (
                    self.dialogue_manager._get_current_tb().finished_advancing
                    and self.player.controls.INTERACT.hold
                ):
                    self.deactivate()

    # run at the beginning of the tutorial
    def start(self):
        if self.tasks_achieved == -1:
            self.tasks_achieved = 0
        self.switch_to_task(self.tasks_achieved)

    def update(self, game_paused):
        self.check_tasks(game_paused)

    def deactivate(self):
        self.dialogue_manager.close_dialogue()
        self.player.blocked = False
        self.tasks_achieved = self.n_tasks
        self.level.player.save_file.is_tutorial_completed = True
