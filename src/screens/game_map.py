import copy
import warnings
from collections.abc import Callable
from typing import Any

import pygame
from pathfinding.core.grid import Grid  # type: ignore[import-untyped]
from pytmx import (  # type: ignore[import-untyped]
    TiledElement,
    TiledMap,
    TiledObject,
    TiledObjectGroup,
    TiledTileLayer,
)

from src.camera.camera_target import CameraTarget
from src.camera.zoom_area import ZoomArea
from src.camera.zoom_manager import ZoomManager
from src.enums import (
    Direction,
    FarmingTool,
    InventoryResource,
    Layer,
    Map,
    SpecialObjectLayer,
    StudyGroup,
)
from src.exceptions import GameMapWarning, InvalidMapError
from src.groups import AllSprites, PersistentSpriteGroup
from src.gui.interface.emotes import NPCEmoteManager, PlayerEmoteManager
from src.gui.scene_animation import SceneAnimation
from src.map_objects import MapObjects, MapObjectType
from src.npc.bases.animal import Animal
from src.npc.behaviour.chicken_behaviour_tree import (
    ChickenBehaviourTree,
    ChickenIndividualContext,
)
from src.npc.behaviour.cow_behaviour_tree import (
    CowConditionalBehaviourTree,
    # CowContinuousBehaviourTree,
    CowIndividualContext,
)
from src.npc.behaviour.npc_behaviour_tree import NPCBehaviourTree
from src.npc.chicken import Chicken
from src.npc.cow import Cow
from src.npc.npc import NPC
from src.npc.setup import AIData
from src.npc.utils import pf_add_matrix_collision
from src.overlay.soil import SoilManager
from src.savefile import SaveFile
from src.settings import (
    DEFAULT_ANIMATION_NAME,
    ENABLE_NPCS,
    SCALE_FACTOR,
    SCALED_TILE_SIZE,
    SETUP_PATHFINDING,
    TEST_ANIMALS,
)
from src.sprites.base import AnimatedSprite, CollideableMapObject, Sprite
from src.sprites.entities.character import Character
from src.sprites.entities.player import Player
from src.sprites.objects.berry_bush import BerryBush
from src.sprites.objects.tree import Tree
from src.sprites.setup import ENTITY_ASSETS
from src.support import parse_crop_types


def _setup_tile_layer(
    layer: TiledTileLayer, func: Callable[[tuple[int, int], pygame.Surface], None]
):
    """
    Calls func for each tile found in layer
    :param layer: TiledTileLayer
    :param func: function(pos, image)
    """
    for x, y, image in layer.tiles():
        x = x * SCALED_TILE_SIZE
        y = y * SCALED_TILE_SIZE
        pos = (x, y)
        func(pos, image)


def _setup_object_layer(
    layer: TiledObjectGroup, func: Callable[[tuple[float, float], TiledObject], Any]
):
    """
    Calls func for each tile found in layer
    :param layer: TiledTileLayer
    :param func: function(pos, object) -> object instance
    :return: All object instances
    """
    objects = []
    for obj in layer:
        x = obj.x * SCALE_FACTOR
        y = obj.y * SCALE_FACTOR
        pos = (x, y)
        objects.append(func(pos, obj))
    return objects


def _setup_animal_ranges(
    interaction_sprites: PersistentSpriteGroup, animals: list[Animal]
) -> None:
    if AIData.Matrix is None:
        raise InvalidMapError("AI Pathfinding Matrix is not defined")

    range_matrix_cows = [row.copy() for row in AIData.Matrix]
    range_matrix_chickens = [row.copy() for row in AIData.Matrix]

    for sprite in interaction_sprites:
        if sprite.name in ["L_RANGE_BLOCKAGE", "R_RANGE_BLOCKAGE"]:
            rect = sprite.rect
            pf_add_matrix_collision(
                range_matrix_cows,
                (rect.x / SCALE_FACTOR, rect.y / SCALE_FACTOR),
                (rect.width / SCALE_FACTOR, rect.height / SCALE_FACTOR),
            )
            pf_add_matrix_collision(
                range_matrix_chickens,
                (rect.x / SCALE_FACTOR, rect.y / SCALE_FACTOR),
                (rect.width / SCALE_FACTOR, rect.height / SCALE_FACTOR),
            )
        if sprite.name in ["L_BARN_BLOCKAGE", "R_BARN_BLOCKAGE"]:
            rect = sprite.rect
            pf_add_matrix_collision(
                range_matrix_chickens,
                (rect.x / SCALE_FACTOR, rect.y / SCALE_FACTOR),
                (rect.width / SCALE_FACTOR, rect.height / SCALE_FACTOR),
            )

    CowIndividualContext.range_grid = Grid(matrix=range_matrix_cows)
    ChickenIndividualContext.range_grid = Grid(matrix=range_matrix_chickens)


