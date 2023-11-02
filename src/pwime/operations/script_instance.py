from __future__ import annotations

import dataclasses
import typing

from retro_data_structures.formats.mlvl import Mlvl
from retro_data_structures.formats.script_object import InstanceId
from retro_data_structures.properties import field_reflection
from retro_data_structures.properties.base_property import BaseObjectType, BaseProperty
from retro_data_structures.properties.echoes import objects

from pwime.operations.base import Operation

if typing.TYPE_CHECKING:
    from retro_data_structures.formats.script_object import ScriptInstance

    from pwime.asset_manager import OurAssetManager
    from pwime.project import Project
    from pwime.util.json_lib import JsonObject


@dataclasses.dataclass(frozen=True)
class InstanceReference:
    mlvl: int
    mrea: int
    instance_id: InstanceId

    def to_json(self) -> JsonObject:
        return {
            "mlvl": self.mlvl,
            "mrea": self.mrea,
            "instance_id": self.instance_id,
        }

    @classmethod
    def from_json(cls, data: JsonObject) -> typing.Self:
        data_json = typing.cast(dict[str, int], data)
        return cls(data_json["mlvl"], data_json["mrea"], InstanceId(data["instance_id"]))


@dataclasses.dataclass(frozen=True)
class PropReference:
    instance: InstanceReference
    path: tuple[str, ...]

    def append(self, field: str) -> PropReference:
        return PropReference(self.instance, self.path + (field,))


def get_instance(manager: OurAssetManager, reference: InstanceReference) -> ScriptInstance:
    """Gets a ScriptInstance from a InstanceReference"""
    mlvl = manager.get_file(reference.mlvl, Mlvl)
    area = mlvl.get_area(reference.mrea)
    return area.get_instance(reference.instance_id)


PropType = typing.TypeVar("PropType", bound=BaseObjectType)


def _modified_fields(prop: type[BaseProperty], delta: JsonObject, parent: str = "") -> list[str]:
    result = []

    for name, reflection in field_reflection.get_reflection(prop).items():
        key = f"0x{reflection.id:08X}"
        if key not in delta:
            continue

        if issubclass(reflection.type, BaseProperty) and field_reflection.get_reflection(reflection.type):
            result.extend(_modified_fields(reflection.type, delta[key], f"{parent}{name}."))
        else:
            result.append(f"{parent}{name}")

    return result


def create_patch_for(instance: ScriptInstance, value_path: tuple[str, ...], new_value: typing.Any) -> JsonObject:
    delta = {}
    current_type = instance.type
    current_value = delta

    for i, name in enumerate(value_path):
        reflection = field_reflection.get_reflection(current_type)[name]
        current_type = reflection.type
        key = f"0x{reflection.id:08X}"
        if i == len(value_path) - 1:
            current_value[key] = reflection.to_json(new_value)
        else:
            current_value[key] = {}
            current_value = current_value[key]

    return delta


def patch_property(prop: PropType, delta: JsonObject) -> None:
    for name, reflection in field_reflection.get_reflection(type(prop)).items():
        key = f"0x{reflection.id:08X}"
        if key not in delta:
            continue

        if issubclass(reflection.type, BaseProperty) and field_reflection.get_reflection(reflection.type):
            patch_property(getattr(prop, name), delta[key])
        else:
            setattr(prop, name, reflection.from_json(delta[key]))


class ScriptInstancePropertyEdit(Operation, typing.Generic[PropType]):
    """Represents changing a property of an existing script object."""

    reference: InstanceReference
    prop_type: type[PropType]
    delta: JsonObject
    old_value: PropType | None = None

    def __init__(self, reference: InstanceReference, prop_type: type[PropType], delta: JsonObject):
        self.reference = reference
        self.prop_type = prop_type
        self.delta = delta

    def perform(self, project: Project) -> None:
        """Performs the change."""
        instance = get_instance(project.asset_manager, self.reference)
        self.old_value = instance.get_properties()

        with instance.edit_properties(self.prop_type) as prop:
            patch_property(prop, self.delta)

    def undo(self, project: Project) -> None:
        """Reverts the change."""
        assert self.old_value is not None
        instance = get_instance(project.asset_manager, self.reference)
        instance.set_properties(self.old_value)

    def _modified_fields(self) -> list[str]:
        return _modified_fields(self.prop_type, self.delta)

    def overwrites_operation(self, operation: Operation) -> bool:
        """Yes if changing the same field of the same object."""
        if isinstance(operation, ScriptInstancePropertyEdit):
            if self.reference != operation.reference:
                return False
            return self._modified_fields() == operation._modified_fields()
        return False

    def describe(self) -> str:
        return (
            f"Edited fields {', '.join(self._modified_fields())} of `{self.reference.instance_id}`,"
            f" a {self.prop_type.__name__}"
        )

    def to_json(self) -> JsonObject:
        return {
            "kind": "script_instance_property_edit",
            "reference": self.reference.to_json(),
            "prop_type": self.prop_type.object_type(),
            "delta": self.delta,
        }

    @classmethod
    def from_json(cls, data: JsonObject) -> typing.Self:
        return cls(
            reference=InstanceReference.from_json(data["reference"]),
            prop_type=objects.get_object(data["prop_type"]),
            delta=data["delta"],
        )
