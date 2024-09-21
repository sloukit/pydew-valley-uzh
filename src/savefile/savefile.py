import json
from itertools import chain

import pygame

from src.enums import FarmingTool, InventoryResource, SeedType, StudyGroup
from src.savefile.tile_info import PlantInfo, TileInfo
from src.settings import Coordinate, GogglesStatus
from src.support import resource_path
from src import utils

_NONSEED_INVENTORY_DEFAULT_AMOUNT = 20
_SEED_INVENTORY_DEFAULT_AMOUNT = 5
_INV_DEFAULT_AMOUNTS = (
    _NONSEED_INVENTORY_DEFAULT_AMOUNT,
    _SEED_INVENTORY_DEFAULT_AMOUNT,
)
CONVERT_TO_FT = "__FarmingTool__"
CONVERT_TO_IR = "__InventoryResource__"


def _as_farmingtool(o: dict):
    if CONVERT_TO_FT in o:
        ret = o.copy()
        del ret[CONVERT_TO_FT]
        keys = set(ret.keys())
        for k in keys:
            if k in o[CONVERT_TO_FT]:
                ret[k] = FarmingTool.from_serialised_string(o[k])
        return ret
    return o


def _as_inventoryresource(o: dict):
    if CONVERT_TO_IR in o:
        ret = o.copy()
        del ret[CONVERT_TO_IR]
        keys = set(ret.keys())
        for k in keys:
            if k in o[CONVERT_TO_IR]:
                ret[InventoryResource.from_serialised_string(k)] = o[k]
        return ret
    return o


def _extract_group(o: dict):
    if "group" in o:
        ret = o.copy()
        ret["group"] = StudyGroup(ret["group"])
        return ret
    return o


def _extract_tile_info(o: dict):
    if "soil_data" in o:
        ret = o.copy()
        orig_soil_data = ret["soil_data"]
        converted_data = {}
        for info in orig_soil_data:
            plant_info_orig = info.get("plant_info")
            if plant_info_orig is not None:
                new_plant_info = PlantInfo(
                    SeedType(plant_info_orig["plant_type"]), plant_info_orig["age"]
                )
            else:
                new_plant_info = None
            is_watered = info.get("watered", False)
            pos = tuple(info["pos"])
            converted_data[pos] = TileInfo(is_watered, pos, new_plant_info)
        ret["soil_data"] = converted_data
        return ret
    return o


def _decoder_object_hook(o):
    processed = _as_farmingtool(o)
    processed = _as_inventoryresource(processed)
    processed = _extract_group(processed)
    processed = _extract_tile_info(processed)
    return processed


def _load_internal():
    with open(resource_path("data/save.json"), "r") as file:
        return utils.json_loads(file.read(), object_hook=_decoder_object_hook)


class SaveFile:
    _has_goggles: GogglesStatus
    _study_group: StudyGroup
    _current_tool: FarmingTool
    _current_seed: FarmingTool
    _money: int
    inventory: dict[InventoryResource, int]
    _soil_data: dict[Coordinate, TileInfo]

    def __init__(
        self,
        current_tool: FarmingTool,
        current_seed: FarmingTool,
        inventory: dict[InventoryResource, int],
        group: StudyGroup,
        goggles_status: GogglesStatus,
        money: int = 200,
        soil_data: dict[Coordinate, TileInfo] | None = None,
    ):
        self._current_tool = current_tool
        self._current_seed = current_seed
        self._money = money
        self.inventory = {
            res: inventory.get(
                res.as_serialised_string(),
                _SEED_INVENTORY_DEFAULT_AMOUNT
                if res >= InventoryResource.CORN_SEED
                else _NONSEED_INVENTORY_DEFAULT_AMOUNT,
            )
            for res in InventoryResource.__members__.values()
        }
        self.study_group = group
        self.has_goggles = goggles_status
        self._soil_data = soil_data or {}

    @classmethod
    def load(cls):
        data = _load_internal()
        data.setdefault("group", StudyGroup.INGROUP)
        data.setdefault("goggles_status", None)
        data.setdefault("current_tool", FarmingTool.get_first_tool_id())
        data.setdefault("current_seed", FarmingTool.get_first_seed_id())
        return SaveFile(**data)

    def _jsonify_soil_data(self):
        return [tile_info.__json__() for tile_info in self.soil_data.values()]

    def save(self):
        with open(resource_path("data/save.json"), "w") as file:
            serialised_inventory = {
                k.as_serialised_string(): self.inventory[k] for k in self.inventory
            }
            keys_to_convert = list(serialised_inventory.keys())
            serialised_inventory[CONVERT_TO_IR] = keys_to_convert
            obj_to_dump = {
                CONVERT_TO_FT: ["current_tool", "current_seed"],
                "money": self.money,
                "current_tool": self.current_tool.as_serialised_string(),
                "current_seed": self.current_seed.as_serialised_string(),
                "group": self.study_group.value,
                "goggles_status": self.has_goggles,
                "inventory": serialised_inventory,
            }
            if self._soil_data:
                obj_to_dump["soil_data"] = self._jsonify_soil_data()
            json.dump(obj_to_dump, file, indent=2)

    @property
    def current_tool(self):
        return self._current_tool

    @current_tool.setter
    def current_tool(self, val: FarmingTool):
        if val.is_seed():
            raise ValueError("current_tool cannot be a seed")
        self._current_tool = val

    @property
    def current_seed(self):
        return self._current_seed

    @current_seed.setter
    def current_seed(self, val: FarmingTool):
        if not val.is_seed():
            raise ValueError("val must be a seed")
        self._current_seed = val

    @property
    def money(self):
        return self._money

    @money.setter
    def money(self, val: int):
        if val < 0:
            raise ValueError("money amount cannot be negative")
        self._money = val

    @property
    def soil_data(self):
        return self._soil_data

    def set_soil_data(self, *tile_groups: pygame.sprite.Group):
        new_data = {}
        for tile in chain(*tile_groups):
            if not tile.hoed:
                continue
            if tile.plant is not None:
                plant_info = PlantInfo(tile.plant.seed_type, tile.plant.age)
            else:
                plant_info = None
            new_data[tile.pos] = TileInfo(tile.watered, tile.pos, plant_info)
        self._soil_data = new_data
