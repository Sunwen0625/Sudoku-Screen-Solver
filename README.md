# Sudoku Screen Solver

Windows desktop tool for recognizing and auto-filling Sudoku puzzles from a screen capture.

## Install

```powershell
poetry install
```

## Command Line

Dry run against an image:

```powershell
poetry run python -m sudoku_solver --image gameOriginal.jpg --dry-run
```

Auto-fill the current screen:

```powershell
poetry run python -m sudoku_solver --auto
```

## Windows GUI

Start the quick GUI:

```powershell
poetry run sudoku-gui
```

Build a standalone Windows executable:

```powershell
poetry run python build_windows_exe.py
```

The executable will be created at `dist\SudokuQuickGUI.exe`.

In the GUI:

1. Pick a window from the dropdown, or browse an image for testing.
2. Click `Dry Run` to verify recognition.
3. Click `Auto Run` to tap cells and digits automatically.
4. If the game shows the waiting overlay, the app will pause until it disappears.

## Notes

- `--window-title` captures a live window and applies the click offsets correctly.
- `--image` is for offline testing and does not click.
- PyAutoGUI fail-safe is enabled. Move the mouse to the top-left corner to stop automation.
