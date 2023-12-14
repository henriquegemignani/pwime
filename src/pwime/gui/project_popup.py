import os
from pathlib import Path

from imgui_bundle import imgui
from retro_data_structures.game_check import Game

from pwime.asset_manager import OurAssetManager
from pwime.gui.gui_state import state
from pwime.gui.gui_tools import FolderPrompt, IsoPrompt
from pwime.gui.popup import CurrentImguiPopup
from pwime.preferences import Preferences
from pwime.project import Project
from pwime.util import imgui_helper


def validate_project_file(s: str) -> bool:
    p = Path(s)
    return p.suffix == ".pwimep" and p.is_file()


def validate_project_path(s: str) -> bool:
    return s != "" and Path(s).is_dir()


class NewProjectPopup(CurrentImguiPopup):
    _open_popup = True
    project_name: str = ""

    def __init__(self, preferences: Preferences):
        self._preferences = preferences
        self.game = Game.ECHOES

        iso_path = ""
        if self.game in preferences.game_iso_paths:
            iso_path = os.fspath(preferences.game_iso_paths[self.game])

        self._iso_prompt = IsoPrompt(iso_path)
        self._location_prompt = FolderPrompt(
            "Project Location",
            "Where to create project",
            "",
            validate_project_path,
            False,
        )

    def _valid_project_path(self) -> bool:
        return self._location_prompt.validate()

    def _popup_name(self) -> str:
        return "New Project"

    def render_modal(self) -> bool:
        result = True

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

        return result

    def _prompt_for_location(self) -> None:
        self._location_prompt.render()

    def _prompt_for_iso(self) -> None:
        self._iso_prompt.render()

    def create_project(self) -> None:
        self._preferences.game_iso_paths[self.game] = Path(self._iso_prompt.value)
        self._preferences.last_project_path = Path(self._location_prompt.value).joinpath(f"{self.project_name}.pwimep")

        state().load_iso(self.game, self._preferences.game_iso_paths[self.game])
        Project(self.project_name, OurAssetManager(state().file_providers[self.game], self.game)).save_to_file(
            self._preferences.last_project_path
        )

        state().open_project(self._preferences.last_project_path)
        self._preferences.write_to_user_home()
