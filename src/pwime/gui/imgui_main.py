from __future__ import annotations

import typing
from pathlib import Path

from imgui_bundle import hello_imgui, imgui, immapp, portable_file_dialogs
from retro_data_structures.game_check import Game

from pwime.gui.gui_state import state

if typing.TYPE_CHECKING:
    import argparse


def main_gui() -> None:
    if state().asset_manager is not None:
        if imgui.begin_table("All Assets", 3, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h):
            imgui.table_setup_column("Type", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Asset Id", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Name")

            imgui.table_headers_row()

            for i in state().global_file_list:
                imgui.table_next_row()

                imgui.table_next_column()
                imgui.text(state().asset_manager.get_asset_type(i))

                imgui.table_next_column()
                if imgui.selectable(
                        f"{i:08X}",
                        False,
                        imgui.SelectableFlags_.span_all_columns | imgui.SelectableFlags_.allow_item_overlap,
                )[1]:
                    state().mlvl_state.open_mlvl(i)

                imgui.table_next_column()
                imgui.text_disabled(state().asset_manager.asset_names.get(i, "<unknown>"))

            imgui.end_table()
    else:
        imgui.text("No ISO loaded. Open one in the Projects menu above.")


def _show_menu() -> None:
    if imgui.begin_menu("Project"):
        if imgui.menu_item("Open ISO", "", False)[0]:
            state().open_file_dialog = portable_file_dialogs.open_file("Select ISO", filters=["*.iso"])
        imgui.end_menu()

    if state().open_file_dialog is not None and state().open_file_dialog.ready():
        files = state().open_file_dialog.result()
        if files:
            state().load_iso(Path(files[0]), Game.ECHOES)
        state().open_file_dialog = None

    imgui.text_disabled("Bai")


def _pre_new_frame() -> None:
    if state().pending_windows:
        params = hello_imgui.get_runner_params().docking_params
        params.dockable_windows = params.dockable_windows + state().pending_windows
        state().pending_windows = []


def run_gui(args: argparse.Namespace) -> None:
    if args.iso:
        state().load_iso(args.iso, args.game)

    runner_params = hello_imgui.RunnerParams()
    runner_params.callbacks.show_menus = _show_menu
    runner_params.callbacks.pre_new_frame = _pre_new_frame
    runner_params.app_window_params.window_title = "Prime World Interactive Media Editor"
    runner_params.imgui_window_params.show_menu_app = False
    runner_params.imgui_window_params.show_menu_bar = True
    runner_params.imgui_window_params.show_status_bar = True

    runner_params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
    )
    # In this demo, we also demonstrate multiple viewports.
    # you can drag windows outside out the main window in order to put their content into new native windows
    runner_params.imgui_window_params.enable_viewports = True

    #
    # Define our dockable windows : each window provide a Gui callback, and will be displayed
    # in a docking split.
    #
    dockable_windows: list[hello_imgui.DockableWindow] = []

    def add_dockable_window(label: str, demo_gui: typing.Callable[[], None]):
        window = hello_imgui.DockableWindow()
        window.label = label
        window.dock_space_name = "MainDockSpace"
        window.gui_function = demo_gui
        dockable_windows.append(window)

    add_dockable_window("File List", main_gui)
    dockable_windows.append(state().mlvl_state.create_imgui_window())
    dockable_windows.append(state().area_state.create_imgui_window())
    dockable_windows.append(state().instance_state.create_imgui_window())

    runner_params.docking_params.dockable_windows = dockable_windows

    runner_params.docking_params.docking_splits = [
        hello_imgui.DockingSplit(
            "MainDockSpace", "RightSpace", imgui.Dir_.right, 0.4
        )
    ]

    immapp.run(runner_params=runner_params)
