from __future__ import annotations

from imgui_bundle import hello_imgui, imgui
from retro_data_structures.exceptions import UnknownAssetId
from retro_data_structures.formats import Mlvl

from pwime.gui.editor.base_window import BaseWindow
from pwime.gui.gui_state import state


class MlvlWindow(BaseWindow[Mlvl]):
    @property
    def window_label(self):
        try:
            return self.asset.world_name
        except UnknownAssetId:
            return super().window_label

    def render(self) -> None:
        if imgui.begin_table("Areas", 2, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h):
            imgui.table_setup_column("Name", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Asset Id", imgui.TableColumnFlags_.width_fixed)
            imgui.table_headers_row()

            areas = list(self.asset.areas)
            areas.sort(key=lambda it: it.name)

            for area in areas:
                imgui.table_next_row()

                imgui.table_next_column()
                imgui.text(area.name)

                imgui.table_next_column()
                if imgui.selectable(
                    f"{area.mrea_asset_id:08X}",
                    False,
                    imgui.SelectableFlags_.span_all_columns,
                )[1]:
                    state().area_state.open_area(area)

            imgui.end_table()
