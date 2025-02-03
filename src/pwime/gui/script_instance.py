from __future__ import annotations

import dataclasses
import enum
import functools
import typing

from imgui_bundle import hello_imgui, imgui
from retro_data_structures.formats.script_object import Connection
from retro_data_structures.base_resource import AssetId
from retro_data_structures.properties.base_color import BaseColor
from retro_data_structures.properties.base_property import BaseProperty
from retro_data_structures.properties.base_vector import BaseVector
from retro_data_structures.properties.base_spline import Knot

from pwime.gui.gui_state import FilteredAssetList, state
from pwime.util import imgui_helper
from pwime.operations.script_instance import (
    InstanceReference,
    PropReference,
    ScriptInstancePropertyEdit,
    create_patch_for,
    get_instance,
)

if typing.TYPE_CHECKING:
    from retro_data_structures.formats.mrea import Area
    from retro_data_structures.formats.script_object import ScriptInstance

T = typing.TypeVar("T")


def submit_edit_for(reference: PropReference, new_value: typing.Any) -> None:
    instance = get_instance(state().asset_manager, reference.instance)

    delta = create_patch_for(instance, reference.path, new_value)

    state().project.add_new_operation(
        ScriptInstancePropertyEdit(
            reference.instance,
            instance.type,
            delta,
        )
    )


def submit_imgui_results(reference: PropReference, imgui_result: tuple[bool, object]) -> None:
    if imgui_result[0]:
        submit_edit_for(reference, imgui_result[1])


class PropertyRenderer(typing.Generic[T]):
    def __init__(self, item: T, field: dataclasses.Field):
        self.item = item
        self.field = field

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        raise NotImplementedError

    def is_leaf(self) -> bool:
        return True

    def render(self, reference: PropReference) -> None:
        raise NotImplementedError


class VectorRenderer(PropertyRenderer[BaseVector]):
    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, BaseVector):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        v = [self.item.x, self.item.y, self.item.z]
        modified, new_value = imgui.input_float3(f"##{self.field.name}", v)
        if modified:
            submit_edit_for(reference, type(self.item)(*new_value))


class ColorRenderer(PropertyRenderer[BaseColor]):
    color_cls: type[BaseColor]

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, BaseColor):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        v = [self.item.r, self.item.g, self.item.b, self.item.a]

        modified, new_value = imgui.color_edit4(f"##{self.field.name}", v)
        if modified:
            submit_edit_for(reference, type(self.item)(*new_value))


