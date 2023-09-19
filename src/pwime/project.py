from pwime.asset_manager import OurAssetManager
from pwime.operations.base import Operation


class Project:
    asset_manager: OurAssetManager
    operations: list[Operation]

    def __init__(self, manager: OurAssetManager):
        self.asset_manager = manager
        self.operations = []

    def add_new_operation(self, operation: Operation) -> None:
        """Performs the operation and records it, ensuring we can undo it later and is persisted."""

        self.operations.append(operation)
        operation.perform(self)
