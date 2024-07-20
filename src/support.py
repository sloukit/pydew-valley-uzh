import os
import pygame
import pytmx
import sys
from src import settings
from src.settings import (
    CHAR_TILE_SIZE,
    SCALE_FACTOR,
    TILE_SIZE,
)
import json


def resource_path(relative_path: str):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    relative_path = relative_path.replace("/", os.sep)
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_path, relative_path)


# Might be changed later on if we use pygame.freetype instead
def import_font(size: int, font_path: str) -> pygame.font.Font:
    return pygame.font.Font(resource_path(font_path), size)


def import_image(img_path: str, alpha: bool = True) -> pygame.Surface:
    full_path = resource_path(img_path)
    surf = pygame.image.load(full_path).convert_alpha(
    ) if alpha else pygame.image.load(full_path).convert()
    return pygame.transform.scale_by(surf, SCALE_FACTOR)


def import_folder(fold_path: str) -> list[pygame.Surface]:
    frames = []
    for folder_path, _, file_names in os.walk(resource_path(fold_path)):
        for file_name in sorted(
            file_names, key=lambda name: int(
                name.split('.')[0])):
            full_path = os.path.join(folder_path, file_name)
            frames.append(pygame.transform.scale_by(
                pygame.image.load(full_path).convert_alpha(), SCALE_FACTOR))
    return frames


def import_folder_dict(fold_path: str) -> dict[str, pygame.Surface]:
    frames = {}
    for folder_path, _, file_names in os.walk(resource_path(fold_path)):
        for file_name in file_names:
            full_path = os.path.join(folder_path, file_name)
            frames[file_name.split('.')[0]] = pygame.transform.scale_by(
                pygame.image.load(full_path).convert_alpha(), SCALE_FACTOR)
    return frames


def tmx_importer(tmx_path: str) -> settings.MapDict:
    files = {}
    for folder_path, _, file_names in os.walk(resource_path(tmx_path)):
        for file_name in file_names:
            full_path = os.path.join(folder_path, file_name)
            files[file_name.split('.')[0]] = (
                pytmx.util_pygame.load_pygame(full_path)
            )
    return files


def animation_importer(*ani_path: str) -> dict[str, settings.AniFrames]:
    animation_dict = {}
    for folder_path, _, file_names in os.walk(os.path.join(*ani_path)):
        for file_name in file_names:
            full_path = os.path.join(folder_path, file_name)
            surf = pygame.image.load(full_path).convert_alpha()
            animation_dict[file_name.split('.')[0]] = []
            for col in range(surf.get_width() // TILE_SIZE):
                cutout_surf = pygame.Surface(
                    (TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                cutout_rect = pygame.Rect(
                    col * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE)
                cutout_surf.blit(surf, (0, 0), cutout_rect)
                animation_dict[file_name.split('.')[0]].append(
                    pygame.transform.scale_by(cutout_surf, SCALE_FACTOR))
    return animation_dict


def single_character_importer(*sc_path: str) -> settings.AniFrames:
    char_dict = {}
    full_path = os.path.join(*sc_path)
    surf = pygame.image.load(full_path).convert_alpha()
    for row, dirct in enumerate(['down', 'up', 'left']):
        char_dict[dirct] = []
        for col in range(surf.get_width() // CHAR_TILE_SIZE):
            cutout_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
            cutout_rect = pygame.Rect(
                col * CHAR_TILE_SIZE,
                row * CHAR_TILE_SIZE,
                CHAR_TILE_SIZE,
                CHAR_TILE_SIZE)
            cutout_surf.blit(surf, (0, 0), cutout_rect)
            char_dict[dirct].append(
                pygame.transform.scale_by(cutout_surf, SCALE_FACTOR))
    char_dict['right'] = [pygame.transform.flip(
        surf, True, False) for surf in char_dict['left']]
    return char_dict


def character_importer(chr_path: str) -> dict[str, settings.AniFrames]:
    # create dict with subfolders
    for _, sub_folders, _ in os.walk(resource_path(chr_path)):
        if sub_folders:
            char_dict = {folder: {} for folder in sub_folders}

    # go through all images and use single_character_importer to get the frames
    for char, frame_dict in char_dict.items():
        for folder_path, sub_folders, file_names in os.walk(
                os.path.join(resource_path(chr_path), char)):
            for file_name in file_names:
                char_dict[char][file_name.split('.')[0]] = (
                    single_character_importer(
                        os.path.join(folder_path, file_name)
                    )
                )
    return char_dict


def sound_importer(
        *snd_path: str,
        default_volume: float = 0.5
        ) -> settings.SoundDict:
    sounds_dict = {}

    for sound_name in os.listdir(resource_path(os.path.join(*snd_path))):
        key = sound_name.split('.')[0]
        value = pygame.mixer.Sound(os.path.join(*snd_path, sound_name))
        value.set_volume(default_volume)
        sounds_dict[key] = value
    return sounds_dict


def save_data(data, file_name):
    folder_path = resource_path('data/settings')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    with open(resource_path('data/settings/' + file_name), 'w') as file:
        json.dump(data, file, indent=4)


def load_data(file_name):
    with open(resource_path('data/settings/' + file_name), 'r') as file:
        return json.load(file)


def generate_particle_surf(img: pygame.Surface) -> pygame.Surface:
    px_mask = pygame.mask.from_surface(img)
    ret = px_mask.to_surface()
    ret.set_colorkey("black")
    return ret


def flip_items(d: dict) -> dict:
    """Returns a copy of d with key-value pairs flipped
    (i.e. keys become values and vice-versa)."""
    ret = {}
    for key, val in d.items():
        ret[val] = key
    return ret


def tile_to_screen(pos):
    tile_size = TILE_SIZE * SCALE_FACTOR
    return pos[0] * tile_size, pos[1] * tile_size


def screen_to_tile(pos):
    tile_size = TILE_SIZE * SCALE_FACTOR
    return pos[0] // tile_size, pos[1] // tile_size