def _setup_camera_layer(layer: TiledObjectGroup):
    # BEWARE! THIS FUNCTION IS A GENERATOR!
    # DO NOT TRY TO USE THIS AS A LIST!
    """Sets up all camera targets for a cutscene using the layer objects."""

    targs = sorted(
        layer,
        key=lambda targ: (
            targ.properties.get("animation_name", DEFAULT_ANIMATION_NAME),
            targ.properties["targ_id"],
        ),
    )
    for target in targs:
        target_props = target.properties

        custom_properties = {}
        animation_name = target_props.get("animation_name")
        speed = target_props.get("speed")
        pause = target_props.get("pause")

        # Fields are private inside CameraTarget,
        # the only public access to them is through properties.
        # As CameraTarget is a dataclass, the parameters' names
        # in its generated __init__ match the field names
        # (i.e. there HAS to be an underscore when defining these keys
        # inside this additional keyword argument dictionary
        # or else when generating the CameraTarget object
        # Python will raise TypeErrors for unexpected arguments)
        if animation_name is not None:
            custom_properties["_animation_name"] = animation_name
        if speed is not None:
            custom_properties["_speed"] = speed
        if pause is not None:
            custom_properties["_pause"] = pause

        yield CameraTarget(
            (target.x * SCALE_FACTOR, target.y * SCALE_FACTOR),
            target_props["targ_id"],
            **custom_properties,
        )


def _setup_zoom_layer(layer: TiledObjectGroup):
    """Setup the zoom areas from an object group."""
    for area_id, obj in enumerate(layer):
        covered_surface = pygame.FRect(
            obj.x * SCALE_FACTOR,
            obj.y * SCALE_FACTOR,
            obj.width * SCALE_FACTOR,
            obj.height * SCALE_FACTOR,
        )

        speed_and_factor = {}
        obj_props = obj.properties
        speed = obj_props.get("speed")
        factor = obj_props.get("factor")

        # Fields are private inside ZoomArea,
        # the only public access to them is through properties.
        # As ZoomArea is a dataclass, the parameters' names
        # in its generated __init__ match the field names
        # (i.e. there HAS to be an underscore when defining these keys
        # inside this additional keyword argument dictionary
        # or else when generating the ZoomArea object
        # Python will raise TypeErrors for unexpected arguments)
        if speed is not None:
            speed_and_factor["_zoom_speed"] = speed
        if factor is not None:
            speed_and_factor["_zoom_factor"] = factor

        yield ZoomArea(area_id, covered_surface, **speed_and_factor)


def _get_element_property(
    element: TiledElement,
    property_name: str,
    callback: Callable[[str], Any],
    default: Any,
) -> Any:
    """
    :param element: Element to retrieve the property value from
    :param property_name: Name of the property
    :param callback: Function that should be called with the property value
                     retrieved from element
    :param default: Default value to return if callback raises an exception
    :return: Return value of callback
    """
    prop = element.properties.get("layer")
    if prop:
        try:
            return callback(prop)
        except Exception as e:
            warnings.warn(
                f"Property {property_name} with value {prop} is invalid for "
                f"map element {element}. Full error: {e}\n",
                GameMapWarning,
            )

    if prop is None:
        return default


