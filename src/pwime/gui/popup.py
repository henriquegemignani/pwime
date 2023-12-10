from __future__ import annotations

from imgui_bundle import imgui


class CurrentPopup:
    def render(self) -> bool:
        """Displays the popup. If return is false, it's removed."""
        raise NotImplementedError


class CurrentImguiPopup(CurrentPopup):
    """Renders an imgui popup_modal as the popup"""
    _open_popup: bool = True

    def _popup_name(self) -> str:
        """The imgui popup modal name."""
        raise NotImplementedError

    def render_modal(self) -> bool:
        """Same as render, but already has the imgui popup context open."""
        raise NotImplementedError

    def render(self) -> bool:
        result = True

        if self._open_popup:
            imgui.open_popup(self._popup_name())
            self._open_popup = False

        center = imgui.get_main_viewport().get_center()
        imgui.set_next_window_pos(center, imgui.Cond_.appearing, imgui.ImVec2(0.5, 0.5))

        if imgui.begin_popup_modal(self._popup_name(), None):
            result = self.render_modal()

            imgui.end_popup()

        return result