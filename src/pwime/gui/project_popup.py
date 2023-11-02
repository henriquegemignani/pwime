from pathlib import Path

from imgui_bundle import imgui
from imgui_bundle._imgui_bundle import portable_file_dialogs

from pwime.gui.popup import CurrentPopup
from pwime.util import imgui_helper


def validate_project_path(s: str) -> bool:
    return s != "" and Path(s).is_dir()


class NewProjectPopup(CurrentPopup):
    _open_popup = True
    project_name: str = ""
    project_path: str = ""
    folder_dialog: portable_file_dialogs.select_folder | None = None

    def _valid_project_path(self) -> bool:
        return validate_project_path(self.project_path)

    def render(self) -> bool:
        result = True

        if self._open_popup:
            imgui.open_popup("New Project")
            self._open_popup = False

        center = imgui.get_main_viewport().get_center()
        imgui.set_next_window_pos(center, imgui.Cond_.appearing, imgui.ImVec2(0.5, 0.5))

        if imgui.begin_popup_modal("New Project", None, imgui.WindowFlags_.always_auto_resize):
            modified, new_name = imgui_helper.validated_input_text(
                "Name", self.project_name,
                self.project_name != ""
            )
            if modified:
                self.project_name = new_name

            imgui.combo("Game", 0, ["Metroid Prime 2"])

            modified, new_path = imgui_helper.validated_input_text(
                "Location", self.project_path,
                self._valid_project_path()
            )
            if modified:
                self.project_path = new_path

            imgui.same_line()
            if imgui.button("Select Folder"):
                self.folder_dialog = portable_file_dialogs.select_folder("Where to create project",
                                                                         self.project_path)
            if self.folder_dialog is not None:
                if self.folder_dialog.ready():
                    new_folder = self.folder_dialog.result()
                    if new_folder:
                        self.project_path = new_folder
                    self.folder_dialog = None

            valid = self._valid_project_path() and self.project_name != ""
            with imgui_helper.disabled(not valid):
                if imgui.button("Create project"):
                    result = False

            imgui.same_line()
            if imgui.button("Cancel"):
                result = False

            imgui.end_popup()

        return result
