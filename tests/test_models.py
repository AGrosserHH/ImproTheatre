from improtheatre.core.models import SceneBrief, ScenePreset, SceneRecord, Suggestion


def test_scene_brief_and_suggestion_are_constructible() -> None:
    brief = SceneBrief(
        location="museum",
        relationship="strangers",
        energy="dry",
        audience_goal="build a patient reveal",
    )
    suggestion = Suggestion(
        opening_beat="start small",
        complication="raise stakes",
        side_coach="name the game",
        next_line="we should not be here",
    )

    assert brief.location == "museum"
    assert suggestion.next_line == "we should not be here"


def test_scene_record_and_preset_round_trip() -> None:
    brief = SceneBrief(
        location="harbor",
        relationship="siblings",
        energy="chaotic",
        audience_goal="heighten quickly",
    )
    suggestion = Suggestion(
        opening_beat="start mid-argument",
        complication="the boat is missing",
        side_coach="use specifics",
        next_line="you lost the lighthouse?",
        provider_id="local",
        provider_label="Local Template",
    )
    record = SceneRecord(brief=brief, suggestion=suggestion)
    preset = ScenePreset(name="Dock panic", brief=brief)

    assert SceneRecord.from_dict(record.to_dict()).brief.location == "harbor"
    assert ScenePreset.from_dict(preset.to_dict()).name == "Dock panic"