class GenericPropertyRenderer(PropertyRenderer[BaseProperty]):
    """Renders the property if it's a struct. Recursively renders the fields."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, BaseProperty):
            return cls(item, field)
        return None

    def is_leaf(self) -> bool:
        return False

    def render(self, reference: PropReference) -> None:
        imgui.text("--")
        render_property(self.item, reference)


cached_asset_list: FilteredAssetList = FilteredAssetList(frozenset(), "", [])


class AssertIdRenderer(PropertyRenderer[AssetId]):
    """Renders the int as hex."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, AssetId) and "asset_types" in field.metadata:
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        if imgui.button("Change"):
            imgui.open_popup("Select an asset")

        imgui.same_line()
        imgui.text(state().asset_manager.asset_names.get(self.item, f"{self.item:08X}"))

        imgui.set_next_window_size(imgui.ImVec2(600, 400))
        if imgui.begin_popup("Select an asset"):
            asset_types = frozenset(self.field.metadata["asset_types"])
            asset_manager = state().asset_manager

            global cached_asset_list  # noqa: PLW0603
            asset_filter = imgui.input_text("Filter Assets", cached_asset_list.filter)[1]

            if imgui.begin_table(
                    "All Assets",
                    2,
                    imgui.TableFlags_.row_bg
                    | imgui.TableFlags_.borders_h
                    | imgui.TableFlags_.scroll_y
                    | imgui.TableFlags_.sortable,
            ):
                imgui.table_setup_column("Asset Id", imgui.TableColumnFlags_.width_fixed)
                imgui.table_setup_column("Name")

                imgui.table_headers_row()

                sort_spec = imgui.table_get_sort_specs()
                if sort_spec.specs_dirty or (asset_types, asset_filter) != cached_asset_list[:2]:
                    # Filter changed, re-filter list
                    if (asset_types, asset_filter) != cached_asset_list[:2]:
                        cached_asset_list = state().filtered_asset_list(asset_types, asset_filter)

                    spec = sort_spec.get_specs(0)

                    # Find the value to sort by.
                    if spec.column_index == 0:

                        def val(a: tuple[int, int]) -> int:
                            return a[1]

                    else:

                        def val(a: tuple[int, int]) -> int:
                            return asset_manager.asset_names.get(a[1], "ZZZZZZZZZZ")  # sort last!

                    # And the direction
                    if spec.get_sort_direction() == imgui.SortDirection_.ascending.value:
                        mul = 1
                    else:
                        mul = -1

                    def sort_by_spec(a: tuple[int, int], b: tuple[int, int]) -> int:
                        a_val = val(a)
                        b_val = val(b)
                        if a_val < b_val:
                            return -mul
                        if a_val == b_val:
                            return 0
                        return mul

                    indices = list(enumerate(cached_asset_list.ids))
                    indices.sort(key=functools.cmp_to_key(sort_by_spec))
                    cached_asset_list = FilteredAssetList(
                        cached_asset_list.types, asset_filter, [cached_asset_list.ids[i] for i, _ in indices]
                    )
                    sort_spec.specs_dirty = False

                clipper = imgui.ListClipper()
                clipper.begin(len(cached_asset_list.ids))
                while clipper.step():
                    for index in range(clipper.display_start, clipper.display_end):
                        asset = cached_asset_list.ids[index]
                        # for asset in self.cached_asset_list.ids:
                        imgui.table_next_row()

                        imgui.table_next_column()
                        if imgui.selectable(
                                f"{asset:08X}",
                                False,
                                imgui.SelectableFlags_.span_all_columns,
                        )[1]:
                            submit_edit_for(reference, asset)
                            imgui.close_current_popup()

                        imgui.table_next_column()
                        imgui.text_disabled(asset_manager.asset_names.get(asset, "<unknown>"))

                imgui.end_table()

            imgui.end_popup()


def _enum_name(e: enum.Enum) -> str:
    name = e.name
    if name == "_None":
        return "None"
    return name


class IntEnumRenderer(PropertyRenderer[enum.IntEnum]):
    """Renders a combo box to select an enum value."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, enum.IntEnum):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        changed, new_value = imgui_helper.enum_combo(self.item, f"##{self.field.name}")
        if changed:
            submit_edit_for(reference, new_value)


class IntFlagRenderer(PropertyRenderer[enum.IntFlag]):
    """Renders a multiple-choice combo box for a flagset."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, enum.IntFlag):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        new_value = None

        if imgui.begin_combo(f"##{self.field.name}", self.item.name):
            for alt in self.item.__class__:
                changed, check = imgui.checkbox(_enum_name(alt), alt in self.item)
                if changed:
                    assert new_value is None
                    if check:
                        new_value = self.item | alt
                    else:
                        new_value = self.item & ~alt

            imgui.end_combo()

        if new_value is not None:
            submit_edit_for(reference, new_value)


class FloatRenderer(PropertyRenderer[float]):
    """Renders the float as an float input."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, float):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        submit_imgui_results(
            reference,
            imgui.input_float(f"##{self.field.name}", self.item),
        )


class StringRenderer(PropertyRenderer[str]):
    """Renders the str as text box."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, str):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        submit_imgui_results(
            reference,
            imgui.input_text(f"##{self.field.name}", self.item),
        )


class BoolRenderer(PropertyRenderer[bool]):
    """Renders the bool as a checkbox."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, bool):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        submit_imgui_results(
            reference,
            imgui.checkbox(f"##{self.field.name}", self.item),
        )


class IntRenderer(PropertyRenderer[int]):
    """Renders the bool as a checkbox."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, int):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        submit_imgui_results(
            reference,
            imgui.input_int(f"##{self.field.name}", self.item),
        )

def render_knot_field_begin(name: str, fields: tuple[dataclasses.Field]) -> dataclasses.Field:
    field: dataclasses.Field
    field = next(filter(lambda f: f.name == name, fields), None)
    assert field is not None
    
    imgui.table_next_row()
    imgui.table_next_column()
    
    if "asset_types" in field.metadata:
        type_name = f"AssetId ({'/'.join(field.metadata['asset_types'])})"
    else:
        type_name = field.type
    
    imgui.text(field.name)
    
    imgui.table_next_column()
    imgui.text(type_name)
    imgui.table_next_column()
    
    return field

