import contextlib
import enum
import typing

from imgui_bundle import imgui


@contextlib.contextmanager
def disabled(value: bool = True):
    imgui.begin_disabled(value)
    yield
    imgui.end_disabled()


@contextlib.contextmanager
def color_input_border(enabled: bool, color: imgui.ImColor):
    if enabled:
        imgui.push_style_var(imgui.StyleVar_.frame_border_size, 2.0)
        imgui.push_style_color(imgui.Col_.border, color.value)
    yield
    if enabled:
        imgui.pop_style_color()
        imgui.pop_style_var()


def validated_input_text(title: str, value: str, valid: bool) -> tuple[bool, str]:
    with color_input_border(not valid, imgui.ImColor(1.0, 0.3, 0.3)):
        return imgui.input_text(title, value)


E = typing.TypeVar("E", bound=enum.IntEnum)


def _enum_name(e: enum.Enum) -> str:
    name = e.name
    if name == "_None":
        return "None"
    return name

def enum_combo(item: E, label = "") -> tuple[bool, E]:
    ordered_enums = list(item.__class__)
    all_names = [_enum_name(it) for it in ordered_enums]
    changed, selected = imgui.combo(label, ordered_enums.index(item), all_names)
    return changed, ordered_enums[selected]
