from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "SudokuQuickGUI",
        "--collect-all",
        "pyautogui",
        "--collect-all",
        "pygetwindow",
        "--collect-all",
        "PIL",
        str(ROOT / "gui_launcher.py"),
    ]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