def render_knot_field_end() -> None:
    pass

def submit_imgui_knot_results(field: str, reference: PropReference, imgui_result: tuple[bool, object], knot: Knot, knots: list[Knot], factory: type | None = None) -> None:
    if imgui_result[0]:
        setattr(knot, field, factory(imgui_result[1]) if factory is not None else imgui_result[1])
        submit_edit_for(reference, knots)

class KnotListRenderer(PropertyRenderer[list[Knot]]):
    """Renders the list of Knots."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, list) and field.name == "knots":
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        knots: list[Knot] = self.item
        
        if imgui.begin_table(
                "Knnots", 2, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h | imgui.TableFlags_.resizable
        ):
            imgui.table_setup_column("Index")
            imgui.table_setup_column("Value")
            
            i: int = 0
            knot: Knot
            for knot in knots:
                imgui.table_headers_row()

                imgui.table_next_row()
                imgui.table_next_column()

                imgui.text(str(i))
                imgui.table_next_column()

                if imgui.begin_table(f"Knot{i}", 3, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h | imgui.TableFlags_.resizable):
                    imgui.table_setup_column("Name")
                    imgui.table_setup_column("Type")
                    imgui.table_setup_column("Value")
                    imgui.table_headers_row()

                    # ================================================================================
                    assert dataclasses.is_dataclass(knot)
                    fields: tuple[dataclasses.Field] = dataclasses.fields(knot)
                    field: dataclasses.Field
                    
                    if knot.cached_tangents_a is None:
                        knot.cached_tangents_a = (float(0.0), float(0.0))
                    
                    if knot.cached_tangents_b is None:
                        knot.cached_tangents_b = (float(0.0), float(0.0))

                    field = render_knot_field_begin("time", fields)
                    submit_imgui_knot_results("time", reference, imgui.input_float(f"##{field.name}", knot.time), knot, knots)
                    render_knot_field_end()

                    field = render_knot_field_begin("amplitude", fields)
                    submit_imgui_knot_results("amplitude", reference, imgui.input_float(f"##{field.name}", knot.amplitude), knot, knots)
                    render_knot_field_end()

                    field = render_knot_field_begin("unk_a", fields)
                    submit_imgui_knot_results("unk_a", reference, imgui.input_int(f"##{field.name}", knot.unk_a), knot, knots)
                    render_knot_field_end()

                    field = render_knot_field_begin("unk_b", fields)
                    submit_imgui_knot_results("unk_b", reference, imgui.input_int(f"##{field.name}", knot.unk_b), knot, knots)
                    render_knot_field_end()

                    field = render_knot_field_begin("cached_tangents_a", fields)
                    if knot.unk_a == 5:
                        submit_imgui_knot_results("cached_tangents_a", reference, imgui.input_float2(f"##{self.field.name}", list(knot.cached_tangents_a)), knot, knots, tuple)
                    else:
                        imgui.text("N/A")
                    render_knot_field_end()

                    field = render_knot_field_begin("cached_tangents_b", fields)
                    if knot.unk_b == 5:
                        submit_imgui_knot_results("cached_tangents_b", reference, imgui.input_float2(f"##{self.field.name}", list(knot.cached_tangents_b)), knot, knots, tuple)
                    else:
                        imgui.text("N/A")
                    render_knot_field_end()
                    # ================================================================================

                    imgui.end_table()

                imgui.table_next_column()
                i += 1

            imgui.end_table()

        if imgui.begin_table("Add/Remove", 2):
            imgui.table_setup_column("Content")

            imgui.table_next_row()
            imgui.table_next_column()

            if imgui.button("-"):
                knots.pop()
                submit_edit_for(reference, knots)

            imgui.table_next_column()

            if imgui.button("+"):
                try:
                    knots.append(Knot())
                except TypeError:
                    knots.append(Knot(float(0.0), float(0.0), 0, 0, (float(0.0), float(0.0)), (float(0.0), float(0.0))))
                submit_edit_for(reference, knots)

            imgui.end_table()


class UnknownPropertyRenderer(PropertyRenderer):
    """Renders the property by casting to text. Can't edit."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        return cls(item, field)

    def render(self, reference: PropReference) -> None:
        imgui.text(str(self.item))


