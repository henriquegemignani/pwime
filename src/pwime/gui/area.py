from __future__ import annotations

from typing import TYPE_CHECKING

from imgui_bundle import hello_imgui, imgui

from pwime.gui.gui_state import state
from pwime.gui.script_instance import ScriptInstanceState

if TYPE_CHECKING:
    from retro_data_structures.formats.mrea import Area


class AreaState(hello_imgui.DockableWindow):
    area: Area | None = None
    filter: str = ""
    window_label: str = "Area###Area"

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

    def open_area(self, area: Area) -> None:
        self.area = area

        window = hello_imgui.get_runner_params().docking_params.dockable_window_of_name(
            self.window_label
        )
        window.is_visible = True

        self.window_label = f"{self.area.name}###Area"
        window.label = self.window_label

    def render(self):
        if self.area is None:
            return

        changed, new_text = imgui.input_text("Filter Objects", self.filter)
        if changed:
            self.filter = new_text

        if imgui.begin_table("Objects", 4,
                             imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h | imgui.TableFlags_.resizable):
            imgui.table_setup_column("Layer", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Instance Id", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Type", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Name")
            imgui.table_headers_row()

            for layer in self.area.all_layers:
                for instance in layer.instances:
                    instance_name = instance.name
                    type_name = instance.type.__name__

                    if self.filter:
                        if self.filter not in instance_name and self.filter not in type_name:
                            continue

                    imgui.table_next_row()

                    imgui.table_next_column()
                    imgui.text(layer.name if layer.has_parent else "<Generated Objects>")
                    imgui.table_next_column()
                    imgui.text(str(instance.id))
                    imgui.table_next_column()
                    imgui.text(type_name)
                    imgui.table_next_column()
                    if imgui.selectable(
                            f"{instance_name}##{instance.id}",
                            False,
                            imgui.SelectableFlags_.span_all_columns | imgui.SelectableFlags_.allow_item_overlap,
                    )[1]:
                        state().instance_state.open_instance(self.area, instance)

            imgui.end_table()
