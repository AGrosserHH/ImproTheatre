from __future__ import annotations

from collections.abc import Callable
from threading import Event

from improtheatre.bot.providers import (
    GenerationCancelledError,
    LocalTemplateProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    ProviderConfigurationError,
    ProviderError,
    ProviderInfo,
    SuggestionProvider,
)
from improtheatre.core.models import SceneBrief, Suggestion


class SuggestionEngine:
    def __init__(self, providers: list[SuggestionProvider] | None = None) -> None:
        self.providers = {
            provider.provider_id: provider
            for provider in (providers or self.default_providers())
        }

    @staticmethod
    def default_providers() -> list[SuggestionProvider]:
        return [LocalTemplateProvider(), OllamaProvider(), OpenAICompatibleProvider()]

    def list_providers(self) -> list[ProviderInfo]:
        infos = [
            ProviderInfo(
                provider_id=provider.provider_id,
                label=provider.label,
                description=provider.description,
                configured=provider.is_configured(),
            )
            for provider in self.providers.values()
        ]
        return sorted(infos, key=lambda item: item.label.lower())

    def suggest(self, brief: SceneBrief, provider_id: str) -> Suggestion:
        return self.stream_suggestion(brief, provider_id)

    def stream_suggestion(
        self,
        brief: SceneBrief,
        provider_id: str,
        on_update: Callable[[str], None] | None = None,
        cancel_event: Event | None = None,
    ) -> Suggestion:
        provider = self.providers.get(provider_id)
        if provider is None:
            raise ProviderError(f"Unknown provider: {provider_id}")
        if not provider.is_configured():
            raise ProviderConfigurationError(
                f"{provider.label} is not configured on this machine yet."
            )
        return provider.suggest(brief, on_update=on_update, cancel_event=cancel_event)


__all__ = ["GenerationCancelledError", "SuggestionEngine"]
