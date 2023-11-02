from pwime.operations.base import Operation
from pwime.operations.script_instance import ScriptInstancePropertyEdit
from pwime.util.json_lib import JsonObject


def decode_from_json(data: JsonObject) -> Operation:
    match data["kind"]:
        case "script_instance_property_edit":
            return ScriptInstancePropertyEdit.from_json(data)
        case _:
            raise ValueError(f"Unknown kind: {data['kind']})")
