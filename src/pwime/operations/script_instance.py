from __future__ import annotations

import dataclasses
import typing

from retro_data_structures.formats import Mlvl

from pwime.asset_manager import OurAssetManager
from pwime.operations.base import Operation
from pwime.project import Project

if typing.TYPE_CHECKING:
    from retro_data_structures.formats.script_object import InstanceId, ScriptInstance


@dataclasses.dataclass(frozen=True)
class InstanceReference:
    mlvl: int
    mrea: int
    instance_id: InstanceId


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


PropType = typing.TypeVar("PropType")


class ScriptInstancePropertyEdit(Operation, typing.Generic[PropType]):
    """Represents changing a property of an existing script object."""

    reference: PropReference
    prop_type: type[PropType]
    new_value: object

    def __init__(self, reference: PropReference, prop_type: type[PropType], new_value: object):
        self.reference = reference
        self.prop_type = prop_type
        self.new_value = new_value

    def perform(self, project: Project) -> None:
        """Performs the change."""
        instance = get_instance(project.asset_manager, self.reference.instance)

        with instance.edit_properties(self.prop_type) as prop:
            for path in self.reference.path[:-1]:
                prop = getattr(prop, path)
            setattr(prop, self.reference.path[-1], self.new_value)
