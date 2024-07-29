import pygame

from src import support
from src.gui.interface import dialog, emotes, indicators


def setup_gui():
    # region Dialog
    _tb_base = pygame.image.load(
        support.resource_path("images/textbox.png")
    ).convert_alpha()
    tb_cname_base_surf = _tb_base.subsurface(pygame.Rect(0, 0, 212, 67))
    tb_main_text_base_surf = _tb_base.subsurface(pygame.Rect(0, 74, 391, 202))

    dialog.prepare_tb_image(tb_cname_base_surf, tb_main_text_base_surf)
    # endregion

    # region Emotes
    emote_dialog_box = pygame.image.load(
        support.resource_path("images/ui/dialog_boxes/tiny_down.png")
    ).convert_alpha()
    emote_dialog_box = emote_dialog_box.subsurface(pygame.Rect(8, 8, 32, 32))
    emote_dialog_box = pygame.transform.scale(
        emote_dialog_box, (32 * 3, 32 * 3)
    )
    emotes.EmoteBox.EMOTE_DIALOG_BOX = emote_dialog_box

    entity_focus_indicator = pygame.image.load(
        support.resource_path("images/ui/indicators/entity_focused.png")
    ).convert_alpha()
    entity_focus_indicator = pygame.transform.scale(
        entity_focus_indicator, (entity_focus_indicator.width * 2,
                                 entity_focus_indicator.height * 2))
    indicators.ENTITY_FOCUSED = entity_focus_indicator
    # endregion