class GameMap:
    """
    Class representing a single game map

    Attributes:
        _tilemap: loaded map as pytmx.TiledMap
        _tilemap_size: size of the current map (tile-scale)
        _tilemap_scaled_size: size of the current map (pixel-scale)

        _map_objects: Objects that have been loaded with custom hitboxes
                      TODO: This should probably be reworked to only load on
                       game start, as all maps are loaded on game start as well

        _pf_matrix: pathfinding matrix

        player_spawnpoint: default spawnpoint for the player
        player_entry_warps: warps where the player should enter the map,
                            depending on which map they came from
        player_exit_warps: hitboxes where the player should exit the map on
                           collision

        npcs: list of all NPCs on the map
        animals: list of all Animals on the map
    """

    _tilemap: TiledMap
    _tilemap_size: tuple[int, int]
    _tilemap_scaled_size: tuple[int, int]

    _map_objects: MapObjects

    minigame_layer: TiledObjectGroup | None

    # pathfinding
    _pf_matrix: list[list[int]]

    # map warp points
    player_spawnpoint: tuple[int, int] | None
    player_entry_warps: dict[str, tuple[int, int]]
    player_exit_warps: pygame.sprite.Group

    # non-player entities
    npcs: list[NPC]
    animals: list[Animal]

    round_config: dict[str, Any]

    def __init__(
        self,
        selected_map: Map,
        tilemap: TiledMap,
        save_file: SaveFile,
        scene_ani: SceneAnimation,
        zoom_man: ZoomManager,
        # Sprite groups
        all_sprites: AllSprites,
        collision_sprites: PersistentSpriteGroup,
        interaction_sprites: PersistentSpriteGroup,
        tree_sprites: PersistentSpriteGroup,
        bush_sprites: PersistentSpriteGroup,
        player_exit_warps: pygame.sprite.Group,
        # Player instance
        player: Player,
        # Emote manager instances
        player_emote_manager: PlayerEmoteManager,
        npc_emote_manager: NPCEmoteManager,
        # SoilLayer and Tool applying function for farming NPCs
        soil_manager: SoilManager,
        apply_tool: Callable[[FarmingTool, tuple[float, float], Character], None],
        plant_collision: Callable[[Character], None],
        # assets
        frames: dict,
        round_config: dict[str, Any],
        get_game_version: Callable[[], int],
    ):
        self.get_game_version = get_game_version
        self.number_of_hats_to_exclude = 2
        self._tilemap = tilemap

        if "Player" not in self._tilemap.layernames:
            raise InvalidMapError("No Player layer could be found")

        self.player_exit_warps = player_exit_warps

        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.interaction_sprites = interaction_sprites
        self.tree_sprites = tree_sprites
        self.bush_sprites = bush_sprites

        self.player = player

        self.player_emote_manager = player_emote_manager
        self.npc_emote_manager = npc_emote_manager

        self.soil_manager = soil_manager
        self.apply_tool = apply_tool
        self.plant_collision = plant_collision

        self.frames = frames
        self.round_config = round_config

        self._tilemap_size = (self._tilemap.width, self._tilemap.height)
        self._tilemap_scaled_size = (
            self._tilemap_size[0] * SCALED_TILE_SIZE,
            self._tilemap_size[1] * SCALED_TILE_SIZE,
        )

        # pathfinding
        self._pf_matrix = [
            [1 for _ in range(self._tilemap_size[0])]
            for _ in range(self._tilemap_size[1])
            if SETUP_PATHFINDING
        ]

        self._map_objects = MapObjects(self._tilemap)

        self.minigame_layer = None

        self.player_spawnpoint = None
        self.player_entry_warps = {}

        self.npcs = []
        self.animals = []

        self._setup_layers(save_file, selected_map, scene_ani, zoom_man)

        if selected_map == Map.MINIGAME and not self.round_config.get(
            "minigame_rooting_npcs", False
        ):
            self.npcs = []

        if SETUP_PATHFINDING:
            AIData.update(self._pf_matrix, self.player, [*self.npcs, *self.animals])

            if ENABLE_NPCS:
                self._setup_emote_interactions()
                _setup_animal_ranges(self.interaction_sprites, self.animals)

    def round_config_changed(self, round_config: dict[str, Any]) -> None:
        self.round_config = round_config
        self.process_npc_round_config()

    def process_npc_round_config(self):
        crop_types_list = self.round_config.get("crop_types_list", [])
        allowed_seeds = parse_crop_types(
            crop_types_list,
            include_base_allowed_crops=False,
            include_crops=False,
            include_seeds=True,
        )

        self.number_of_hats_to_exclude = 2
        for npc in self.npcs:
            npc.set_sickness_allowed(self.round_config.get("sickness", False))
            npc.set_allowed_seeds(allowed_seeds)
            npc.assign_outfit_ingroup(
                self.round_config.get("ingroup_40p_hat_necklace_appearance", False)
            )
            self.exclude_hat_if_possible(npc)

    @property
    def size(self):
        return self._tilemap_scaled_size

    # region tile layer setup methods
    def _setup_base_tile(
        self,
        pos: tuple[int, int],
        surf: pygame.Surface,
        layer: Layer,
        groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
    ):
        """
        Create a new Sprite and add it to the given groups
        :param pos: Position of the Sprite (x, y)
        :param surf: Surface that will be scaled up by SCALE_FACTOR and serve
                     as image for the Sprite
        :param layer: z-Layer on which the Sprite should be displayed
        :param groups: Groups the Sprite should be added to
        """
        image = pygame.transform.scale_by(surf, SCALE_FACTOR)
        Sprite(pos, image, z=layer).add(groups)

    def _setup_collideable_tile(
        self,
        pos: tuple[int, int],
        surf: pygame.Surface,
        layer: Layer,
        groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
    ):
        """
        Set up a base tile, and add it as collideable Tile to the pathfinding
        matrix
        """
        self._setup_base_tile(pos, surf, layer, groups)

        if SETUP_PATHFINDING:
            pf_add_matrix_collision(
                self._pf_matrix,
                (pos[0] / SCALE_FACTOR, pos[1] / SCALE_FACTOR),
                surf.get_size(),
            )

    def _setup_water_tile(
        self,
        pos: tuple[int, int],
        groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
    ):
        """
        Create a new AnimatedSprite and add it to the given groups.
        This Sprite will be animated as Water and displayed on Layer.WATER
        :param pos: Position of Sprite (x, y)
        :param groups: Groups the Sprite should be added to
        """
        image = self.frames["level"]["animations"]["water"]
        AnimatedSprite(pos, image, z=Layer.WATER).add(groups)

    # endregion

    # region object layer setup methods
    def _setup_base_object(
        self,
        pos: tuple[int, int],
        obj: TiledObject,
        layer: Layer,
        groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
        name: str = None,
    ):
        """
        Create a new rectangular hitbox and add it to the given groups.
        :param pos: Position of the hitbox Sprite (x, y)
        :param obj: TiledObject from which the hitbox should be created
        :param layer: z-Layer on which the Sprite should be displayed
                      TODO: Should likely be removed / reworked since hitboxes
                       should not be displayed at all
        :param groups: Groups the Sprite should be added to
        :param name: [Optional] name of the Sprite
        """
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        Sprite(pos, image, z=layer, name=name, custom_properties=obj.properties).add(
            groups
        )

    def _setup_collision_rect(
        self,
        pos: tuple[int, int],
        obj: TiledObject,
        layer: Layer,
        groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group,
        name: str = None,
    ):
        """
        Set up a base object and add it as collideable object to the
        pathfinding matrix
        """
        size = (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
        image = pygame.Surface(size)
        Sprite(pos, image, z=layer, name=name).add(groups)

        if SETUP_PATHFINDING:
            pf_add_matrix_collision(
                self._pf_matrix, (obj.x, obj.y), (obj.width, obj.height)
            )

    def _setup_tree(
        self, pos: tuple[int, int], obj: TiledObject, object_type: MapObjectType
    ):
        props = obj.properties
        if props.get("size") == "medium" and props.get("breakable"):
            fruit = props.get("fruit_type")
            if fruit == "no_fruit":
                fruit_type, fruit_frames = None, None
            else:
                fruit_type = InventoryResource.from_serialised_string(fruit)
                fruit_frames = self.frames["level"]["objects"][fruit]
            stump_frames = self.frames["level"]["objects"]["stump"]

            tree = Tree(
                pos,
                object_type,
                (self.all_sprites, self.collision_sprites, self.tree_sprites),
                obj.name,
                fruit_frames,
                fruit_type,
                stump_frames,
            )
            # we need a tree surf without fruits
            tree.image = self.frames["level"]["objects"]["tree"]
            tree.surf = tree.image
        else:
            CollideableMapObject(pos, object_type, z=Layer.MAIN).add(
                self.all_sprites,
                self.collision_sprites,
            )

    def _setup_bush(
        self, pos: tuple[int, int], obj: TiledObject, object_type: MapObjectType
    ):
        props = obj.properties
        if props.get("size") == "medium":
            fruit = props.get("fruit_type")
            if fruit == "no_fruit":
                fruit_type, fruit_frames = None, None
            else:
                fruit_type = InventoryResource.from_serialised_string(fruit)
                fruit_frames = self.frames["level"]["objects"][fruit]

            bush = BerryBush(
                pos,
                object_type,
                (
                    self.all_sprites,
                    self.collision_sprites,
                    self.bush_sprites,
                    self.interaction_sprites,
                ),
                obj.name,
                fruit_frames,
                fruit_type,
            )
            # we need a bush surf without fruits
            bush.image = self.frames["level"]["objects"]["bush_medium"]
            bush.surf = bush.image
        else:
            CollideableMapObject(pos, object_type, z=Layer.MAIN).add(
                self.all_sprites,
                self.collision_sprites,
            )

    def _setup_map_object(
        self,
        pos: tuple[int, int],
        obj: TiledObject,
        layer: Layer,
    ):
        """
        Create a new collideable Sprite from the given TiledObject.
        If the value of the object's "type" property equals "tree", this Sprite will be
        created from the Tree class and will take its assets from self.frames
        :param pos: Position of Sprite (x, y)
        :param obj: TiledObject to create the Sprite from
        :param layer: z-Layer on which the Sprite should be displayed
                      (Trees will always be rendered on Layer.MAIN)
        """
        object_type = self._map_objects.get(obj.gid)
        props = obj.properties

        if object_type.hitbox is not None:
            if props.get("type") == "tree":
                self._setup_tree(pos, obj, object_type)
            elif props.get("type") == "bush":
                self._setup_bush(pos, obj, object_type)

            else:
                if props.get("type") == "hidden_sign":
                    # layer = Layer.HIDDEN_SIGN
                    name = "hidden_sign"
                else:
                    name = None

                if object_type.hitbox is not None:
                    CollideableMapObject(pos, object_type, z=layer, name=name).add(
                        self.all_sprites,
                        self.collision_sprites,
                    )

            if SETUP_PATHFINDING:
                pf_add_matrix_collision(
                    self._pf_matrix,
                    (
                        obj.x + object_type.hitbox.x / SCALE_FACTOR,
                        obj.y + object_type.hitbox.y / SCALE_FACTOR,
                    ),
                    (
                        object_type.hitbox.width / SCALE_FACTOR,
                        object_type.hitbox.height / SCALE_FACTOR,
                    ),
                )
        else:
            surf = pygame.transform.scale_by(object_type.image, SCALE_FACTOR)
            Sprite(pos, surf, z=layer).add(self.all_sprites)

    def _setup_player_warp(self, pos: tuple[int, int], obj: TiledObject):
        """
        Add a new Player warp point.
        The type of the warp will be retrieved from the object's name.

        The default spawnpoint should be named "spawnpoint", and warp
        destination points should be named "from " + map name (without .tmx),
        e.g. a warp point used when warping from forest should be named
        "from forest". Warp origins should be defined as rectangular
        objects that warp the player when colliding with them. They should
        be named "to " + map name (without .tmx), e.g. a warp point that
        will be used when warping to farm_new should be named
        "to farm_new".

        :param pos: Position of the warp
        :param obj: TiledObject to create the warp from
        """
        name = obj.name
        player_group = self.player.study_group
        spawnpoint_group = player_group
        if len(name.split(" ")) == 2:
            spawnpoint_group = obj.name.split(" ")[1]
            if spawnpoint_group == "ingroup":
                spawnpoint_group = StudyGroup.INGROUP
            if spawnpoint_group == "outgroup":
                spawnpoint_group = StudyGroup.OUTGROUP

        if "spawnpoint" in name and (player_group == spawnpoint_group):
            if self.player_spawnpoint:
                warnings.warn(
                    f"Multiple spawnpoints found ({self.player_spawnpoint}, {pos})",
                    GameMapWarning,
                )
            self.player_spawnpoint = pos
        else:
            name = name.split(" ")
            if len(name) == 2:
                warp_type = name[0]
                warp_map = name[1]
                if warp_type == "from":
                    self.player_entry_warps[warp_map] = pos
                elif warp_type == "to":
                    warp_hitbox = pygame.Surface(
                        (obj.width * SCALE_FACTOR, obj.height * SCALE_FACTOR)
                    )
                    Sprite(
                        (obj.x * SCALE_FACTOR, obj.y * SCALE_FACTOR),
                        warp_hitbox,
                        name=warp_map,
                    ).add(self.player_exit_warps)
                else:
                    warnings.warn(f'Invalid player warp "{name}"', GameMapWarning)
            else:
                warnings.warn(f'Invalid player warp "{name}"', GameMapWarning)

    def _setup_npc(self, pos: tuple[int, int], obj: TiledObject, gmap: Map):
        """
        Creates a new NPC sprite at the given position

        TODO: The NPCs study_group attribute currently only limits their farming area,
         but does not restrict the NPC from moving into another groups farming area.
         Although this should only happen if every single Tile of the NPCs designated
         farming area is planted and watered, we should keep this in mind and perhaps
         actually restrict its movable area, or make sure that a day does not last long
         enough after a farming area has been fully watered.
        """

        if gmap == Map.MINIGAME and not self.round_config.get(
            "minigame_rooting_npcs", False
        ):
            return None

        features = obj.properties.get("features")
        has_hat = False
        has_necklace = False
        if features:
            if "hat" in features:
                has_hat = True
            if "necklace" in features:
                has_necklace = True

        study_group = StudyGroup.NO_GROUP
        group = obj.properties.get("group")
        if group is None:
            warnings.warn(
                f"NPC with ID {obj.id} has no group assigned to it", GameMapWarning
            )
        else:
            try:
                study_group = StudyGroup[group]
            except KeyError:
                warnings.warn(
                    f"NPC with ID {obj.id} has an invalid group '{group}' assigned to "
                    f"it",
                    GameMapWarning,
                )

        npc = NPC(
            pos=pos,
            assets=copy.deepcopy(ENTITY_ASSETS.RABBIT),
            groups=(self.all_sprites, self.collision_sprites),
            collision_sprites=self.collision_sprites,
            study_group=study_group,
            apply_tool=self.apply_tool,
            plant_collision=self.plant_collision,
            soil_manager=self.soil_manager,
            emote_manager=self.npc_emote_manager,
            tree_sprites=self.tree_sprites,
            sickness_allowed=self.round_config.get("sickness", False),
            has_hat=has_hat,
            has_necklace=has_necklace,
            special_features=features,
            npc_id=obj.id,
        )
        npc.teleport(pos)
        # Ingroup NPCs wearing only the hat and no necklace should not be able to walk on the forest and town map,
        # only on the farming map
        no_walking_npc = (
            (
                gmap != Map.FARM
                and npc.study_group == StudyGroup.INGROUP
                and not npc.has_necklace
                and npc.has_hat
                and gmap != Map.MINIGAME
            )
            or gmap == Map.MINIGAME
            and obj.name
            and obj.name == "opponent"
        )
        if gmap == Map.MINIGAME and obj.name and obj.name == "opponent":
            if npc.study_group == self.player.study_group:
                npc.kill()
        if gmap == Map.MINIGAME:
            npc.probability_to_get_sick = 1

        cheering = gmap == Map.MINIGAME

        behaviour = obj.properties.get("behaviour")
        if behaviour != "Woodcutting" and gmap == Map.NEW_FARM:
            npc.conditional_behaviour_tree = NPCBehaviourTree.Farming
        elif no_walking_npc:
            npc.conditional_behaviour_tree = NPCBehaviourTree.DoNothing
        elif cheering:
            npc.conditional_behaviour_tree = NPCBehaviourTree.Cheer
            if npc.study_group == StudyGroup.INGROUP:
                npc.facing_direction = Direction.RIGHT
            if npc.study_group == StudyGroup.OUTGROUP:
                npc.facing_direction = Direction.LEFT
        else:
            npc.conditional_behaviour_tree = NPCBehaviourTree.Woodcutting
        return npc

    def _setup_animal(self, pos: tuple[int, int], obj: TiledObject):
        """
        Creates a new Animal sprite at the given position.
        The animal type is determined by the object name, objects named
        "Chicken" will create Chickens, objects that are named "Cow" will
        create Cows.
        """
        animal: Cow | Chicken | None = None
        if obj.name == "Chicken":
            animal = Chicken(
                pos=pos,
                assets=ENTITY_ASSETS.CHICKEN,
                groups=(self.all_sprites, self.collision_sprites),
                collision_sprites=self.collision_sprites,
            )
            animal.conditional_behaviour_tree = ChickenBehaviourTree.Wander
        elif obj.name == "Cow":
            animal = Cow(
                pos=pos,
                assets=ENTITY_ASSETS.COW,
                groups=(self.all_sprites, self.collision_sprites),
                collision_sprites=self.collision_sprites,
            )
            animal.conditional_behaviour_tree = CowConditionalBehaviourTree.Wander
            # animal.continuous_behaviour_tree = CowContinuousBehaviourTree.Flee

        if animal is not None:
            animal.teleport(pos)
            return animal
        else:
            warnings.warn(
                f'Malformed animal object name "{obj.name}" in tilemap', GameMapWarning
            )

    # endregion

    def _setup_layers(
        self,
        save_file: SaveFile,
        gmap: Map,
        scene_ani: SceneAnimation,
        zoom_man: ZoomManager,
    ):
        """
        Iterates over all map layers, updates the GameMap state and creates
        all Sprites for the map.
        """

        # We clear the target data first so that the cutscene from the previous
        # room doesn't play again if the current one
        # doesn't have any camera targets
        scene_ani.reset()
        scene_ani.clear()

        # Clearing the zoom manager in advance, in case no zoom areas exist for the current map
        zoom_man.clear()

        for tilemap_layer in self._tilemap.layers:
            if isinstance(tilemap_layer, TiledTileLayer):
                # create soil layer
                if tilemap_layer.name == "farmable_ingroup":
                    self.soil_manager.load_area(
                        StudyGroup.INGROUP, tilemap_layer, save_file.soil_data
                    )
                    continue
                elif tilemap_layer.name == "farmable_outgroup":
                    self.soil_manager.load_area(
                        StudyGroup.OUTGROUP, tilemap_layer, save_file.soil_data
                    )
                    continue
                elif tilemap_layer.name == "Border":
                    _setup_tile_layer(
                        tilemap_layer,
                        lambda pos, image: self._setup_collideable_tile(
                            pos,
                            image,
                            Layer.BORDER,
                            (
                                self.all_sprites,
                                self.collision_sprites,
                            ),
                        ),
                    )
                    continue

                # create tile layers
                # set layer if defined in the TileLayer properties
                layer = _get_element_property(
                    element=tilemap_layer,
                    property_name="layer",
                    callback=lambda prop: Layer[prop],
                    default=Layer.GROUND,
                )

                if layer == Layer.WATER:
                    # tiles on the WATER layer will always be created as water
                    _setup_tile_layer(
                        tilemap_layer,
                        lambda pos, _: self._setup_water_tile(pos, self.all_sprites),
                    )
                else:
                    # decorative and ground tiles will be created as base tile
                    _setup_tile_layer(
                        tilemap_layer,
                        lambda pos, image: self._setup_base_tile(
                            pos,
                            image,
                            layer,  # noqa: B023 # TODO: Fix B023 to avoid potential UnboundLocalError
                            self.all_sprites,
                        ),
                    )

            elif isinstance(tilemap_layer, TiledObjectGroup):
                match tilemap_layer.name:
                    case SpecialObjectLayer.MINIGAME:
                        self.minigame_layer = tilemap_layer
                    case SpecialObjectLayer.INTERACTIONS:
                        _setup_object_layer(
                            tilemap_layer,
                            lambda pos, obj: self._setup_base_object(
                                pos,
                                obj,
                                Layer.MAIN,
                                self.interaction_sprites,
                                name=obj.name,
                            ),
                        )
                    case SpecialObjectLayer.COLLISIONS:
                        _setup_object_layer(
                            tilemap_layer,
                            lambda pos, obj: self._setup_collision_rect(
                                pos, obj, Layer.MAIN, self.collision_sprites
                            ),
                        )
                    case SpecialObjectLayer.PLAYER:
                        _setup_object_layer(
                            tilemap_layer,
                            lambda pos, obj: self._setup_player_warp(pos, obj),
                        )

                        if not self.player_entry_warps and not self.player_spawnpoint:
                            raise InvalidMapError(
                                "No Player warp point could be found in the map's "
                                "Player layer"
                            )
                    case SpecialObjectLayer.NPCS:
                        if not ENABLE_NPCS:
                            continue
                        self.npcs = _setup_object_layer(
                            tilemap_layer,
                            lambda pos, obj: self._setup_npc(pos, obj, gmap),
                        )
                    case SpecialObjectLayer.ANIMALS:
                        if not TEST_ANIMALS:
                            continue
                        self.animals = _setup_object_layer(
                            tilemap_layer, lambda pos, obj: self._setup_animal(pos, obj)
                        )
                    case SpecialObjectLayer.CAMERA_TARGETS:
                        scene_ani.set_target_points(_setup_camera_layer(tilemap_layer))
                    case SpecialObjectLayer.ZOOM_AREAS:
                        zoom_man.set_zoom_areas(_setup_zoom_layer(tilemap_layer))
                    case _:
                        # set layer if defined in the TileLayer properties
                        layer = _get_element_property(
                            tilemap_layer, "layer", lambda prop: Layer[prop], Layer.MAIN
                        )

                        # decorative objects will be created as collideable object
                        _setup_object_layer(
                            tilemap_layer,
                            lambda pos, obj, obj_layer=layer: self._setup_map_object(
                                pos,
                                obj,
                                obj_layer,
                            ),
                        )

            else:
                # This should be the case when an Image or Group layer is found
                warnings.warn(
                    f"Support for {tilemap_layer.__class__.__name__} layers is not (yet) "
                    f"implemented! Layer {tilemap_layer.name} will be skipped",
                    GameMapWarning,
                )

    def _setup_emote_interactions(self):
        self.player_emote_manager.reset()

        @self.player_emote_manager.on_show_emote
        def on_show_emote(emote: str):
            if self.player.focused_entity:
                npc = self.player.focused_entity
                npc.abort_path()

                self.npc_emote_manager.show_emote(npc, emote)

                # check if the player achieved task "interact with an ingroup member" or "interact
                # with an outgroup member"
                payload = {}
                payload["emote_index"] = (
                    self.player_emote_manager.emote_wheel.emote_index
                )
                payload["emote_name"] = self.player_emote_manager.emote_wheel._emotes[
                    payload["emote_index"]
                ]
                payload["player_pos"] = ", ".join(
                    str(round(v)) for v in self.player.rect.topleft
                )
                payload["npc_pos"] = ", ".join(str(round(v)) for v in npc.rect.topleft)

                if self.player.study_group == npc.study_group:
                    self.player.ingroup_member_interacted = True
                    payload["emote_target"] = "ingroup"
                else:
                    self.player.outgroup_member_interacted = True
                    payload["emote_target"] = "outgroup"

                self.player.send_telemetry("player_interaction", payload)

        @self.player_emote_manager.on_emote_wheel_opened
        def on_emote_wheel_opened():
            player_pos = self.player.rect.center
            distance_to_player = 5 * SCALED_TILE_SIZE
            npc_to_focus = None
            for npc in self.npcs:
                current_distance = (
                    (player_pos[0] - npc.rect.center[0]) ** 2
                    + (player_pos[1] - npc.rect.center[1]) ** 2
                ) ** 0.5
                if current_distance < distance_to_player:
                    distance_to_player = current_distance
                    npc_to_focus = npc
            if npc_to_focus:
                self.player.focus_entity(npc_to_focus)

        @self.player_emote_manager.on_emote_wheel_closed
        def on_emote_wheel_closed():
            self.player.unfocus_entity()

    def get_size(self):
        return self._tilemap_scaled_size

    def exclude_hat_if_possible(self, npc: NPC):
        # in version 3 of the game we remove all hat and necklaces for npcs with special features added in the map
        if self.get_game_version() == 3:
            if npc.study_group == StudyGroup.INGROUP and npc.npc_id in [368, 372]:
                npc.has_hat = False
                npc.has_necklace = False
        # in version 1 and 2 of the game we remove hats for two npcs without special features
        elif self.get_game_version() in [1, 2]:
            if (
                npc.npc_id not in [368, 372]
                and npc.has_hat
                and self.number_of_hats_to_exclude > 0
            ):
                npc.has_hat = False
                npc.has_necklace = False
                self.number_of_hats_to_exclude -= 1
