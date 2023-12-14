from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor

import json
import typing
from pathlib import Path

from retro_data_structures.asset_manager import AssetManager, IsoFileProvider
from retro_data_structures.base_resource import AssetId, BaseResource, NameOrAssetId
from retro_data_structures.game_check import Game


T = typing.TypeVar("T", bound=BaseResource)


Providers: typing.TypeAlias = dict[Game, IsoFileProvider]


class OurAssetManager(AssetManager):
    provider: IsoFileProvider
    memory_files: dict[NameOrAssetId, BaseResource]
    asset_names: dict[AssetId, str]

    def __init__(self, provider: IsoFileProvider, target_game: Game):
        super().__init__(provider, target_game)
        self.memory_files = {}

        asset_names_path = Path(__file__).parent.joinpath("asset_names", f"{target_game.name}.json")
        try:
            with asset_names_path.open() as f:
                name_to_id: dict = json.load(f)

            self.asset_names = {asset_id: name for name, asset_id in name_to_id.items()}

        except FileNotFoundError:
            self.asset_names = {}

    def flush_modified_assets(self):
        with ThreadPoolExecutor() as executor:
            for name, resource in self.memory_files.items():
                executor.submit(self.replace_asset, name, resource)
        self.memory_files = {}

    def get_file(self, path: NameOrAssetId, type_hint: type[T] = BaseResource) -> T:
        if path not in self.memory_files:
            self.memory_files[path] = self.get_parsed_asset(path, type_hint=type_hint)
        return self.memory_files[path]
