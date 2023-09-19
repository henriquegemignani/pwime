from __future__ import annotations

from imgui_bundle import hello_imgui, imgui
from retro_data_structures.exceptions import UnknownAssetId
from retro_data_structures.formats import Mlvl

from pwime.gui.gui_state import state


class MlvlState:
    mlvl: Mlvl | None = None
    mlvl_id: int | None = None
    window_label: str = "World###MLVL"

    def create_imgui_window(self) -> hello_imgui.DockableWindow:
        result = hello_imgui.DockableWindow(
            self.window_label,
            "MainDockSpace",
            self.render,
            is_visible_=False,
        )
        result.include_in_view_menu = False
        result.remember_is_visible = False
        return result

    def open_mlvl(self, mlvl_id: int) -> None:
        self.mlvl = state().asset_manager.get_file(mlvl_id, Mlvl)
        self.mlvl_id = mlvl_id

        window = hello_imgui.get_runner_params().docking_params.dockable_window_of_name(
            self.window_label
        )
        window.is_visible = True

        try:
            name = self.mlvl.world_name
        except UnknownAssetId:
            name = f"MLVL {mlvl_id:08X}"

        self.window_label = f"{name}###MLVL"
        window.label = self.window_label

    def render(self) -> None:
        if self.mlvl is None:
            return

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
                    state().area_state.open_area(area)

            imgui.end_table()
