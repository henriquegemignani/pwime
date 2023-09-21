from __future__ import annotations

JsonObject = dict[str, "JsonValue"]
JsonArray = list["JsonValue"]
JsonValue = str | int | float | JsonObject | JsonArray | None
