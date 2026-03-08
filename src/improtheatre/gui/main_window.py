from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from improtheatre.bot.service import SuggestionEngine
from improtheatre.core.models import SceneBrief, ScenePreset, SceneRecord, Suggestion
from improtheatre.core.storage import HistoryStore, PresetStore
from improtheatre.gui.workers import SuggestionWorker


class MainWindow(QMainWindow):
    def __init__(
        self,
        engine: SuggestionEngine,
        history_store: HistoryStore | None = None,
        preset_store: PresetStore | None = None,
    ) -> None:
        super().__init__()
        self.engine = engine
        self.history_store = history_store or HistoryStore()
        self.preset_store = preset_store or PresetStore()
        self.history_records = self.history_store.load()
        self.presets = self.preset_store.load()
        self.current_suggestion: Suggestion | None = None
        self.current_brief: SceneBrief | None = None
        self.current_provider_label = ""
        self.thread_pool = QThreadPool(self)
        self.current_worker: SuggestionWorker | None = None
        self.setWindowTitle("ImproTheatre")
        self.resize(1180, 720)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("bakery at closing time")
        self.relationship_input = QLineEdit()
        self.relationship_input.setPlaceholderText("rivals forced to work together")
        self.energy_input = QLineEdit()
        self.energy_input.setPlaceholderText("playful, tense, chaotic")
        self.audience_goal_input = QLineEdit()
        self.audience_goal_input.setPlaceholderText("earn a strong first laugh")

        self.provider_combo = QComboBox()
        self.populate_provider_combo()

        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.history_list = QListWidget()
        self.history_list.itemSelectionChanged.connect(self.load_selected_history)
        self.preset_list = QListWidget()
        self.preset_list.itemSelectionChanged.connect(self.load_selected_preset_preview)

        self.status_label = QLabel("Enter a scene brief and generate a suggestion.")

        self.generate_button = QPushButton("Generate coaching beat")
        self.generate_button.clicked.connect(self.generate_suggestion)
        self.save_preset_button = QPushButton("Save preset")
        self.save_preset_button.clicked.connect(self.save_preset)
        self.delete_preset_button = QPushButton("Delete preset")
        self.delete_preset_button.clicked.connect(self.delete_preset)
        self.copy_button = QPushButton("Copy suggestion")
        self.copy_button.clicked.connect(self.copy_suggestion)
        self.export_button = QPushButton("Export suggestion")
        self.export_button.clicked.connect(self.export_suggestion)
        self.export_history_button = QPushButton("Export history")
        self.export_history_button.clicked.connect(self.export_history)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_generation)
        self.cancel_button.setEnabled(False)

        form = QFormLayout()
        form.addRow("Provider", self.provider_combo)
        form.addRow("Location", self.location_input)
        form.addRow("Relationship", self.relationship_input)
        form.addRow("Energy", self.energy_input)
        form.addRow("Audience goal", self.audience_goal_input)

        brief_group = QGroupBox("Scene brief")
        brief_group.setLayout(form)

        controls = QHBoxLayout()
        controls.addWidget(self.generate_button)
        controls.addWidget(self.save_preset_button)
        controls.addWidget(self.copy_button)
        controls.addWidget(self.export_button)
        controls.addWidget(self.export_history_button)
        controls.addWidget(self.cancel_button)
        controls.addStretch(1)

        preset_controls = QHBoxLayout()
        preset_controls.addWidget(self.delete_preset_button)
        preset_controls.addStretch(1)

        preset_layout = QVBoxLayout()
        preset_layout.addWidget(self.preset_list)
        preset_layout.addLayout(preset_controls)
        preset_group = QGroupBox("Saved presets")
        preset_group.setLayout(preset_layout)

        history_layout = QVBoxLayout()
        history_layout.addWidget(self.history_list)
        history_group = QGroupBox("Scene history")
        history_group.setLayout(history_layout)

        sidebar = QVBoxLayout()
        sidebar.addWidget(preset_group, stretch=1)
        sidebar.addWidget(history_group, stretch=2)
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)

        editor_layout = QVBoxLayout()
        editor_layout.addWidget(brief_group)
        editor_layout.addLayout(controls)
        editor_layout.addWidget(self.output, stretch=1)
        editor_layout.addWidget(self.status_label)
        editor_widget = QWidget()
        editor_widget.setLayout(editor_layout)

        splitter = QSplitter()
        splitter.addWidget(editor_widget)
        splitter.addWidget(sidebar_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout()
        layout.addWidget(splitter)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.refresh_presets()
        self.refresh_history()

    def populate_provider_combo(self) -> None:
        self.provider_combo.clear()
        for info in self.engine.list_providers():
            label = info.label if info.configured else f"{info.label} (setup required)"
            self.provider_combo.addItem(label, info.provider_id)

    def current_brief_from_form(self) -> SceneBrief:
        return SceneBrief(
            location=self.location_input.text(),
            relationship=self.relationship_input.text(),
            energy=self.energy_input.text(),
            audience_goal=self.audience_goal_input.text(),
        )

    def set_form_enabled(self, enabled: bool) -> None:
        self.generate_button.setEnabled(enabled)
        self.save_preset_button.setEnabled(enabled)
        self.provider_combo.setEnabled(enabled)
        self.cancel_button.setEnabled(not enabled)

    def generate_suggestion(self) -> None:
        if self.current_worker is not None:
            return
        brief = self.current_brief_from_form()
        provider_id = str(self.provider_combo.currentData())
        self.current_suggestion = None
        self.current_provider_label = self.provider_combo.currentText().replace(
            " (setup required)", ""
        )
        worker = SuggestionWorker(self.engine, brief, provider_id)
        worker.signals.partial.connect(self.on_partial_response)
        worker.signals.finished.connect(
            lambda suggestion: self.on_suggestion_ready(brief, suggestion)
        )
        worker.signals.cancelled.connect(self.on_suggestion_cancelled)
        worker.signals.failed.connect(self.on_suggestion_failed)
        worker.signals.completed.connect(lambda: self.on_worker_completed(worker))
        self.current_worker = worker
        self.set_form_enabled(False)
        self.output.setPlainText("Generating suggestion...")
        self.status_label.setText("Running coach in the background...")
        self.thread_pool.start(worker)

    def cancel_generation(self) -> None:
        if self.current_worker is None:
            return
        self.current_worker.cancel()
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Cancelling suggestion...")

    def on_partial_response(self, partial_text: str) -> None:
        if not partial_text.strip():
            return
        self.output.setPlainText(
            f"Streaming from {self.current_provider_label}...\n\n{partial_text}"
        )

    def on_suggestion_ready(self, brief: SceneBrief, suggestion: Suggestion) -> None:
        self.current_brief = brief
        self.current_suggestion = suggestion
        self.output.setPlainText(suggestion.format_for_display())
        self.history_records = self.history_store.add(
            SceneRecord(brief=brief, suggestion=suggestion)
        )
        self.refresh_history()
        self.status_label.setText(f"Suggestion ready from {suggestion.provider_label}.")

    def on_suggestion_failed(self, message: str) -> None:
        self.output.clear()
        self.status_label.setText(message)
        QMessageBox.warning(self, "Suggestion failed", message)

    def on_suggestion_cancelled(self, message: str) -> None:
        self.status_label.setText(message)

    def on_worker_completed(self, worker: SuggestionWorker) -> None:
        if self.current_worker is worker:
            self.current_worker = None
        self.set_form_enabled(True)

    def refresh_history(self) -> None:
        self.history_list.clear()
        for record in self.history_records:
            self.history_list.addItem(record.label())

    def refresh_presets(self) -> None:
        self.preset_list.clear()
        for preset in self.presets:
            self.preset_list.addItem(preset.name)

    def load_selected_history(self) -> None:
        row = self.history_list.currentRow()
        if row < 0 or row >= len(self.history_records):
            return
        record = self.history_records[row]
        self.apply_brief(record.brief)
        self.current_brief = record.brief
        self.current_suggestion = record.suggestion
        self.output.setPlainText(record.suggestion.format_for_display())
        self.status_label.setText(
            f"Loaded scene from history using {record.suggestion.provider_label}."
        )

    def load_selected_preset_preview(self) -> None:
        row = self.preset_list.currentRow()
        if row < 0 or row >= len(self.presets):
            return
        preset = self.presets[row]
        self.apply_brief(preset.brief)
        self.status_label.setText(f"Loaded preset: {preset.name}")

    def apply_brief(self, brief: SceneBrief) -> None:
        self.location_input.setText(brief.location)
        self.relationship_input.setText(brief.relationship)
        self.energy_input.setText(brief.energy)
        self.audience_goal_input.setText(brief.audience_goal)

    def save_preset(self) -> None:
        name, accepted = QInputDialog.getText(self, "Save preset", "Preset name")
        if not accepted or not name.strip():
            return
        preset = ScenePreset(name=name.strip(), brief=self.current_brief_from_form())
        self.presets = self.preset_store.upsert(preset)
        self.refresh_presets()
        self.status_label.setText(f"Preset saved: {preset.name}")

    def delete_preset(self) -> None:
        row = self.preset_list.currentRow()
        if row < 0 or row >= len(self.presets):
            return
        preset = self.presets[row]
        self.presets = self.preset_store.delete(preset.name)
        self.refresh_presets()
        self.status_label.setText(f"Preset deleted: {preset.name}")

    def copy_suggestion(self) -> None:
        if self.current_suggestion is None:
            self.status_label.setText("Generate or load a suggestion before copying.")
            return
        QApplication.clipboard().setText(self.current_suggestion.format_for_display())
        self.status_label.setText("Suggestion copied to clipboard.")

    def export_suggestion(self) -> None:
        if self.current_suggestion is None:
            self.status_label.setText("Generate or load a suggestion before exporting.")
            return
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export suggestion",
            str(Path.home() / "impro-suggestion.txt"),
            "Text Files (*.txt)",
        )
        if not export_path:
            return
        Path(export_path).write_text(self.current_suggestion.format_for_display(), encoding="utf-8")
        self.status_label.setText(f"Suggestion exported to {export_path}")

    def export_history(self) -> None:
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export scene history",
            str(Path.home() / "impro-history.json"),
            "JSON Files (*.json)",
        )
        if not export_path:
            return
        self.history_store.export_json(Path(export_path))
        self.status_label.setText(f"History exported to {export_path}")
