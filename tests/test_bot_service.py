from threading import Event

import pytest

from improtheatre.bot.providers import (
    GenerationCancelledError,
    LocalTemplateProvider,
    parse_suggestion_payload,
)
from improtheatre.bot.service import SuggestionEngine
from improtheatre.core.models import SceneBrief


class FakeStreamingProvider:
    provider_id = "fake"
    label = "Fake Streaming"
    description = "Testing provider"

    def is_configured(self) -> bool:
        return True

    def suggest(self, brief, on_update=None, cancel_event=None):
        fragments = [
            '{"opening_beat": "start"',
            ', "complication": "push"',
            ', "side_coach": "repeat"',
            ', "next_line": "go"}',
        ]
        built = ""
        for fragment in fragments:
            if cancel_event is not None and cancel_event.is_set():
                raise GenerationCancelledError("Suggestion cancelled.")
            built += fragment
            if on_update is not None:
                on_update(built)
        return parse_suggestion_payload(
            built,
            provider_id=self.provider_id,
            provider_label=self.label,
        )


def test_suggestion_engine_uses_scene_brief_values() -> None:
    engine = SuggestionEngine(providers=[LocalTemplateProvider()])

    suggestion = engine.suggest(
        SceneBrief(
            location="train station",
            relationship="siblings",
            energy="urgent",
            audience_goal="land a fast laugh",
        ),
        provider_id="local",
    )

    assert "train station" in suggestion.opening_beat
    assert "siblings" in suggestion.opening_beat
    assert "urgent" in suggestion.opening_beat
    assert "land a fast laugh" in suggestion.complication
    assert suggestion.provider_id == "local"


def test_parse_suggestion_payload_reads_json_content() -> None:
    payload = (
        '{"opening_beat": "start bold", "complication": "raise stakes", '
        '"side_coach": "repeat the game", "next_line": "we are out of time"}'
    )

    suggestion = parse_suggestion_payload(payload, provider_id="ollama", provider_label="Ollama")

    assert suggestion.provider_label == "Ollama"
    assert suggestion.next_line == "we are out of time"


def test_stream_suggestion_emits_partial_updates() -> None:
    engine = SuggestionEngine(providers=[FakeStreamingProvider()])
    updates: list[str] = []

    suggestion = engine.stream_suggestion(
        SceneBrief(
            location="attic",
            relationship="neighbors",
            energy="careful",
            audience_goal="build tension",
        ),
        provider_id="fake",
        on_update=updates.append,
    )

    assert len(updates) == 4
    assert updates[-1].endswith('"next_line": "go"}')
    assert suggestion.provider_id == "fake"


def test_stream_suggestion_can_be_cancelled() -> None:
    engine = SuggestionEngine(providers=[FakeStreamingProvider()])
    cancel_event = Event()
    cancel_event.set()

    with pytest.raises(GenerationCancelledError):
        engine.stream_suggestion(
            SceneBrief(
                location="attic",
                relationship="neighbors",
                energy="careful",
                audience_goal="build tension",
            ),
            provider_id="fake",
            cancel_event=cancel_event,
        )