ALL_PROPERTY_RENDERERS = [
    VectorRenderer,
    ColorRenderer,
    GenericPropertyRenderer,
    IntEnumRenderer,
    IntFlagRenderer,
    AssertIdRenderer,
    FloatRenderer,
    StringRenderer,
    BoolRenderer,
    IntRenderer,
    KnotListRenderer,
    UnknownPropertyRenderer,
]


def render_property(props: BaseProperty, reference: PropReference) -> None:
    assert dataclasses.is_dataclass(props)
    for field in dataclasses.fields(props):
        imgui.table_next_row()
        imgui.table_next_column()

        item = getattr(props, field.name)

        renderer: PropertyRenderer | None = None
        for renderer_class in ALL_PROPERTY_RENDERERS:
            renderer = renderer_class.matches(item, field)
            if renderer is not None:
                break

        assert renderer is not None

        flags = imgui.TreeNodeFlags_.span_full_width
        if renderer.is_leaf():
            flags |= imgui.TreeNodeFlags_.leaf | imgui.TreeNodeFlags_.bullet | imgui.TreeNodeFlags_.no_tree_push_on_open

        if "asset_types" in field.metadata:
            type_name = f"AssetId ({'/'.join(field.metadata['asset_types'])})"
        else:
            type_name = type(item).__name__

        is_open = imgui.tree_node_ex(field.name, flags)
        imgui.table_next_column()
        imgui.text(type_name)
        imgui.table_next_column()

        if renderer.is_leaf():
            imgui.push_id(field.name)
            renderer.render(reference.append(field.name))
            imgui.pop_id()
        elif is_open:
            renderer.render(reference.append(field.name))
            imgui.tree_pop()


class ScriptInstanceState(hello_imgui.DockableWindow):
    instance_ref: tuple[Area, ScriptInstance] | None = None
    window_label: str = "Object###ScriptInstance"

    def create_imgui_window(self) -> hello_imgui.DockableWindow:
        result = hello_imgui.DockableWindow(
            self.window_label,
            "RightSpace",
            self.render,
            is_visible_=False,
        )
        result.include_in_view_menu = False
        result.remember_is_visible = False
        return result

    def open_instance(self, area: Area, instance: ScriptInstance) -> None:
        self.instance_ref = area, instance

        window = hello_imgui.get_runner_params().docking_params.dockable_window_of_name(self.window_label)
        window.is_visible = True

        self.window_label = f"{instance.name} - {instance.id} ({area.name})###ScriptInstance"
        window.label = self.window_label

    def render(self):
        if self.instance_ref is None:
            return

        area, instance = self.instance_ref

        props = instance.get_properties()

        mlvl_id = state().mlvl_state.mlvl_id

        if imgui.begin_table(
                "Properties", 3, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h | imgui.TableFlags_.resizable
        ):
            imgui.table_setup_column("Name")
            imgui.table_setup_column("Type")
            imgui.table_setup_column("Value")
            imgui.table_headers_row()
            render_property(props, PropReference(InstanceReference(mlvl_id, area.mrea_asset_id, instance.id), ()))
            imgui.end_table()

        if imgui.begin_table(
                "Connections", 4, imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h | imgui.TableFlags_.resizable
        ):
            imgui.table_setup_column("State")
            imgui.table_setup_column("Message")
            imgui.table_setup_column("Target Id")
            imgui.table_setup_column("Target Name")
            imgui.table_headers_row()

            connections = list(instance.connections)
            def edit_connection(index: int, conn: Connection) -> None:
                # TODO: make operation
                connections[index] = conn
                instance.connections = connections

            for i, connection in enumerate(connections):
                imgui.table_next_row()
                imgui.table_next_column()
                changed, new_state = imgui_helper.enum_combo(connection.state, f"##{i}_state")
                if changed:
                    edit_connection(i, dataclasses.replace(connection, state=new_state))
                imgui.table_next_column()

                changed, new_message = imgui_helper.enum_combo(connection.message, f"##{i}_message")
                if changed:
                    edit_connection(i, dataclasses.replace(connection, message=new_message))
                imgui.table_next_column()
                imgui.text(f"{connection.target}")
                imgui.table_next_column()

                if connection.target == instance.id:
                    target_description = "Self"
                else:
                    try:
                        target = area.get_instance(connection.target)
                        target_description = f"{target.type.__name__} - {target.name}"
                    except KeyError:
                        target_description = "Missing"

                imgui.text(target_description)

            imgui.end_table()
