from __future__ import annotations

from threading import Event

from PySide6.QtCore import QObject, QRunnable, Signal

from improtheatre.bot.service import GenerationCancelledError, SuggestionEngine
from improtheatre.core.models import SceneBrief


class SuggestionWorkerSignals(QObject):
    finished = Signal(object)
    partial = Signal(str)
    failed = Signal(str)
    cancelled = Signal(str)
    completed = Signal()


class SuggestionWorker(QRunnable):
    def __init__(self, engine: SuggestionEngine, brief: SceneBrief, provider_id: str) -> None:
        super().__init__()
        self.engine = engine
        self.brief = brief
        self.provider_id = provider_id
        self.cancel_event = Event()
        self.signals = SuggestionWorkerSignals()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            suggestion = self.engine.stream_suggestion(
                self.brief,
                self.provider_id,
                on_update=self.signals.partial.emit,
                cancel_event=self.cancel_event,
            )
        except GenerationCancelledError as exc:
            self.signals.cancelled.emit(str(exc))
        except Exception as exc:
            self.signals.failed.emit(str(exc))
        else:
            self.signals.finished.emit(suggestion)
        finally:
            self.signals.completed.emit()