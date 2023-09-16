from __future__ import annotations

import functools

from imgui_bundle import hello_imgui, imgui
from retro_data_structures.exceptions import UnknownAssetId
from retro_data_structures.formats import Mlvl

from pwime.gui.area import AreaDockWindow
from pwime.gui.gui_state import state


class MlvlDockWindow(hello_imgui.DockableWindow):
    def __init__(self, mlvl_id: int):
        mlvl = state.asset_manager.get_file(mlvl_id, Mlvl)
        try:
            name = mlvl.world_name
        except UnknownAssetId:
            name = f"MLVL {mlvl_id:08X}"

        self.mlvl = mlvl
        super().__init__(
            name,
            "MainDockSpace",
            self.render,
        )

    def render(self):
        if imgui.begin_table("Areas", 2, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h):
            imgui.table_setup_column("Name", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Asset Id", imgui.TableColumnFlags_.width_fixed)
            imgui.table_headers_row()

            areas = list(self.mlvl.areas)
            areas.sort(key=lambda it: it.name)

            for area in areas:
                imgui.table_next_row()

                imgui.table_next_column()
                imgui.text(area.name)

                imgui.table_next_column()
                if imgui.selectable(
                        f"{area.mrea_asset_id:08X}",
                        False,
                        imgui.SelectableFlags_.span_all_columns | imgui.SelectableFlags_.allow_item_overlap,
                )[1]:
                    state.pending_new_docks.append(AreaDockWindow(area))

            imgui.end_table()
