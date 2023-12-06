import os
from pathlib import Path

from imgui_bundle import imgui
from imgui_bundle import portable_file_dialogs
from retro_data_structures.game_check import Game

from pwime.asset_manager import OurAssetManager
from pwime.gui.gui_state import state
from pwime.gui.popup import CurrentPopup
from pwime.preferences import Preferences
from pwime.project import Project
from pwime.util import imgui_helper


def validate_project_path(s: str) -> bool:
    return s != "" and Path(s).is_dir()


class NewProjectPopup(CurrentPopup):
    _open_popup = True
    project_name: str = ""
    project_path: str = ""
    iso_path: str = ""
    folder_dialog: portable_file_dialogs.select_folder | None = None
    iso_dialog: portable_file_dialogs.open_file | None = None

    def __init__(self, preferences: Preferences):
        self._preferences = preferences
        self.game = Game.ECHOES
        if self.game in preferences.game_iso_paths:
            self.iso_path = os.fspath(preferences.game_iso_paths[self.game])

    def _valid_project_path(self) -> bool:
        return validate_project_path(self.project_path)

    def _valid_iso_path(self) -> bool:
        p = Path(self.iso_path)
        return p.suffix == ".iso" and p.is_file()

    def render(self) -> bool:
        result = True

        if self._open_popup:
            imgui.open_popup("New Project")
            self._open_popup = False

        center = imgui.get_main_viewport().get_center()
        imgui.set_next_window_pos(center, imgui.Cond_.appearing, imgui.ImVec2(0.5, 0.5))

        if imgui.begin_popup_modal("New Project", None):
            # Name Row
            modified, new_name = imgui_helper.validated_input_text(
                "Project Name", self.project_name,
                self.project_name != ""
            )
            if modified:
                self.project_name = new_name

            imgui.combo("Game", 0, ["Metroid Prime 2"])

            # Project Location
            self._prompt_for_location()

            # Prompt for ISO
            self._prompt_for_iso()

            # Buttons at the end
            valid = self._valid_project_path() and self.project_name != ""
            with imgui_helper.disabled(not valid):
                if imgui.button("Create project"):
                    self.create_project()
                    result = False

            imgui.same_line()
            if imgui.button("Cancel"):
                result = False

            imgui.end_popup()

        return result

    def _prompt_for_location(self) -> None:
        modified, new_path = imgui_helper.validated_input_text(
            "Project Location", self.project_path,
            self._valid_project_path()
        )
        if modified:
            self.project_path = new_path

        imgui.same_line()
        if imgui.button("Select Folder"):
            self.folder_dialog = portable_file_dialogs.select_folder(
                "Where to create project",
                self.project_path
            )

        if self.folder_dialog is not None:
            if self.folder_dialog.ready():
                new_folder = self.folder_dialog.result()
                if new_folder:
                    self.project_path = new_folder
                self.folder_dialog = None

    def _prompt_for_iso(self) -> None:
        modified, new_path = imgui_helper.validated_input_text(
            "Game ISO", self.iso_path,
            self._valid_iso_path()
        )
        if modified:
            self.iso_path = new_path

        imgui.same_line()
        if imgui.button("Select ISO"):
            self.iso_dialog = portable_file_dialogs.open_file(
                "Path to a game ISO",
                self.iso_path,
                filters=["*.iso"]
            )

        if self.iso_dialog is not None:
            if self.iso_dialog.ready():
                new_iso = self.iso_dialog.result()
                if new_iso:
                    self.iso_path = new_iso[0]
                self.iso_dialog = None

    def create_project(self) -> None:
        self._preferences.game_iso_paths[self.game] = Path(self.iso_path)
        self._preferences.last_project_path = Path(self.project_path).joinpath(f"{self.project_name}.pwimep")

        state().load_iso(self.game, self._preferences.game_iso_paths[self.game])
        Project(self.project_name, OurAssetManager(state().file_providers[self.game], self.game)).save_to_file(
            self._preferences.last_project_path
        )

        state().open_project(self._preferences.last_project_path)
        self._preferences.write_to_user_home()
