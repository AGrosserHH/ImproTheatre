from __future__ import annotations

import json
from pathlib import Path

from improtheatre.bot.providers import LocalTemplateProvider
from improtheatre.bot.service import SuggestionEngine
from improtheatre.core.models import SceneBrief, Suggestion
from improtheatre.core.storage import HistoryStore, PresetStore
from improtheatre.gui.main_window import MainWindow


def create_window(tmp_path: Path, qapp) -> MainWindow:
    window = MainWindow(
        engine=SuggestionEngine(providers=[LocalTemplateProvider()]),
        history_store=HistoryStore(tmp_path / "history.json"),
        preset_store=PresetStore(tmp_path / "presets.json"),
    )
    window.show()
    qapp.processEvents()
    return window


def test_history_selection_reloads_scene(tmp_path: Path, qapp) -> None:
    window = create_window(tmp_path, qapp)
    brief = SceneBrief(
        location="city hall",
        relationship="mayor and intern",
        energy="tense",
        audience_goal="heighten authority",
    )
    suggestion = Suggestion(
        opening_beat="Start with a crisis briefing.",
        complication="The wrong speech is in the folder.",
        side_coach="Name the status gap.",
        next_line="You are holding the budget and the apology speech.",
    )

    try:
        window.on_suggestion_ready(brief, suggestion)
        window.location_input.clear()
        window.history_list.setCurrentRow(0)
        qapp.processEvents()

        assert window.location_input.text() == "city hall"
        assert "Local Template" in window.output.toPlainText()
    finally:
        window.close()


def test_save_and_load_preset_flow(tmp_path: Path, qapp, monkeypatch) -> None:
    window = create_window(tmp_path, qapp)
    window.location_input.setText("moon base kitchen")
    window.relationship_input.setText("chef and saboteur")
    window.energy_input.setText("paranoid")
    window.audience_goal_input.setText("start fast")

    try:
        monkeypatch.setattr(
            "improtheatre.gui.main_window.QInputDialog.getText",
            lambda *args, **kwargs: ("Moon preset", True),
        )
        window.save_preset()
        qapp.processEvents()

        names = [
            window.preset_list.item(index).text()
            for index in range(window.preset_list.count())
        ]
        assert "Moon preset" in names

        target_row = names.index("Moon preset")
        window.location_input.clear()
        window.preset_list.setCurrentRow(target_row)
        qapp.processEvents()

        assert window.location_input.text() == "moon base kitchen"
    finally:
        window.close()


def test_export_suggestion_and_history(tmp_path: Path, qapp, monkeypatch) -> None:
    window = create_window(tmp_path, qapp)
    brief = SceneBrief(
        location="radio booth",
        relationship="host and producer",
        energy="urgent",
        audience_goal="land a reveal",
    )
    suggestion = Suggestion(
        opening_beat="Open mid-broadcast.",
        complication="The guest is missing.",
        side_coach="Keep naming the unseen danger.",
        next_line="We are on air and somehow less prepared than yesterday.",
    )
    suggestion_path = tmp_path / "suggestion.txt"
    history_path = tmp_path / "history.json"
    save_paths = iter(
        [
            (str(suggestion_path), "Text Files (*.txt)"),
            (str(history_path), "JSON Files (*.json)"),
        ]
    )

    try:
        window.on_suggestion_ready(brief, suggestion)
        monkeypatch.setattr(
            "improtheatre.gui.main_window.QFileDialog.getSaveFileName",
            lambda *args, **kwargs: next(save_paths),
        )

        window.export_suggestion()
        window.export_history()

        assert suggestion_path.exists()
        assert "Open mid-broadcast." in suggestion_path.read_text(encoding="utf-8")

        payload = json.loads(history_path.read_text(encoding="utf-8"))
        assert payload[0]["brief"]["location"] == "radio booth"
    finally:
        window.close()