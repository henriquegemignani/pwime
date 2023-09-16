from __future__ import annotations

from imgui_bundle import hello_imgui, imgui
from retro_data_structures.formats.mrea import Area

from pwime.gui.gui_state import state
from pwime.gui.script_instance import ScriptInstanceDockWindow


class AreaDockWindow(hello_imgui.DockableWindow):
    def __init__(self, area: Area):
        super().__init__(
            area.name,
            "MainDockSpace",
            gui_function_=self.render,
        )
        self.area = area
        self.filter = ""

    def render(self):
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
                        state.pending_new_docks.append(ScriptInstanceDockWindow(self, instance))

            imgui.end_table()
