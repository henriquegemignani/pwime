from __future__ import annotations

import dataclasses
import functools
from typing import TYPE_CHECKING

from retro_data_structures.asset_manager import IsoFileProvider
from retro_data_structures.game_check import Game

from pwime.gui.asset_manager import OurAssetManager

if TYPE_CHECKING:
    from pathlib import Path

    from imgui_bundle import portable_file_dialogs

    from pwime.gui.mlvl import MlvlState
    from pwime.gui.area import AreaState
    from pwime.gui.script_instance import ScriptInstanceState


@dataclasses.dataclass()
class GuiState:
    mlvl_state: MlvlState
    area_state: AreaState
    instance_state: ScriptInstanceState
    asset_manager: OurAssetManager | None = None
    global_file_list: tuple[int, ...] = ()
    open_file_dialog: portable_file_dialogs.open_file = None
    selected_asset: int | None = None
    reset_docks: bool = False

    def load_iso(self, path: Path):
        self.asset_manager = OurAssetManager(IsoFileProvider(path), Game.ECHOES)

        global_file_types = {
            "MLVL",
        }
        self.global_file_list = tuple(
            i for i in self.asset_manager.all_asset_ids() if self.asset_manager.get_asset_type(i) in global_file_types
        )


@functools.cache
def state() -> GuiState:
    from pwime.gui.mlvl import MlvlState
    from pwime.gui.area import AreaState
    from pwime.gui.script_instance import ScriptInstanceState
    return GuiState(MlvlState(), AreaState(), ScriptInstanceState())
