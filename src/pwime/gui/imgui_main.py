from __future__ import annotations

import datetime
import logging
import os
import typing
from pathlib import Path

import humanize
from imgui_bundle import hello_imgui, imgui, immapp
from retro_data_structures.game_check import Game

from pwime.gui.gui_state import state
from pwime.gui.gui_tools import FilePrompt, IsoPrompt
from pwime.gui.popup import CurrentImguiPopup, ConfirmCancelActionPopup
from pwime.gui.project_popup import NewProjectPopup, validate_project_file
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
                        imgui.SelectableFlags_.span_all_columns,
                )[1]:
                    state().mlvl_state.open_mlvl(i)

                imgui.table_next_column()
                imgui.text_disabled(asset_manager.asset_names.get(i, "<unknown>"))

            imgui.end_table()
    else:
        imgui.text("No project loaded. Open one in the Projects menu above.")


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



class OpenProjectPopup(ConfirmCancelActionPopup):
    def __init__(self):
        self._confirm_action_text = "Open project"

        self.game = Game.ECHOES
        preferences = state().preferences

        last_project = ""
        if preferences.last_project_path is not None:
            last_project = os.fspath(preferences.last_project_path)

        iso_path = ""
        if self.game in preferences.game_iso_paths:
            iso_path = os.fspath(preferences.game_iso_paths[self.game])

        self._iso_prompt = IsoPrompt(iso_path, False)

        self.project_prompt = FilePrompt(
            "Project File",
            "Path to the PWIME Project file",
            "Select File",
            ["*.pwimep"],
            last_project,
            validate_project_file,
            save_file=False,
        )

    def _popup_name(self) -> str:
        return "Open Project"

    def render_modal(self) -> bool:
        self.project_prompt.render()
        self._iso_prompt.render()
        return super().render_modal()

    def _valdiate(self) -> bool:
        return self.project_prompt.validate() and self._iso_prompt.validate()

    def _perform_action(self) -> None:
        preferences = state().preferences
        preferences.last_project_path = Path(self.project_prompt.value)
        preferences.game_iso_paths[self.game] = Path(self._iso_prompt.value)

        state().load_iso(self.game, preferences.game_iso_paths[self.game])
        state().open_project(preferences.last_project_path)
        preferences.write_to_user_home()


class ExportProjectPopup(ConfirmCancelActionPopup):
    def __init__(self):
        self._confirm_action_text = "Export project"

        initial_value = ""
        if state().preferences.last_export_path is not None:
            initial_value = os.fspath(state().preferences.last_export_path)

        self.iso_prompt = IsoPrompt(
            initial_value,
            save_file=True,
        )

    def _popup_name(self) -> str:
        return "Export Project"

    def render_modal(self) -> bool:
        self.iso_prompt.render()
        return super().render_modal()

    def _valdiate(self) -> bool:
        return self.iso_prompt.validate()

    def _perform_action(self) -> None:
        preferences = state().preferences
        preferences.last_export_path = Path(self.iso_prompt.value)
        state().project.export_to(preferences.last_export_path)
        preferences.write_to_user_home()



def _show_menu() -> None:
    if imgui.begin_menu("Project"):
        if imgui.menu_item("New", "", False)[0]:
            state().current_popup = NewProjectPopup(state().preferences)

        if imgui.menu_item("Open existing", "", False)[0]:
            state().current_popup = OpenProjectPopup()

        with imgui_helper.disabled(state().project is None):
            if imgui.menu_item("Save", "", False)[0]:
                state().project.save_to_file(state().current_project_path)

            if imgui.menu_item("Export", "", False)[0]:
                state().current_popup = ExportProjectPopup()

            if imgui.menu_item("Close", "", False)[0]:
                # TODO: confirm discarding changes
                state().project = None

        imgui.end_menu()
    #
    # if imgui.begin_menu("Preferences"):
    #     if imgui.menu_item("Metroid Prime 2 ISO", "", False)[0]:
    #         state().current_popup = SelectPrime2IsoPopup()
    #     imgui.end_menu()

    if state().current_popup is not None:
        if not state().current_popup.render():
            state().current_popup = None

    imgui.text_disabled("Bai")


def _any_backend_event_callback(event) -> bool:
    print("EVENT!", event)
    return False


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
    logging.basicConfig(level=logging.DEBUG)

    state().preferences.read_from_user_home()
    state().restore_from_preferences()

    runner_params = hello_imgui.RunnerParams()
    runner_params.callbacks.show_menus = _show_menu
    runner_params.callbacks.pre_new_frame = _pre_new_frame
    runner_params.callbacks.any_backend_event_callback = _any_backend_event_callback
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
