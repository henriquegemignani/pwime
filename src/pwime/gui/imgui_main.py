import argparse
import dataclasses
import functools
import typing
from pathlib import Path

from imgui_bundle import imgui, hello_imgui, immapp
from imgui_bundle.immapp import static
from imgui_bundle import portable_file_dialogs

from retro_data_structures.asset_manager import AssetManager, IsoFileProvider
from retro_data_structures.formats import Mlvl
from retro_data_structures.game_check import Game

_args: argparse.Namespace | None = None


@dataclasses.dataclass()
class GuiState:
    asset_manager: AssetManager | None = None
    mlvls: tuple[int, ...] = ()
    open_file_dialog: portable_file_dialogs.open_file = None


@static(state=GuiState())
def main_loop() -> None:
    state: GuiState = main_loop.state

    global _args
    if _args is not None:
        if _args.iso is not None:
            state.asset_manager = AssetManager(IsoFileProvider(_args.iso), Game.ECHOES)

        _args = None

    imgui.text_wrapped(
        f"""
Current FPS:  {hello_imgui.frame_rate():.1f}

Current manager: {state.asset_manager}
"""
    )

    if imgui.button("Open with ISO"):
        state.open_file_dialog = portable_file_dialogs.open_file("Select ISO", filters=["*.iso"])

    if state.open_file_dialog is not None and state.open_file_dialog.ready():
        files = state.open_file_dialog.result()
        if files:
            state.asset_manager = AssetManager(IsoFileProvider(Path(files[0])), Game.ECHOES)
            state.mlvls = tuple(i for i in state.asset_manager.all_asset_ids()
                                if state.asset_manager.get_asset_type(i) == "MLVL")
        state.open_file_dialog = None

    if state.asset_manager is not None:
        if imgui.begin_menu("Worlds"):
            for i in state.mlvls:
                if imgui.menu_item(f"{i:08x}", "", False):
                    print("YO")
            imgui.end_menu()


def run_gui(args: argparse.Namespace) -> None:
    global _args
    _args = args
    immapp.run(main_loop)
