import datetime
import json
import typing
from pathlib import Path

import pwime.version
from pwime.asset_manager import OurAssetManager
from pwime.operations import serializer
from pwime.operations.base import Operation


class PerformedOperation(typing.NamedTuple):
    operation: Operation
    moment: datetime.datetime


class Project:
    asset_manager: OurAssetManager
    performed_operations: list[PerformedOperation]

    def __init__(self, manager: OurAssetManager):
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
            "operations": [
                {
                    "time": operation.moment.astimezone(datetime.UTC).isoformat(),
                    "data": operation.operation.to_json(),
                }
                for operation in self.performed_operations
            ]
        }
        path.write_text(json.dumps(data, indent=4))

    @classmethod
    def load_from_file(cls, manager: OurAssetManager, path: Path) -> typing.Self:
        with path.open() as file:
            data = json.load(file)

        result = cls(manager)
        for op in data["operations"]:
            result.performed_operations.append(PerformedOperation(
                serializer.decode_from_json(op["data"]),
                datetime.datetime.fromisoformat(op["time"])
            ))

        return result

