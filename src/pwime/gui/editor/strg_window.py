from __future__ import annotations

from imgui_bundle import hello_imgui, imgui
from retro_data_structures.exceptions import UnknownAssetId
from retro_data_structures.formats import Mlvl, Strg

from pwime.gui.editor.base_window import BaseWindow
from pwime.gui.gui_state import state


class StrgWindow(BaseWindow[Strg]):
    def render(self) -> None:
        imgui.text("Hi world")
