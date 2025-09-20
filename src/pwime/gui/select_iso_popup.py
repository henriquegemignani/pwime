import os
from pathlib import Path

from imgui_bundle import imgui
from retro_data_structures.game_check import Game

from pwime.gui.gui_state import state
from pwime.gui.gui_tools import IsoPrompt
from pwime.gui.popup import CurrentImguiPopup
from pwime.preferences import Preferences


class SelectIsoPopup(CurrentImguiPopup):
    project_name: str = ""

    def __init__(self, preferences: Preferences):
        self._preferences = preferences
        self.game = Game.ECHOES

        iso_path = ""
        if self.game in preferences.game_iso_paths:
            iso_path = os.fspath(preferences.game_iso_paths[self.game])

        self._iso_prompt = IsoPrompt(iso_path,
                                     save_file=False,
                                     title="Prime 2 ISO")

    def _popup_name(self) -> str:
        return "Select ISOs"

    def render_modal(self) -> bool:
        result = True

        # Prompt for ISO
        self._prompt_for_iso()

        # Buttons at the end
        if imgui.button("Save"):
            self.save_choice()
            result = False

        imgui.same_line()
        if imgui.button("Cancel"):
            result = False

        return result

    def _prompt_for_iso(self) -> None:
        self._iso_prompt.render()

    def save_choice(self) -> None:
        self._preferences.game_iso_paths[self.game] = Path(self._iso_prompt.value)
        state().load_iso(self.game, self._preferences.game_iso_paths[self.game])
        self._preferences.write_to_user_home()
