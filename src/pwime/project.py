import datetime
import typing

from pwime.asset_manager import OurAssetManager
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
            if now - last_op.moment < self._threshold_to_overwrite and operation.overwrites_operation(last_op.operation):
                last_op.operation.undo(self)
                self.performed_operations.pop()

        operation.perform(self)
        self.performed_operations.append(PerformedOperation(operation, now))
