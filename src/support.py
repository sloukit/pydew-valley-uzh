import json, pygame, sys
import os
from os import path, sep, walk, listdir
from os.path import join           
from pytmx.util_pygame import load_pygame          
from .settings import TILE_SIZE, CHAR_TILE_SIZE, SCALE_FACTOR


def resource_path(relative_path: str):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    relative_path = relative_path.replace("/", sep)
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = path.dirname(path.abspath(sys.argv[0]))
    return path.join(base_path, relative_path)


def import_font(size, font_path):
    return pygame.font.Font(resource_path(font_path), size)


def import_image(img_path, alpha=True):
    full_path = resource_path(img_path)
    surf = pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()
    return pygame.transform.scale_by(surf, SCALE_FACTOR)


def import_folder(fold_path):
    frames = []
    for folder_path, _, file_names in walk(resource_path(fold_path)):
        for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
            full_path = join(folder_path, file_name)
            frames.append(pygame.transform.scale_by(pygame.image.load(full_path).convert_alpha(), SCALE_FACTOR))
    return frames


def import_folder_dict(fold_path):
    frames = {}
    for folder_path, _, file_names in walk(resource_path(fold_path)):
        for file_name in file_names:
            full_path = join(folder_path, file_name)
            frames[file_name.split('.')[0]] = pygame.transform.scale_by(pygame.image.load(full_path).convert_alpha(),
                                                                        SCALE_FACTOR)
    return frames


def tmx_importer(tmx_path):
    files = {}
    for folder_path, _, file_names in walk(resource_path(tmx_path)):
        for file_name in file_names:
            full_path = join(folder_path, file_name)
            files[file_name.split('.')[0]] = load_pygame(full_path)
    return files


def animation_importer(*path):
    animation_dict = {}
    for folder_path, _, file_names in walk(join(*path)):
        for file_name in file_names:
            full_path = join(folder_path, file_name)
            surf = pygame.image.load(full_path).convert_alpha()
            animation_dict[file_name.split('.')[0]] = []
            for col in range(surf.get_width() // TILE_SIZE):
                cutout_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                cutout_rect = pygame.Rect(col * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE)
                cutout_surf.blit(surf, (0, 0), cutout_rect)
                animation_dict[file_name.split('.')[0]].append(pygame.transform.scale_by(cutout_surf, SCALE_FACTOR))
    return animation_dict


def single_character_importer(*path):
    char_dict = {}
    full_path = join(*path)
    surf = pygame.image.load(full_path).convert_alpha()
    for row, dir in enumerate(['down', 'up', 'left']):
        char_dict[dir] = []
        for col in range(surf.get_width() // CHAR_TILE_SIZE):
            cutout_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
            cutout_rect = pygame.Rect(col * CHAR_TILE_SIZE, row * CHAR_TILE_SIZE, CHAR_TILE_SIZE, CHAR_TILE_SIZE)
            cutout_surf.blit(surf, (0, 0), cutout_rect)
            char_dict[dir].append(pygame.transform.scale_by(cutout_surf, SCALE_FACTOR))
    char_dict['right'] = [pygame.transform.flip(surf, True, False) for surf in char_dict['left']]
    return char_dict


def character_importer(chr_path):
    # create dict with subfolders 
    for _, sub_folders, _ in walk(resource_path(chr_path)):
        if sub_folders:
            char_dict = {folder: {} for folder in sub_folders}

    # go through all images and use single_character_importer to get the frames
    for char, frame_dict in char_dict.items():
        for folder_path, sub_folders, file_names in walk(join(resource_path(chr_path), char)):
            for file_name in file_names:
                char_dict[char][file_name.split('.')[0]] = single_character_importer(join(folder_path, file_name))
    return char_dict


def sound_importer(*path, default_volume=0.5):
    sounds_dict = {}

    for sound_name in listdir(resource_path(join(*path))):
        key = sound_name.split('.')[0]
        value = pygame.mixer.Sound(join(*path, sound_name))
        value.set_volume(default_volume)
        sounds_dict[key] = value
    return sounds_dict


def save_data(data, file_name):
    folder_path = resource_path('data/settings')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = resource_path('data/settings/' + file_name)
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    
def load_data(file_name):
    file_path = resource_path('data/settings/' + file_name)
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as file:
        return json.load(file)
    
def map_coords_to_tile(pos):
    return (pos[0] // (TILE_SIZE * SCALE_FACTOR), pos[1] // (TILE_SIZE * SCALE_FACTOR))