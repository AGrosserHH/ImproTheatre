from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(slots=True)
class SceneBrief:
    location: str
    relationship: str
    energy: str
    audience_goal: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> SceneBrief:
        return cls(
            location=str(data.get("location", "")),
            relationship=str(data.get("relationship", "")),
            energy=str(data.get("energy", "")),
            audience_goal=str(data.get("audience_goal", "")),
        )

    def summary(self) -> str:
        location = self.location.strip() or "open scene"
        relationship = self.relationship.strip() or "unknown dynamic"
        return f"{location} | {relationship}"


@dataclass(slots=True)
class Suggestion:
    opening_beat: str
    complication: str
    side_coach: str
    next_line: str
    provider_id: str = "local"
    provider_label: str = "Local Template"
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Suggestion:
        return cls(
            opening_beat=str(data.get("opening_beat", "")),
            complication=str(data.get("complication", "")),
            side_coach=str(data.get("side_coach", "")),
            next_line=str(data.get("next_line", "")),
            provider_id=str(data.get("provider_id", "local")),
            provider_label=str(data.get("provider_label", "Local Template")),
            created_at=str(data.get("created_at", utc_now_iso())),
        )

    def format_for_display(self) -> str:
        return "\n\n".join(
            [
                f"Provider\n{self.provider_label}",
                f"Opening beat\n{self.opening_beat}",
                f"Complication\n{self.complication}",
                f"Side coach\n{self.side_coach}",
                f"Next line\n{self.next_line}",
            ]
        )


@dataclass(slots=True)
class SceneRecord:
    brief: SceneBrief
    suggestion: Suggestion

    def to_dict(self) -> dict[str, object]:
        return {
            "brief": self.brief.to_dict(),
            "suggestion": self.suggestion.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> SceneRecord:
        brief_data = data.get("brief")
        suggestion_data = data.get("suggestion")
        return cls(
            brief=SceneBrief.from_dict(brief_data if isinstance(brief_data, dict) else {}),
            suggestion=Suggestion.from_dict(
                suggestion_data if isinstance(suggestion_data, dict) else {}
            ),
        )

    def label(self) -> str:
        created_at = self.suggestion.created_at.replace("T", " ")[:16]
        return f"{created_at} | {self.brief.summary()}"


@dataclass(slots=True)
class ScenePreset:
    name: str
    brief: SceneBrief

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "brief": self.brief.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ScenePreset:
        brief_data = data.get("brief")
        return cls(
            name=str(data.get("name", "Untitled preset")),
            brief=SceneBrief.from_dict(brief_data if isinstance(brief_data, dict) else {}),
        )
