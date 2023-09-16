from __future__ import annotations

import typing

from retro_data_structures.asset_manager import AssetManager, FileProvider
from retro_data_structures.base_resource import BaseResource, NameOrAssetId
from retro_data_structures.game_check import Game

T = typing.TypeVar("T", bound=BaseResource)


class OurAssetManager(AssetManager):
    memory_files: dict[NameOrAssetId, BaseResource]

    def __init__(self, provider: FileProvider, target_game: Game):
        super().__init__(provider, target_game)
        self.memory_files = {}

    def get_file(self, path: NameOrAssetId, type_hint: type[T] = BaseResource) -> T:
        if path not in self.memory_files:
            self.memory_files[path] = self.get_parsed_asset(path, type_hint=type_hint)
        return self.memory_files[path]
