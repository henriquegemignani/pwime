from __future__ import annotations

from imgui_bundle import hello_imgui
from retro_data_structures.base_resource import BaseResource


class BaseWindow[T: BaseResource]:
    asset_id: int
    asset: T
    window: hello_imgui.DockableWindow

    def __init__(self, asset_id: int):
        from pwime.gui.gui_state import state

        self.asset_id = asset_id
        self.asset = state().asset_manager.get_file(asset_id)
        self.window = self.create_imgui_window()

    @property
    def window_label(self):
        return f"{self.asset.resource_type()} {self.asset_id:08X}"

    @property
    def default_dock_space(self) -> str:
        return "MainDockSpace"

    def create_imgui_window(self) -> hello_imgui.DockableWindow:
        result = hello_imgui.DockableWindow(
            f"{self.window_label}###Editor{self.asset_id}",
            self.default_dock_space,
            self.render,
            is_visible_=True,
        )
        result.include_in_view_menu = False
        result.remember_is_visible = False
        return result

    def render(self) -> None:
        pass
