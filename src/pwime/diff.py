
import argparse
from pathlib import Path
from retro_data_structures.asset_manager import IsoFileProvider
from retro_data_structures.game_check import Game

from retro_data_structures.base_resource import (
    AssetId,
    RawResource,
)
import tqdm

from pwime.asset_manager import OurAssetManager


def run_cli(args: argparse.Namespace) -> None:
    base_iso: Path = args.base_iso
    target_iso: Path = args.target_iso

    base_manager = OurAssetManager(IsoFileProvider(base_iso), Game.ECHOES)
    target_manager = OurAssetManager(IsoFileProvider(target_iso), Game.ECHOES)

    different_ids: list[tuple[AssetId, RawResource, RawResource]] = []

    all_ids = list(base_manager.all_asset_ids())
    for asset_id in tqdm.tqdm(all_ids):
        base_raw = base_manager.get_raw_asset(asset_id)
        target_raw = target_manager.get_raw_asset(asset_id)
        if base_raw != target_raw:
            different_ids.append((asset_id, base_raw, target_raw))

    for asset_id, base_raw, target_raw in different_ids:
        print(f"Different asset: {asset_id:08x} ({base_raw.type})")
