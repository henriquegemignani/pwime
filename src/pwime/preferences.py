import dataclasses
import json
from pathlib import Path

from appdirs import AppDirs

from pwime.util.json_lib import JsonObject

roaming_dirs = AppDirs("pwime", False, roaming=True)


@dataclasses.dataclass()
class Preferences:
    prime2_iso: Path | None = None

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
        prime2_iso = data.get("prime2_iso")
        if prime2_iso is not None:
            self.prime2_iso = Path(prime2_iso)

    def to_json(self) -> JsonObject:
        return {
            "prime2_iso": str(self.prime2_iso) if self.prime2_iso is not None else None,
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
