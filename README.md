# ImproTheatre

ImproTheatre is a local desktop app for improv performers. The repository now contains one Python application with two complementary layers:

- a GUI for entering scene context and viewing coaching output
- an internal bot service with pluggable providers for offline, local-LLM, or remote OpenAI-compatible coaching

## What this repo contains

This repository is a single Python desktop application. It is not split into separate bot and GUI repositories anymore.

- The GUI is built with `PySide6`.
- The app logic lives in a single package under `src/improtheatre`.
- Suggestion generation supports multiple providers.
- Tests cover core logic, persistence, and GUI flows.

## Project structure

```text
scripts/             # helper scripts for packaging and smoke tests
src/improtheatre/
	app.py          # desktop entry point
	bot/            # provider registry and coaching services
	core/           # shared domain models
	gui/            # PySide6 desktop interface and background workers
tests/            # smoke tests for shared logic
```

## Features

- Provider selection in the desktop UI.
- Background suggestion generation so slower providers do not block the window.
- Cancellation and streamed partial responses for long-running providers.
- Persistent scene history and saved presets stored in the local user profile.
- Export current suggestions to text and export full history to JSON.
- Clipboard copy support for quick sharing.

## Requirements

Before you start, make sure you have:

- Windows with PowerShell available.
- Python `3.11+` installed. The project currently runs on Python `3.13.5` in this repo.
- `pip` available for package installation.
- Optional: Ollama installed locally if you want real local LLM suggestions.
- Optional: an OpenAI-compatible API key and endpoint if you want remote provider support.

## First-time setup

Create and activate a virtual environment, then install the project in editable mode.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
```

If you also want to build a desktop distribution:

```powershell
pip install -e .[dev,packaging]
```

## How to start the app

From the repository root:

```powershell
python -m improtheatre.app
```

You can also use the installed console script:

```powershell
improtheatre
```

## Provider setup

You can run the app with no external service at all, or connect it to a local or remote model provider.

### Built-in offline provider

No setup required. Use `Local Template` for a deterministic fallback.

### Ollama provider

Install and start Ollama locally, then pull a model. Example:

```powershell
ollama pull qwen2.5:0.5b
```

Set the provider environment values if needed:

```powershell
$env:IMPROTHEATRE_OLLAMA_MODEL = "qwen2.5:0.5b"
$env:IMPROTHEATRE_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
```

The UI streams partial text while Ollama is generating and lets you cancel mid-request.

### OpenAI-compatible provider

Set:

```powershell
$env:IMPROTHEATRE_OPENAI_API_KEY = "..."
$env:IMPROTHEATRE_OPENAI_MODEL = "gpt-4.1-mini"
$env:IMPROTHEATRE_OPENAI_BASE_URL = "https://api.openai.com/v1"
```

If the endpoint supports SSE chat streaming, partial responses are shown live in the window.

## How to work with the repo

The main day-to-day workflow is:

1. Activate the virtual environment.
2. Install dependencies with editable mode.
3. Run the test suite before and after changes.
4. Start the desktop app locally to verify the GUI behavior.
5. If you touch packaging, rebuild the distribution in `dist/`.

Typical development session:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
pytest
python -m improtheatre.app
```

## Common development commands

Install or refresh dev dependencies:

```powershell
pip install -e .[dev]
```

Run all tests:

```powershell
pytest
```

Run linting:

```powershell
ruff check .
```

GUI tests run with Qt in offscreen mode and cover history, presets, and export flows.

## Key files to know

- `pyproject.toml`: package metadata, dependencies, pytest config, Ruff config.
- `src/improtheatre/app.py`: app entry point.
- `src/improtheatre/bot/providers.py`: provider implementations and streaming logic.
- `src/improtheatre/bot/service.py`: provider selection and orchestration.
- `src/improtheatre/gui/main_window.py`: main desktop window and user flows.
- `src/improtheatre/gui/workers.py`: background worker logic for suggestion generation.
- `src/improtheatre/core/storage.py`: local history and preset persistence.
- `tests/`: regression coverage for service, models, storage, and GUI flows.

## Package

```powershell
pip install -e .[dev,packaging]
.\scripts\package.ps1 -Clean
```

This builds a PyInstaller distribution into `dist/ImproTheatre/` using [ImproTheatre.spec](ImproTheatre.spec).
If you have multiple Python installations, set `IMPROTHEATRE_PYTHON` before packaging so PyInstaller uses the intended interpreter.

Example:

```powershell
$env:IMPROTHEATRE_PYTHON = "C:\Users\you\AppData\Local\Programs\Python\Python313\python.exe"
.\scripts\package.ps1 -Clean
```

## Smoke testing the packaged app

After packaging, the built executable is here:

```text
dist/ImproTheatre/ImproTheatre.exe
```

You can also run the helper script used for packaged smoke testing:

```powershell
python .\scripts\smoke_packaged_ui.py
```

## Local data and generated files

- User history and presets are stored under the current user's app-data location.
- `build/` and `dist/` are generated by PyInstaller.
- `.venv/`, `.pytest_cache/`, and `.ruff_cache/` are local development artifacts.

## Next improvements

1. Add cancellation and streaming updates for longer-running providers.
2. Attach richer scene metadata such as cast size, genre, and taboo topics.
3. Package the application as a distributable desktop build.