from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Self, override

from imgui_bundle import imgui
from retro_data_structures.formats import Strg

from pwime.gui.editor.base_window import BaseWindow
from pwime.operations.base import Operation

if TYPE_CHECKING:
    from pwime.project import Project
    from pwime.util.json_lib import JsonObject


@dataclasses.dataclass()
class StrgEditOperation(Operation):
    """Represents a STRG change.."""
    asset_id: int
    index: int
    new_text: str
    language: str | None
    old_value: list[str] | str | None = None

    @override
    def perform(self, project: Project) -> None:
        """Performs the change."""
        asset = project.asset_manager.get_file(self.asset_id, type_hint=Strg)
        if self.language is None:
            self.old_value = [asset.get_strings(language)[self.index] for language in asset.get_language_list()]
        else:
            self.old_value = asset.get_strings(self.language)[self.index]
        asset.set_single_string(self.index, self.new_text, self.language)

    @override
    def undo(self, project: Project) -> None:
        assert self.old_value is not None

        asset = project.asset_manager.get_file(self.asset_id, type_hint=Strg)
        if self.language is None:
            for language, old in zip(asset.get_language_list(), self.old_value, strict=True):
                asset.set_single_string(self.index, old, language)
        else:
            asset.set_single_string(self.index, self.old_value, self.language)

    @override
    def to_json(self) -> JsonObject:
        return {
            "kind": "strg_edit",
            "asset_id": self.asset_id,
            "index": self.index,
            "new_text": self.new_text,
            "language": self.language,
            "old_value": self.old_value,
        }

    @classmethod
    def from_json(cls, data: JsonObject) -> Self:
        return cls(
            asset_id=data["asset_id"],
            index=data["index"],
            new_text=data["new_text"],
            language=data["language"],
            old_value=data["old_value"],
        )

    @override
    def overwrites_operation(self, operation: Operation) -> bool:
        if not isinstance(operation, StrgEditOperation):
            return False

        overwrite_language = self.language is None or operation.language == self.language
        return operation.asset_id == self.asset_id and overwrite_language and operation.index == self.index

    @override
    def describe(self) -> str:
        """Human-readable description of this operation. For use in the history tab."""
        return f"Edit string {self.index} of STRG 0x{self.asset_id:08X}"



class StrgWindow(BaseWindow[Strg]):
    use_multirow: bool = False
    language_index: int = 0
    change_all_languages: bool = False

    def render(self) -> None:
        languages = list(self.asset.get_language_list())

        name_table = {
            idx: name
            for name, idx in self.asset.raw.name_table.items()
        }

        self.use_multirow = imgui.checkbox("Use multirow input", self.use_multirow)[1]
        self.change_all_languages = imgui.checkbox("Change all languages", self.change_all_languages)[1]

        changed, selected = imgui.combo("Language", self.language_index, languages)
        if changed:
            self.language_index = selected

        if imgui.begin_table(
                f"Strings for {languages[self.language_index]}", 4,
                imgui.TableFlags_.row_bg | imgui.TableFlags_.borders_h | imgui.TableFlags_.resizable | imgui.TableFlags_.scroll_y
        ):
            strings = self.asset.get_strings(languages[self.language_index])

            imgui.table_setup_column("Idx", imgui.TableColumnFlags_.width_fixed)
            imgui.table_setup_column("Name")
            imgui.table_setup_column("String")
            imgui.table_setup_scroll_freeze(3, 1)
            imgui.table_headers_row()

            for i, s in enumerate(strings):
                imgui.table_next_row()

                imgui.table_next_column()
                imgui.text(str(i))

                imgui.table_next_column()
                imgui.text(name_table.get(i, ""))

                imgui.table_next_column()
                text_func = imgui.input_text_multiline if self.use_multirow else imgui.input_text
                changed, new_text = text_func(f"###entry_{i}_{self.language_index}", s)
                if changed:
                    from pwime.gui.gui_state import state
                    state().project.add_new_operation(
                        StrgEditOperation(
                            asset_id=self.asset_id,
                            index=i,
                            new_text=new_text,
                            language=None if self.change_all_languages else languages[self.language_index],
                        )
                    )

            imgui.end_table()
