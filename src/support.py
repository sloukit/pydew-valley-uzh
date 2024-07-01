import sys
from os import path, sep, walk, listdir
from os.path import join


from .settings import (
    pygame,
    SCALE_FACTOR,
    load_pygame,
    TILE_SIZE,
    CHAR_TILE_SIZE,
    MapDict,
    AniFrames,
    SoundDict
)


def resource_path(relative_path: str):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    relative_path = relative_path.replace("/", sep)
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = path.dirname(path.abspath(sys.argv[0]))
    return path.join(base_path, relative_path)


def import_font(size: int, font_path: str) -> pygame.font.Font: # Might be changed later on if we use pygame.freetype instead
    return pygame.font.Font(resource_path(font_path), size)


def import_image(img_path: str, alpha: bool = True) -> pygame.Surface:
    full_path = resource_path(img_path)
    surf = pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()
    return pygame.transform.scale_by(surf, SCALE_FACTOR)


def import_folder(fold_path: str) -> list[pygame.Surface]:
    frames = []
    for folder_path, _, file_names in walk(resource_path(fold_path)):
        for file_name in sorted(file_names, key=lambda name: int(name.split('.')[0])):
            full_path = join(folder_path, file_name)
            frames.append(pygame.transform.scale_by(pygame.image.load(full_path).convert_alpha(), SCALE_FACTOR))
    return frames


def import_folder_dict(fold_path: str) -> dict[str, pygame.Surface]:
    frames = {}
    for folder_path, _, file_names in walk(resource_path(fold_path)):
        for file_name in file_names:
            full_path = join(folder_path, file_name)
            frames[file_name.split('.')[0]] = pygame.transform.scale_by(pygame.image.load(full_path).convert_alpha(),
                                                                        SCALE_FACTOR)
    return frames


def tmx_importer(tmx_path: str) -> MapDict:
    files = {}
    for folder_path, _, file_names in walk(resource_path(tmx_path)):
        for file_name in file_names:
            full_path = join(folder_path, file_name)
            files[file_name.split('.')[0]] = load_pygame(full_path)
    return files


def animation_importer(*ani_path: str) -> dict[str, AniFrames]:
    animation_dict = {}
    for folder_path, _, file_names in walk(join(*ani_path)):
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


def single_character_importer(*sc_path: str) -> AniFrames:
    char_dict = {}
    full_path = join(*sc_path)
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


def character_importer(chr_path: str) -> dict[str, AniFrames]:
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


def sound_importer(*snd_path: str, default_volume: float = 0.5) -> SoundDict:
    sounds_dict = {}

    for sound_name in listdir(resource_path(join(*snd_path))):
        key = sound_name.split('.')[0]
        value = pygame.mixer.Sound(join(*snd_path, sound_name))
        value.set_volume(default_volume)
        sounds_dict[key] = value
    return sounds_dict


def generate_particle_surf(img: pygame.Surface) -> pygame.Surface:
    px_mask = pygame.mask.from_surface(img)
    ret = px_mask.to_surface()
    ret.set_colorkey("black")
    return ret
