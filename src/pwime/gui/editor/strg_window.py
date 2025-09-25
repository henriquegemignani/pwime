from __future__ import annotations

from imgui_bundle import imgui
from retro_data_structures.formats import Strg

from pwime.gui.editor.base_window import BaseWindow


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
                    self.asset.set_single_string(i, new_text,
                                                 None if self.change_all_languages else languages[self.language_index])

            imgui.end_table()
