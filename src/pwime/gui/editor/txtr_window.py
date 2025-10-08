from __future__ import annotations

import os.path
from typing import TYPE_CHECKING

from imgui_bundle import imgui, hello_imgui
from retro_data_structures.formats import Txtr
from retro_data_structures.formats.txtr import ImageFormat

from pwime.gui.editor.base_window import BaseWindow

if TYPE_CHECKING:
    pass


class TxtrWindow(BaseWindow[Txtr]):
    textures: list[tuple[str, tuple[int, int]]]

    def __init__(self, asset_id: int):
        super().__init__(asset_id)

        from pwime.gui.gui_state import state
        self.textures = []

        img = self.asset.main_image_data
        img_name = f"txtr_{self.asset_id:08x}.png"
        img.save(os.path.join(state().temp_assets_path, img_name))

        self.textures.append((
            img_name,
            img.size,
        ))

    def render(self) -> None:
        imgui.text(f"Format: {self.asset.raw.header.format.name}")
        imgui.text(f"Size: {self.asset.raw.header.width} x {self.asset.raw.header.height}")
        imgui.text(f"Mipmaps: {self.asset.raw.header.mipmap_count}")

        for tex_id, size in self.textures:
            hello_imgui.image_from_asset(tex_id, size)
