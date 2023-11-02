import dataclasses
import json
from pathlib import Path

from appdirs import AppDirs

from pwime.util.json_lib import JsonObject

roaming_dirs = AppDirs("pwime", False, roaming=True)


def decode_optional_path(data: JsonObject, key: str) -> Path | None:
    if key in data:
        assert isinstance(data[key], str)
        return Path(data[key])
    return None


def encode_optional_path(path: Path | None) -> str | None:
    if path is not None:
        return str(path)
    return None


@dataclasses.dataclass()
class Preferences:
    prime2_iso: Path | None = None
    last_project_path: Path | None = None

    def read_from_user_home(self) -> None:
        config_path = Path(roaming_dirs.user_config_dir)
        return self.read_from_path(config_path.joinpath("preferences.json"))

    def read_from_path(self, path: Path) -> None:
        try:
            with path.open() as f:
                self.read_from_json(json.load(f))
        except FileNotFoundError:
            pass

    def read_from_json(self, data: JsonObject) -> None:
        self.prime2_iso = decode_optional_path(data, "prime2_iso")
        self.last_project_path = decode_optional_path(data, "last_project_path")

    def to_json(self) -> JsonObject:
        return {
            "prime2_iso": encode_optional_path(self.prime2_iso),
            "last_project_path": encode_optional_path(self.last_project_path),
        }

    def write_to_user_home(self) -> None:
        config_path = Path(roaming_dirs.user_config_dir)
        return self.write_to_path(config_path.joinpath("preferences.json"))

    def write_to_path(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(
            self.to_json(),
            indent=4,
        ))
