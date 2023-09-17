from __future__ import annotations

import dataclasses
import enum
import typing

from imgui_bundle import imgui, hello_imgui
from retro_data_structures.base_resource import AssetId
from retro_data_structures.formats.script_object import ScriptInstance
from retro_data_structures.properties.base_property import BaseProperty
from retro_data_structures.properties.base_vector import BaseVector

from pwime.gui.gui_state import state
from pwime.gui.references import PropReference, InstanceReference

if typing.TYPE_CHECKING:
    from pwime.gui.area import AreaDockWindow

T = typing.TypeVar("T")


class PropertyRenderer(typing.Generic[T]):
    def __init__(self, item: T, field: dataclasses.Field):
        self.item = item
        self.field = field

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        raise NotImplementedError()

    def is_leaf(self) -> bool:
        return True

    def render(self, reference: PropReference) -> None:
        raise NotImplementedError()


class VectorRenderer(PropertyRenderer[BaseVector]):
    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, BaseVector):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        v = [self.item.x, self.item.y, self.item.z]
        imgui.input_float3(f"##{self.field.name}", v)


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
        render_property(self.item, reference.append(self.field.name))


class AssertIdRenderer(PropertyRenderer[AssetId]):
    """Renders the int as hex."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, AssetId) and "asset_types" in field.metadata:
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        types = ",".join(self.field.metadata["asset_types"])
        if imgui.button(f"Select {types}"):
            pass
        imgui.same_line()
        imgui.text(state.asset_manager.asset_names.get(self.item, f"{self.item:08X}"))


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
        all_values = [_enum_name(it) for it in self.item.__class__]
        imgui.combo(f"##{self.field.name}", self.item.value, all_values)


class IntFlagRenderer(PropertyRenderer[enum.IntFlag]):
    """Renders a multiple-choice combo box for a flagset."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, enum.IntFlag):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        if imgui.begin_combo(f"##{self.field.name}", self.item.name):
            for alt in self.item.__class__:
                imgui.checkbox(_enum_name(alt), alt in self.item)
            imgui.end_combo()


class FloatRenderer(PropertyRenderer[float]):
    """Renders the float as an float input."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, float):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        imgui.input_float(f"##{self.field.name}", self.item)


class StringRenderer(PropertyRenderer[str]):
    """Renders the str as text box."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, str):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        imgui.input_text(f"##{self.field.name}", self.item)


class BoolRenderer(PropertyRenderer[bool]):
    """Renders the bool as a checkbox."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, bool):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        imgui.checkbox(f"##{self.field.name}", self.item)


class IntRenderer(PropertyRenderer[int]):
    """Renders the bool as a checkbox."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        if isinstance(item, int):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        imgui.input_int(f"##{self.field.name}", self.item)


class UnknownPropertyRenderer(PropertyRenderer):
    """Renders the property by casting to text. Can't edit."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.Field) -> typing.Self | None:
        return cls(item, field)

    def render(self, reference: PropReference) -> None:
        imgui.text(str(self.item))


ALL_PROPERTY_RENDERERS = [
    VectorRenderer,
    GenericPropertyRenderer,
    IntEnumRenderer,
    IntFlagRenderer,
    AssertIdRenderer,
    FloatRenderer,
    StringRenderer,
    BoolRenderer,
    IntRenderer,
    UnknownPropertyRenderer,
]


def render_property(props: BaseProperty, reference: PropReference) -> None:
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
            renderer.render(reference)
        elif is_open:
            renderer.render(reference)
            imgui.tree_pop()


class ScriptInstanceDockWindow(hello_imgui.DockableWindow):
    def __init__(self, parent: AreaDockWindow, instance: ScriptInstance):
        super().__init__(
            f"{instance.name} - {instance.id} ({parent.area.name})",
            "RightSpace",
            gui_function_=self.render,
        )
        self.parent = parent
        self.instance = instance

    def render(self):
        props = self.instance.get_properties()

        if imgui.begin_table("Properties", 3,
                             imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h | imgui.TableFlags_.resizable):
            imgui.table_setup_column("Name")
            imgui.table_setup_column("Type")
            imgui.table_setup_column("Value")
            imgui.table_headers_row()
            render_property(props,
                            PropReference(
                                InstanceReference(self.parent.area.mrea_asset_id, self.instance.id), ())
                            )
            imgui.end_table()
