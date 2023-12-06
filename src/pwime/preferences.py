import dataclasses
import json
from pathlib import Path

from appdirs import AppDirs
from retro_data_structures.game_check import Game

from pwime.util.json_lib import JsonObject

roaming_dirs = AppDirs("pwime", False, roaming=True)


def decode_optional_path(data: JsonObject, key: str) -> Path | None:
    if data.get(key) is not None:
        assert isinstance(data[key], str)
        return Path(data[key])
    return None


def encode_optional_path(path: Path | None) -> str | None:
    if path is not None:
        return str(path)
    return None


@dataclasses.dataclass()
class Preferences:
    last_project_path: Path | None = None
    game_iso_paths: dict[Game, Path] = dataclasses.field(default_factory=dict)

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
        self.last_project_path = decode_optional_path(data, "last_project_path")
        for game, path in data.get("game_iso_paths", {}).items():
            self.game_iso_paths[getattr(Game, game)] = Path(path)

    def to_json(self) -> JsonObject:
        return {
            "last_project_path": encode_optional_path(self.last_project_path),
            "game_iso_paths": {
                game.name: str(path)
                for game, path in self.game_iso_paths.items()
            }
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
