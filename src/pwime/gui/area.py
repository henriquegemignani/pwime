from __future__ import annotations

from typing import TYPE_CHECKING

from imgui_bundle import hello_imgui, imgui
from imgui_bundle import (
    imgui_node_editor as ed,
)

from pwime.gui.gui_state import state

if TYPE_CHECKING:
    from retro_data_structures.formats.mrea import Area
    from retro_data_structures.properties.echoes.archetypes.EditorProperties import EditorProperties


class AreaState(hello_imgui.DockableWindow):
    area: Area | None = None
    filter: str = ""
    window_label: str = "Area###Area"
    show_object_list: bool = True
    layer_states: dict[int, bool]
    has_position: set[int]

    def __init__(self):
        super().__init__()
        self.layer_states = {}
        self.has_position = set()

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

        window = hello_imgui.get_runner_params().docking_params.dockable_window_of_name(self.window_label)
        window.is_visible = True

        self.window_label = f"{self.area.name}###Area"
        window.label = self.window_label

    def _render_object_list(self) -> None:
        changed, new_text = imgui.input_text("Filter Objects", self.filter)
        if changed:
            self.filter = new_text

        if imgui.begin_table(
            "Objects", 4, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h | imgui.TableFlags_.resizable
        ):
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
                        imgui.SelectableFlags_.span_all_columns,
                    )[1]:
                        state().instance_state.open_instance(self.area, instance)

            imgui.end_table()

    def _render_object_graph(self) -> None:
        for layer in self.area.layers:
            state = self.layer_states.get(layer.index)
            self.layer_states[layer.index] = imgui.checkbox(f"{layer.name}##Layer{layer.index}", state)[1]

        ed.begin("Objects", imgui.ImVec2(0.0, 0.0))

        for layer in self.area.layers:
            if not self.layer_states.get(layer.index):
                continue

            for object in layer.instances:
                node_id = ed.NodeId(int(object.id))

                if object.id not in self.has_position:
                    try:
                        editor_properties: EditorProperties = object.get_properties().editor_properties
                        pos = editor_properties.transform.position
                        ed.set_node_position(node_id, imgui.ImVec2(pos.x * 100, pos.y * 100))
                    except Exception as e:
                        print(e)
                    self.has_position.add(object.id)

                ed.begin_node(node_id)
                imgui.text(f"{object.id} - {object.type.__name__}")
                imgui.text(object.name)

                ed.begin_pin(ed.PinId(object.id << 1), ed.PinKind.input)

                imgui.text("-> In")
                ed.end_pin()
                imgui.same_line()
                ed.begin_pin(ed.PinId((object.id << 1) + 1), ed.PinKind.output)
                imgui.text("Out ->")
                ed.end_pin()

                ed.end_node()

        i = 1 << 32
        for layer in self.area.layers:
            for object in layer.instances:
                for connection in object.connections:
                    ed.link(ed.LinkId(i), ed.PinId((connection.target << 1)), ed.PinId((object.id << 1) + 1))
                    i += 1

        ed.end()

    def render(self):
        if self.area is None:
            return

        if imgui.radio_button("Object List", self.show_object_list):
            self.show_object_list = True
        imgui.same_line()
        if imgui.radio_button("Graph", not self.show_object_list):
            self.show_object_list = False

        if self.show_object_list:
            self._render_object_list()
        else:
            self._render_object_graph()
