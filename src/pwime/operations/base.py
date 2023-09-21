from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pwime.project import Project
    from pwime.util.json_lib import JsonObject


class Operation(ABC):
    """Represents a change performed to the game files. These changes are reversible and can be persisted to disk."""

    def perform(self, project: Project) -> None:
        """Performs the change."""
        raise NotImplementedError

    def undo(self, project: Project) -> None:
        """Reverts what `perform` did. Assumes no other changes were made afterward.
        Can only be called after perform."""
        raise NotImplementedError

    def to_json(self) -> JsonObject:
        """Serializes this operation to a Json."""
        raise NotImplementedError

    def overwrites_operation(self, operation: Operation) -> bool:
        """True, if the results of this operation completely overwrites the results of given operation.
        For when the user quickly does similar actions in a row, such as changing the same field to multiple values."""
        raise NotImplementedError
