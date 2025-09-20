import typing
from pathlib import Path

from imgui_bundle import imgui
from imgui_bundle import portable_file_dialogs

from pwime.util import imgui_helper


class PathPrompt:
    _prompt_dialog: portable_file_dialogs.select_folder | portable_file_dialogs.open_file | None = None

    def __init__(
        self,
        title: str,
        prompt_text: str,
        initial_value: str,
        validator: typing.Callable[[str], bool],
    ):
        self._title = title
        self._prompt_text = prompt_text
        self.value = initial_value
        self._validator = validator

    def validate(self) -> bool:
        return self._validator(self.value)

    def render(self):
        modified, new_value = imgui_helper.validated_input_text(self._title, self.value, self._validator(self.value))
        if modified:
            self.value = new_value

        imgui.same_line()
        self._render_select_path_button()

        if self._prompt_dialog is not None:
            if self._prompt_dialog.ready():
                new_value = self._prompt_dialog.result()
                if new_value:
                    if isinstance(new_value, list):
                        self.value = new_value[0]
                    else:
                        self.value = new_value
                self._prompt_dialog = None

    def _render_select_path_button(self):
        raise NotImplementedError()


def _valid_existing_iso_path(path: str) -> bool:
    p = Path(path)
    return p.suffix == ".iso" and p.is_file()


def _valid_new_iso_path(path: str) -> bool:
    p = Path(path)
    return p.suffix == ".iso" and p.parent.is_dir()


class FilePrompt(PathPrompt):
    def __init__(
        self,
        title: str,
        prompt_text: str,
        select_text: str,
        filters: list[str],
        initial_value: str,
        validator: typing.Callable[[str], bool],
        save_file: bool,
    ):
        super().__init__(
            title,
            prompt_text,
            initial_value,
            validator,
        )
        self._select_text = select_text
        self._filters = filters
        if save_file:
            self._dialog_class = portable_file_dialogs.save_file
        else:
            self._dialog_class = portable_file_dialogs.open_file

    def _render_select_path_button(self):
        if imgui.button(self._select_text):
            self._prompt_dialog = self._dialog_class(
                self._prompt_text,
                self.value,
                filters=self._filters,
            )


class IsoPrompt(FilePrompt):
    def __init__(self, initial_value: str, save_file: bool, title: str = "Game ISO"):
        super().__init__(
            title,
            "Path to a game ISO",
            "Select ISO",
            ["*.iso"],
            initial_value,
            _valid_new_iso_path if save_file else _valid_existing_iso_path,
            save_file,
        )


class FolderPrompt(PathPrompt):
    def _render_select_path_button(self):
        if imgui.button("Select Folder"):
            self._prompt_dialog = portable_file_dialogs.select_folder(self._prompt_text, self.value)
