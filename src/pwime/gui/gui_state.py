from __future__ import annotations

import dataclasses
from pathlib import Path

from imgui_bundle import portable_file_dialogs, hello_imgui
from retro_data_structures.asset_manager import IsoFileProvider
from retro_data_structures.game_check import Game

from pwime.gui.asset_manager import OurAssetManager


@dataclasses.dataclass()
class GuiState:
    asset_manager: OurAssetManager | None = None
    global_file_list: tuple[int, ...] = ()
    open_file_dialog: portable_file_dialogs.open_file = None
    selected_asset: int | None = None
    pending_new_docks: list[hello_imgui.DockableWindow] = dataclasses.field(default_factory=list)

    def load_iso(self, path: Path):
        self.asset_manager = OurAssetManager(IsoFileProvider(path), Game.ECHOES)

        global_file_types = {
            "MLVL",
        }
        self.global_file_list = tuple(
            i for i in self.asset_manager.all_asset_ids() if self.asset_manager.get_asset_type(i) in global_file_types
        )


state = GuiState()
