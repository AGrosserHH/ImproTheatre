from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event
from typing import Protocol
from urllib import error, request

from improtheatre.core.models import SceneBrief, Suggestion


class ProviderError(RuntimeError):
    pass


class ProviderConfigurationError(ProviderError):
    pass


class GenerationCancelledError(ProviderError):
    pass


@dataclass(slots=True, frozen=True)
class ProviderInfo:
    provider_id: str
    label: str
    description: str
    configured: bool


class SuggestionProvider(Protocol):
    provider_id: str
    label: str
    description: str

    def is_configured(self) -> bool:
        ...

    def suggest(
        self,
        brief: SceneBrief,
        on_update: Callable[[str], None] | None = None,
        cancel_event: Event | None = None,
    ) -> Suggestion:
        ...


def ensure_not_cancelled(cancel_event: Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise GenerationCancelledError("Suggestion cancelled.")


def build_prompt(brief: SceneBrief) -> str:
    return "\n".join(
        [
            "You are an improv coach for a local desktop rehearsal app.",
            "Return valid JSON with exactly these keys:",
            "opening_beat, complication, side_coach, next_line",
            "Keep the advice concrete, stageable, and short.",
            f"Location: {brief.location or 'unspecified'}",
            f"Relationship: {brief.relationship or 'unspecified'}",
            f"Energy: {brief.energy or 'balanced'}",
            f"Audience goal: {brief.audience_goal or 'keep the scene moving'}",
        ]
    )


def parse_suggestion_payload(payload: str, provider_id: str, provider_label: str) -> Suggestion:
    text = payload.strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.startswith("```")]
        text = "\n".join(lines).strip()
    data = json.loads(text)
    return Suggestion(
        opening_beat=str(data.get("opening_beat", "")).strip(),
        complication=str(data.get("complication", "")).strip(),
        side_coach=str(data.get("side_coach", "")).strip(),
        next_line=str(data.get("next_line", "")).strip(),
        provider_id=provider_id,
        provider_label=provider_label,
    )


class LocalTemplateProvider:
    provider_id = "local"
    label = "Local Template"
    description = "Fast built-in coach for offline use."

    def is_configured(self) -> bool:
        return True

    def suggest(
        self,
        brief: SceneBrief,
        on_update: Callable[[str], None] | None = None,
        cancel_event: Event | None = None,
    ) -> Suggestion:
        ensure_not_cancelled(cancel_event)
        energy = brief.energy.strip() or "balanced"
        location = brief.location.strip() or "an undefined stage"
        relationship = brief.relationship.strip() or "two performers"
        audience = brief.audience_goal.strip() or "keep the scene moving"

        suggestion = Suggestion(
            opening_beat=(
                f"Start in {location} and reveal the {relationship} dynamic in the first line. "
                f"Play it with a {energy} rhythm."
            ),
            complication=(
                "Drop in a practical problem that makes both characters commit harder "
                f"and {audience}."
            ),
            side_coach=(
                "Say yes to the first odd detail, repeat it, and heighten it on the "
                "next beat."
            ),
            next_line=(
                f"Before you panic about this happening in {location}, remember that I am "
                "the only one"
                " here with a terrible plan and enough confidence to try it."
            ),
            provider_id=self.provider_id,
            provider_label=self.label,
        )
        if on_update is not None:
            on_update(json.dumps(suggestion.to_dict(), indent=2))
        return suggestion


class OllamaProvider:
    provider_id = "ollama"
    label = "Ollama"
    description = "Local LLM via the Ollama HTTP API on this machine."

    def __init__(
        self,
        model: str | None = None,
        endpoint: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.model = model or os.getenv("IMPROTHEATRE_OLLAMA_MODEL", "llama3.2:3b")
        self.endpoint = endpoint or os.getenv(
            "IMPROTHEATRE_OLLAMA_URL", "http://127.0.0.1:11434/api/generate"
        )
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.model and self.endpoint)

    def suggest(
        self,
        brief: SceneBrief,
        on_update: Callable[[str], None] | None = None,
        cancel_event: Event | None = None,
    ) -> Suggestion:
        payload = {
            "model": self.model,
            "prompt": build_prompt(brief),
            "format": "json",
            "stream": True,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                fragments: list[str] = []
                for raw_line in response:
                    ensure_not_cancelled(cancel_event)
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    fragment = str(data.get("response", ""))
                    if fragment:
                        fragments.append(fragment)
                        if on_update is not None:
                            on_update("".join(fragments))
                    if data.get("done"):
                        break
        except error.URLError as exc:
            raise ProviderError(
                "Could not reach Ollama. Start the local Ollama server or switch providers."
            ) from exc

        if not fragments:
            raise ProviderError("Ollama returned an unexpected response.")
        return parse_suggestion_payload("".join(fragments), self.provider_id, self.label)


class OpenAICompatibleProvider:
    provider_id = "openai"
    label = "OpenAI-Compatible"
    description = "Remote or local OpenAI-style chat completion endpoint."

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.base_url = base_url or os.getenv("IMPROTHEATRE_OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = api_key or os.getenv("IMPROTHEATRE_OPENAI_API_KEY", "")
        self.model = model or os.getenv("IMPROTHEATRE_OPENAI_MODEL", "gpt-4.1-mini")
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    def suggest(
        self,
        brief: SceneBrief,
        on_update: Callable[[str], None] | None = None,
        cancel_event: Event | None = None,
    ) -> Suggestion:
        if not self.is_configured():
            raise ProviderConfigurationError(
                "Set IMPROTHEATRE_OPENAI_API_KEY to use the OpenAI-compatible provider."
            )

        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "stream": True,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an improv coach that replies with concise JSON only.",
                },
                {
                    "role": "user",
                    "content": build_prompt(brief),
                },
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        url = self.base_url.rstrip("/") + "/chat/completions"
        req = request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                fragments: list[str] = []
                for raw_line in response:
                    ensure_not_cancelled(cancel_event)
                    line = raw_line.decode("utf-8").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    payload_text = line.removeprefix("data:").strip()
                    if payload_text == "[DONE]":
                        break
                    data = json.loads(payload_text)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    fragment = str(delta.get("content", ""))
                    if fragment:
                        fragments.append(fragment)
                        if on_update is not None:
                            on_update("".join(fragments))
        except error.URLError as exc:
            raise ProviderError(
                "Could not reach the OpenAI-compatible endpoint. Check your URL and network access."
            ) from exc

        if not fragments:
            raise ProviderError(
                "The OpenAI-compatible provider returned an unexpected response."
            )

        return parse_suggestion_payload("".join(fragments), self.provider_id, self.label)