from __future__ import annotations


class CurrentPopup:
    def render(self) -> bool:
        """Displays the popup. If return is false, it's removed."""
        raise NotImplementedError
