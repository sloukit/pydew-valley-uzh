import json
from .enums import InventoryResource, FarmingTool
from .support import resource_path
from jsmin import jsmin

CONVERT_TO_FT = "__FarmingTool__"
CONVERT_TO_IR = "__InventoryResource__"


def as_farmingtool(o: dict):
    if CONVERT_TO_FT in o:
        ret = o.copy()
        del ret[CONVERT_TO_FT]
        keys = set(ret.keys())
        for k in keys:
            if k in o[CONVERT_TO_FT]:
                ret[k] = FarmingTool.from_serialised_string(o[k])
        return ret
    return o


def as_inventoryresource(o: dict):
    if CONVERT_TO_IR in o:
        ret = o.copy()
        del ret[CONVERT_TO_IR]
        keys = set(ret.keys())
        for k in keys:
            if k in o[CONVERT_TO_IR]:
                ret[InventoryResource.from_serialised_string(k)] = o[k]
        return ret
    return o


def decoder_object_hook(o):
    processed = as_farmingtool(o)
    processed = as_inventoryresource(processed)
    return processed


def save(
    current_tool: FarmingTool,
    current_seed: FarmingTool,
    money: int,
    inventory: dict[InventoryResource, int],
):
    with open(resource_path("data/save.json"), "w") as file:
        serialised_inventory = {k.as_serialised_string(): inventory[k] for k in inventory}
        keys_to_convert = list(serialised_inventory.keys())
        serialised_inventory[CONVERT_TO_IR] = keys_to_convert
        obj_to_dump = {
            CONVERT_TO_FT: ["current_tool", "current_seed"],
            "money": money,
            "current_tool": current_tool.as_serialised_string(),
            "current_seed": current_seed.as_serialised_string(),
            "inventory": serialised_inventory
        }
        json.dump(obj_to_dump, file, indent=2)


def load_savefile():
    with open(resource_path("data/save.json"), "r") as file:
        return json.loads(jsmin(file.read()), object_hook=decoder_object_hook)
