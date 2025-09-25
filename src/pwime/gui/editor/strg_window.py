from __future__ import annotations

from imgui_bundle import imgui
from retro_data_structures.formats import Strg

from pwime.gui.editor.base_window import BaseWindow


class StrgWindow(BaseWindow[Strg]):
    def render(self) -> None:
        imgui.text("Hi world")
