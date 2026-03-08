from __future__ import annotations

import json
import os
from pathlib import Path

from improtheatre.core.models import SceneBrief, ScenePreset, SceneRecord


def default_data_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "ImproTheatre"
    return Path.home() / ".improtheatre"


class JsonCollectionStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_payload(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return payload if isinstance(payload, list) else []

    def _save_payload(self, payload: list[dict[str, object]]) -> None:
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class HistoryStore(JsonCollectionStore):
    def __init__(self, path: Path | None = None) -> None:
        super().__init__(path or default_data_dir() / "history.json")

    def load(self) -> list[SceneRecord]:
        return [SceneRecord.from_dict(item) for item in self._load_payload()]

    def save(self, records: list[SceneRecord]) -> None:
        self._save_payload([record.to_dict() for record in records])

    def add(self, record: SceneRecord, limit: int = 50) -> list[SceneRecord]:
        records = self.load()
        records.insert(0, record)
        trimmed = records[:limit]
        self.save(trimmed)
        return trimmed

    def export_json(self, export_path: Path) -> None:
        export_path.write_text(
            json.dumps([record.to_dict() for record in self.load()], indent=2),
            encoding="utf-8",
        )


class PresetStore(JsonCollectionStore):
    def __init__(self, path: Path | None = None) -> None:
        super().__init__(path or default_data_dir() / "presets.json")

    def load(self) -> list[ScenePreset]:
        if not self.path.exists():
            return self.default_presets()
        presets = [ScenePreset.from_dict(item) for item in self._load_payload()]
        return sorted(presets, key=lambda preset: preset.name.lower())

    def save(self, presets: list[ScenePreset]) -> None:
        self._save_payload([preset.to_dict() for preset in presets])

    def upsert(self, preset: ScenePreset) -> list[ScenePreset]:
        presets = [existing for existing in self.load() if existing.name != preset.name]
        presets.append(preset)
        ordered = sorted(presets, key=lambda item: item.name.lower())
        self.save(ordered)
        return ordered

    def delete(self, name: str) -> list[ScenePreset]:
        presets = [preset for preset in self.load() if preset.name != name]
        self.save(presets)
        return presets

    @staticmethod
    def default_presets() -> list[ScenePreset]:
        return [
            ScenePreset(
                name="High-status disaster",
                brief=SceneBrief(
                    location="luxury hotel lobby",
                    relationship="manager and newest concierge",
                    energy="tight and escalating",
                    audience_goal="earn a strong opening laugh",
                ),
            ),
            ScenePreset(
                name="Slow-burn mystery",
                brief=SceneBrief(
                    location="small-town museum archive",
                    relationship="underfunded curator and eager volunteer",
                    energy="patient and curious",
                    audience_goal="build a reveal worth waiting for",
                ),
            ),
        ]