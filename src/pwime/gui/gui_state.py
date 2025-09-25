from __future__ import annotations

import dataclasses
import functools
import typing
from typing import TYPE_CHECKING

from imgui_bundle._imgui_bundle import hello_imgui
from retro_data_structures.asset_manager import IsoFileProvider
from retro_data_structures.game_check import Game

from pwime.asset_manager import OurAssetManager
from pwime.gui.editor.base_window import BaseWindow
from pwime.gui.popup import CurrentPopup
from pwime.preferences import Preferences
from pwime.project import Project

if TYPE_CHECKING:
    from pathlib import Path

    from imgui_bundle import portable_file_dialogs

    from pwime.gui.area import AreaState
    from pwime.gui.script_instance import ScriptInstanceState


class FilteredAssetList(typing.NamedTuple):
    types: frozenset[str]
    filter: str
    ids: list[int]


@dataclasses.dataclass()
class GuiState:
    area_state: AreaState
    instance_state: ScriptInstanceState
    preferences: Preferences
    editors: dict[int, BaseWindow] = dataclasses.field(default_factory=dict)
    file_providers: dict[Game, IsoFileProvider] = dataclasses.field(default_factory=dict)
    project: Project | None = None
    current_project_path: Path | None = None
    current_popup: CurrentPopup | None = None
    open_file_dialog: portable_file_dialogs.open_file = None
    selected_asset: int | None = None
    pending_pre_frame_tasks: list[typing.Callable[[], None]] = dataclasses.field(default_factory=list)
    selected_asset_types: set[str] = dataclasses.field(default_factory=lambda: {"MLVL"})
    asset_filter: str = ""

    @property
    def asset_manager(self) -> OurAssetManager | None:
        if self.project is None:
            return None
        return self.project.asset_manager

    def open_project(self, path: Path) -> None:
        self.project = Project.load_from_file(path, self.file_providers)
        self.current_project_path = path

    def filtered_asset_list(self, asset_types: frozenset[str], name_filter: str) -> FilteredAssetList:
        return FilteredAssetList(
            asset_types,
            name_filter,
            [
                asset
                for asset in self.asset_manager.all_asset_ids()
                if self.asset_manager.get_asset_type(asset) in asset_types
                   and (not name_filter or name_filter in self.asset_manager.asset_names.get(asset, "<unknown>"))
            ],
        )

    def load_iso(self, game: Game, iso: Path) -> None:
        self.file_providers[game] = IsoFileProvider(iso)

    def restore_from_preferences(self):
        for game, path in self.preferences.game_iso_paths.items():
            self.load_iso(game, path)

        if self.preferences.last_project_path:
            self.open_project(self.preferences.last_project_path)

    def open_editor_for(self, asset_id: int, window_class: type[BaseWindow]) -> None:
        if asset_id not in self.editors:
            self.editors[asset_id] = window_class(asset_id)
            hello_imgui.add_dockable_window(self.editors[asset_id].create_imgui_window())


@functools.cache
def state() -> GuiState:
    from pwime.gui.area import AreaState
    from pwime.gui.script_instance import ScriptInstanceState

    return GuiState(AreaState(), ScriptInstanceState(), Preferences())
