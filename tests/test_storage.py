from pathlib import Path

from improtheatre.core.models import SceneBrief, ScenePreset, SceneRecord, Suggestion
from improtheatre.core.storage import HistoryStore, PresetStore


def test_history_store_adds_newest_record_first(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "history.json")
    record = SceneRecord(
        brief=SceneBrief(
            location="station",
            relationship="coworkers",
            energy="fast",
            audience_goal="get to the joke quickly",
        ),
        suggestion=Suggestion(
            opening_beat="arrive late",
            complication="train is gone",
            side_coach="raise the stakes",
            next_line="we missed the one thing we had to catch",
        ),
    )

    records = store.add(record)

    assert len(records) == 1
    assert store.load()[0].brief.location == "station"


def test_preset_store_upserts_and_deletes(tmp_path: Path) -> None:
    store = PresetStore(tmp_path / "presets.json")
    preset = ScenePreset(
        name="Kitchen trouble",
        brief=SceneBrief(
            location="restaurant kitchen",
            relationship="chef and food critic",
            energy="sharp",
            audience_goal="create pressure immediately",
        ),
    )

    presets = store.upsert(preset)

    assert any(item.name == "Kitchen trouble" for item in presets)
    assert any(item.name == "Kitchen trouble" for item in store.load())

    after_delete = store.delete("Kitchen trouble")

    assert all(item.name != "Kitchen trouble" for item in after_delete)