import datetime
import json
import typing
from pathlib import Path

from retro_data_structures.game_check import Game

import pwime.version
from pwime.asset_manager import OurAssetManager, Providers
from pwime.operations import serializer
from pwime.operations.base import Operation


class PerformedOperation(typing.NamedTuple):
    operation: Operation
    moment: datetime.datetime


class Project:
    name: str
    asset_manager: OurAssetManager
    performed_operations: list[PerformedOperation]

    def __init__(self, name: str, manager: OurAssetManager):
        self.name = name
        self.asset_manager = manager
        self.performed_operations = []
        self._threshold_to_overwrite = datetime.timedelta(minutes=1)

    def add_new_operation(self, operation: Operation) -> None:
        """Performs the operation and records it, ensuring we can undo it later and is persisted."""

        now = datetime.datetime.now()
        if self.performed_operations:
            last_op = self.performed_operations[-1]
            if now - last_op.moment < self._threshold_to_overwrite and operation.overwrites_operation(
                    last_op.operation
            ):
                last_op.operation.undo(self)
                self.performed_operations.pop()

        operation.perform(self)
        self.performed_operations.append(PerformedOperation(operation, now))

    def save_to_file(self, path: Path) -> None:
        data = {
            "schema_version": 1,
            "pwime_version": {
                "name": pwime.version.__version__,
            },
            "project_name": self.name,
            "game": self.asset_manager.target_game.value,
            "operations": [
                {
                    "time": operation.moment.astimezone(datetime.UTC).isoformat(),
                    "data": operation.operation.to_json(),
                }
                for operation in self.performed_operations
            ]
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=4))

    @classmethod
    def load_from_file(cls, path: Path, providers: Providers) -> typing.Self:
        with path.open() as file:
            data = json.load(file)

        game = Game(data["game"])
        manager = OurAssetManager(providers[game], game)

        result = cls(data["project_name"], manager)
        for op in data["operations"]:
            result.performed_operations.append(PerformedOperation(
                serializer.decode_from_json(op["data"]),
                datetime.datetime.fromisoformat(op["time"])
            ))
            result.performed_operations[-1].operation.perform(result)

        return result

