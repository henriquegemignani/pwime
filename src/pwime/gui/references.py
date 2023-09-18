from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    from retro_data_structures.formats.script_object import InstanceId


@dataclasses.dataclass(frozen=True)
class InstanceReference:
    mrea: int
    instance_id: InstanceId


@dataclasses.dataclass(frozen=True)
class PropReference:
    instance: InstanceReference
    path: tuple[str, ...]

    def append(self, field: str) -> typing.Self:
        return PropReference(self.instance, self.path + (field,))
