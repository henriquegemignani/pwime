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
        """Reverts what `perform` did. Assumes no other changes were made afterward."""
        raise NotImplementedError

    def to_json(self) -> JsonObject:
        """Serializes this operation to a Json."""
        raise NotImplementedError
