from __future__ import annotations

import dataclasses
import enum
import typing

from imgui_bundle import imgui
from retro_data_structures.properties.base_property import BaseProperty
from retro_data_structures.properties.base_vector import BaseVector
from retro_data_structures.properties.shared_core import Vector

from pwime.gui.references import PropReference

T = typing.TypeVar("T")


class PropertyRenderer(typing.Generic[T]):
    def __init__(self, item: T, field: dataclasses.field):
        self.item = item
        self.field = field

    @classmethod
    def matches(cls, item: object, field: dataclasses.field) -> typing.Self | None:
        raise NotImplementedError()

    def is_leaf(self) -> bool:
        return True

    def render(self, reference: PropReference) -> None:
        raise NotImplementedError()


class VectorRenderer(PropertyRenderer[BaseVector]):
    @classmethod
    def matches(cls, item: object, field: dataclasses.field) -> typing.Self | None:
        if isinstance(item, BaseVector):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        v = [self.item.x, self.item.y, self.item.z]
        imgui.input_float3(f"##{self.field.name}", v)


class GenericPropertyRenderer(PropertyRenderer[BaseProperty]):
    """Renders the property if it's a struct. Recursively renders the fields."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.field) -> typing.Self | None:
        if isinstance(item, BaseProperty):
            return cls(item, field)
        return None

    def is_leaf(self) -> bool:
        return False

    def render(self, reference: PropReference) -> None:
        imgui.text("--")
        render_property(self.item, reference.append(self.field.name))


class IntEnumRenderer(PropertyRenderer[enum.IntEnum]):
    """Renders a combo box to select an enum value."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.field) -> typing.Self | None:
        if isinstance(item, enum.IntEnum):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        all_values = [it.name for it in self.item.__class__]
        imgui.combo(f"##{self.field.name}", self.item.value, all_values)


class IntFlagRenderer(PropertyRenderer[enum.IntFlag]):
    """Renders a multiple-choice combo box for a flagset."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.field) -> typing.Self | None:
        if isinstance(item, enum.IntFlag):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        if imgui.begin_combo(f"##{self.field.name}", self.item.name):
            for alt in self.item.__class__:
                imgui.checkbox(alt.name, alt in self.item)
            imgui.end_combo()


class FloatRenderer(PropertyRenderer[float]):
    """Renders the str as text box."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.field) -> typing.Self | None:
        if isinstance(item, float):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        imgui.input_float(f"##{self.field.name}", self.item)


class StringRenderer(PropertyRenderer[str]):
    """Renders the str as text box."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.field) -> typing.Self | None:
        if isinstance(item, str):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        imgui.input_text(f"##{self.field.name}", self.item)


class BoolRenderer(PropertyRenderer[bool]):
    """Renders the bool as a checkbox."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.field) -> typing.Self | None:
        if isinstance(item, bool):
            return cls(item, field)
        return None

    def render(self, reference: PropReference) -> None:
        imgui.checkbox(f"##{self.field.name}", self.item)


class UnknownPropertyRenderer(PropertyRenderer):
    """Renders the property by casting to text. Can't edit."""

    @classmethod
    def matches(cls, item: object, field: dataclasses.field) -> typing.Self | None:
        return cls(item, field)

    def render(self, reference: PropReference) -> None:
        imgui.text(str(self.item))


ALL_PROPERTY_RENDERERS = [
    VectorRenderer,
    GenericPropertyRenderer,
    IntEnumRenderer,
    IntFlagRenderer,
    FloatRenderer,
    StringRenderer,
    BoolRenderer,
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

        is_open = imgui.tree_node_ex(field.name, flags)
        imgui.table_next_column()
        imgui.text(type(item).__name__)
        imgui.table_next_column()

        renderer.render(reference)

        if is_open and not renderer.is_leaf():
            imgui.tree_pop()
