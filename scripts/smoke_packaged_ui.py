from __future__ import annotations

import argparse
import os
import shutil
import tempfile
import time
from pathlib import Path

from pywinauto import Application, Desktop


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument(
        "--exe",
        default=str(
            Path(__file__).resolve().parents[1]
            / "dist"
            / "ImproTheatre"
            / "ImproTheatre.exe"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    isolated_root = Path(tempfile.mkdtemp(prefix="improtheatre-smoke-"))
    os.environ["APPDATA"] = str(isolated_root / "AppData" / "Roaming")
    os.environ["LOCALAPPDATA"] = str(isolated_root / "AppData" / "Local")
    Path(os.environ["APPDATA"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["LOCALAPPDATA"]).mkdir(parents=True, exist_ok=True)

    app = Application(backend="uia").start(args.exe)
    try:
        time.sleep(5)
        windows = Desktop(backend="uia").windows(process=app.process)
        if not windows:
            raise RuntimeError("No top-level windows were exposed by the packaged app.")
        window = next(
            (item for item in windows if item.window_text() == "ImproTheatre"),
            windows[0],
        )
        window.wait("exists enabled ready", timeout=15)
        if args.inspect:
            print("Top-level windows:")
            for item in windows:
                print(f"- {item.window_text()!r} / {item.class_name()}")
            window.print_control_identifiers()
        else:
            print(f"Window started: {window.window_text()!r}")
    finally:
        try:
            app.kill()
        finally:
            shutil.rmtree(isolated_root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())