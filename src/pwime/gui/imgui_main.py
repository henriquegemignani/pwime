from __future__ import annotations

import datetime
import typing
from pathlib import Path

import humanize
from imgui_bundle import hello_imgui, imgui, immapp, portable_file_dialogs
from retro_data_structures.game_check import Game

from pwime.gui.gui_state import state
from pwime.gui.popup import CurrentPopup
from pwime.gui.project_popup import NewProjectPopup
from pwime.util import imgui_helper

if typing.TYPE_CHECKING:
    import argparse


def main_gui() -> None:
    asset_manager = state().asset_manager
    if asset_manager is not None:
        if imgui.begin_table("All Assets", 3, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h):
            imgui.table_setup_column("Type", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Asset Id", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Name")

            imgui.table_headers_row()

            for i in state().global_file_list:
                imgui.table_next_row()

                imgui.table_next_column()
                imgui.text(asset_manager.get_asset_type(i))

                imgui.table_next_column()
                if imgui.selectable(
                        f"{i:08X}",
                        False,
                        imgui.SelectableFlags_.span_all_columns | imgui.SelectableFlags_.allow_item_overlap,
                )[1]:
                    state().mlvl_state.open_mlvl(i)

                imgui.table_next_column()
                imgui.text_disabled(asset_manager.asset_names.get(i, "<unknown>"))

            imgui.end_table()
    else:
        imgui.text("No ISO loaded. Open one in the Projects menu above.")


def render_history() -> None:
    project = state().project
    if project is not None:
        if imgui.begin_table(
                "History", 2, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h | imgui.TableFlags_.reorderable
        ):
            imgui.table_setup_column("When", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Action", imgui.TableColumnFlags_.width_fixed)

            imgui.table_headers_row()

            now = datetime.datetime.now()

            for op in project.performed_operations:
                imgui.table_next_row()

                imgui.table_next_column()
                imgui.text(humanize.naturaltime(op.moment, when=now))

                imgui.table_next_column()
                imgui.text(op.operation.describe())

            imgui.end_table()
    else:
        imgui.text("No project loaded.")


class SelectPrime2IsoPopup(CurrentPopup):
    def __init__(self):
        self.file_dialog = portable_file_dialogs.open_file("Select ISO", filters=["*.iso"])

    def render(self) -> bool:
        if self.file_dialog.ready():
            files = self.file_dialog.result()
            if files:
                path = Path(files[0])
                state().load_iso(path, Game.ECHOES)
                state().preferences.prime2_iso = path
                state().preferences.write_to_user_home()
            return False

        return True


def _show_menu() -> None:
    if imgui.begin_menu("Project"):
        if imgui.menu_item("New", "", False)[0]:
            state().current_popup = NewProjectPopup()

        if imgui.menu_item("Open existing", "", False)[0]:
            pass

        with imgui_helper.disabled(state().project is None):
            if imgui.menu_item("Save", "", False)[0]:
                state().project.save_to_file(state().current_project_path)

            if imgui.menu_item("Close", "", False)[0]:
                # TODO: confirm discarding changes
                state().project = None

        imgui.end_menu()

    if imgui.begin_menu("Preferences"):
        if imgui.menu_item("Metroid Prime 2 ISO", "", False)[0]:
            state().current_popup = SelectPrime2IsoPopup()
        imgui.end_menu()

    if state().current_popup is not None:
        if not state().current_popup.render():
            state().current_popup = None

    imgui.text_disabled("Bai")


def _pre_new_frame() -> None:
    pending_tasks = list(state().pending_pre_frame_tasks)
    state().pending_pre_frame_tasks.clear()

    for task in pending_tasks:
        task()


def focus_on_file_list() -> None:
    tries = 2

    def task():
        nonlocal tries
        window = hello_imgui.get_runner_params().docking_params.dockable_window_of_name("File List")
        window.focus_window_at_next_frame = True

        tries -= 1
        if tries > 0:
            state().pending_pre_frame_tasks.append(task)

    state().pending_pre_frame_tasks.append(task)


def run_gui(args: argparse.Namespace) -> None:
    state().preferences.read_from_user_home()

    if state().preferences.last_project_path:
        state().open_project(state().preferences.last_project_path)

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

    def add_dockable_window(label: str, gui_function: typing.Callable[[], None]) -> hello_imgui.DockableWindow:
        window = hello_imgui.DockableWindow()
        window.label = label
        window.dock_space_name = "MainDockSpace"
        window.gui_function = gui_function
        window.imgui_window_flags = imgui.WindowFlags_.no_bring_to_front_on_focus
        dockable_windows.append(window)
        return window

    add_dockable_window("File List", main_gui)
    dockable_windows.append(state().mlvl_state.create_imgui_window())
    dockable_windows.append(state().area_state.create_imgui_window())
    dockable_windows.append(state().instance_state.create_imgui_window())
    add_dockable_window("History", render_history).is_visible = False

    runner_params.docking_params.dockable_windows = dockable_windows

    runner_params.docking_params.docking_splits = [
        hello_imgui.DockingSplit("MainDockSpace", "RightSpace", imgui.Dir_.right, 0.4)
    ]

    focus_on_file_list()

    immapp.run(runner_params=runner_params)
