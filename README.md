# ImproTheatre

ImproTheatre is a local desktop app for improv performers. The repository now contains one Python application with two complementary layers:

- a GUI for entering scene context and viewing coaching output
- an internal bot service with pluggable providers for offline, local-LLM, or remote OpenAI-compatible coaching

## Project structure

```text
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

## Provider configuration

### Built-in offline provider

No setup required. Use `Local Template` for a deterministic fallback.

### Ollama provider

Start Ollama locally and optionally set:

```powershell
$env:IMPROTHEATRE_OLLAMA_MODEL = "llama3.2:3b"
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

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
```

## Run

```powershell
python -m improtheatre.app
```

## Test

```powershell
pytest
```

GUI tests run with Qt in offscreen mode and cover history, presets, and export flows.

## Package

```powershell
pip install -e .[packaging]
.\scripts\package.ps1 -Clean
```

This builds a PyInstaller distribution into `dist/ImproTheatre/` using [ImproTheatre.spec](ImproTheatre.spec).
If you have multiple Python installations, set `IMPROTHEATRE_PYTHON` before packaging so PyInstaller uses the intended interpreter.

## Next improvements

1. Add cancellation and streaming updates for longer-running providers.
2. Attach richer scene metadata such as cast size, genre, and taboo topics.
3. Package the application as a distributable desktop build.