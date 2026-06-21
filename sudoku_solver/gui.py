from __future__ import annotations

import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk

from .automation import fill_solution, list_window_titles, screenshot
from .solver import SudokuError, is_valid_solution, solve
from .vision import RecognitionError, offset_result, read_image, recognize


@dataclass(frozen=True)
class RunConfig:
    window_title: str | None
    image_path: str | None
    auto: bool
    delay: float
    wait_timeout: float
    wait_poll: float


class SudokuGuiApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Sudoku Quick GUI")
        self.geometry("760x520")
        self.minsize(720, 480)

        self.window_titles: list[str] = []
        self.window_var = tk.StringVar()
        self.image_path_var = tk.StringVar()
        self.delay_var = tk.StringVar(value="0.05")
        self.wait_timeout_var = tk.StringVar(value="65")
        self.wait_poll_var = tk.StringVar(value="0.5")
        self.status_var = tk.StringVar(value="Ready")
        self.busy_var = tk.BooleanVar(value=False)

        self._build_ui()
        self.refresh_windows()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(outer, text="Sudoku Quick GUI", font=("Segoe UI", 18, "bold"))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        ttk.Label(outer, text="Window").grid(row=1, column=0, sticky="w")
        self.window_combo = ttk.Combobox(
            outer,
            textvariable=self.window_var,
            state="readonly",
            width=52,
            values=self.window_titles,
        )
        self.window_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(8, 8))
        self.refresh_button = ttk.Button(outer, text="Refresh", command=self.refresh_windows)
        self.refresh_button.grid(
            row=1, column=3, sticky="ew"
        )

        ttk.Label(outer, text="Image").grid(row=2, column=0, sticky="w", pady=(10, 0))
        image_row = ttk.Frame(outer)
        image_row.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=(10, 0))
        self.image_entry = ttk.Entry(image_row, textvariable=self.image_path_var)
        self.image_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = ttk.Button(image_row, text="Browse", command=self.pick_image)
        self.browse_button.pack(side="left", padx=(8, 0))

        options = ttk.LabelFrame(outer, text="Options", padding=10)
        options.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(16, 0))
        options.columnconfigure(1, weight=1)
        options.columnconfigure(3, weight=1)

        self.delay_entry = self._add_option(options, 0, "Delay", self.delay_var)
        self.wait_timeout_entry = self._add_option(options, 1, "Wait timeout", self.wait_timeout_var)
        self.wait_poll_entry = self._add_option(options, 2, "Wait poll", self.wait_poll_var)

        buttons = ttk.Frame(outer)
        buttons.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(16, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        buttons.columnconfigure(2, weight=1)

        self.dry_button = ttk.Button(buttons, text="Dry Run", command=lambda: self.start_run(auto=False))
        self.dry_button.grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        self.auto_button = ttk.Button(buttons, text="Auto Run", command=lambda: self.start_run(auto=True))
        self.auto_button.grid(
            row=0, column=1, sticky="ew", padx=(0, 8)
        )
        self.clear_button = ttk.Button(buttons, text="Clear Log", command=self.clear_log)
        self.clear_button.grid(
            row=0, column=2, sticky="ew"
        )

        self.log = tk.Text(outer, height=14, wrap="word")
        self.log.grid(row=5, column=0, columnspan=4, sticky="nsew", pady=(16, 0))
        scroll = ttk.Scrollbar(outer, orient="vertical", command=self.log.yview)
        scroll.grid(row=5, column=4, sticky="ns", pady=(16, 0))
        self.log.configure(yscrollcommand=scroll.set)

        footer = ttk.Label(outer, textvariable=self.status_var)
        footer.grid(row=6, column=0, columnspan=4, sticky="w", pady=(10, 0))

        outer.columnconfigure(1, weight=1)
        outer.columnconfigure(2, weight=1)
        outer.rowconfigure(5, weight=1)

    def _add_option(self, parent: ttk.LabelFrame, row: int, label: str, variable: tk.StringVar) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=variable, width=12)
        entry.grid(row=row, column=1, sticky="w", padx=(8, 24))
        return entry

    def pick_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Sudoku screenshot",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")],
        )
        if path:
            self.image_path_var.set(path)
            self.window_var.set("")
            self.set_status(f"Selected image: {path}")

    def refresh_windows(self) -> None:
        try:
            titles = list_window_titles()
        except Exception as exc:
            self.set_status(str(exc))
            return

        self.window_titles = titles
        self.window_combo["values"] = titles
        if titles and self.window_var.get() not in titles:
            self.window_var.set(titles[0])
        self.set_status(f"Found {len(titles)} windows.")

    def clear_log(self) -> None:
        self.log.delete("1.0", "end")

    def set_status(self, text: str) -> None:
        self.status_var.set(text)
        self._append_log(text)

    def _append_log(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def start_run(self, auto: bool) -> None:
        if self.busy_var.get():
            return
        try:
            config = self._read_config(auto)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.busy_var.set(True)
        self.set_widgets_state("disabled")
        self.set_status("Running...")

        thread = threading.Thread(target=self._run_worker, args=(config,), daemon=True)
        thread.start()

    def _read_config(self, auto: bool) -> RunConfig:
        delay = float(self.delay_var.get())
        wait_timeout = float(self.wait_timeout_var.get())
        wait_poll = float(self.wait_poll_var.get())
        if delay < 0 or wait_timeout < 0 or wait_poll <= 0:
            raise ValueError("Delay must be >= 0, timeout must be >= 0, and poll must be > 0.")

        image_path = self.image_path_var.get().strip() or None
        window_title = self.window_var.get().strip() or None
        if image_path and window_title:
            raise ValueError("Choose either a window or an image, not both.")
        if auto and image_path:
            raise ValueError("Auto run is only supported for live window capture.")
        if not image_path and not window_title:
            raise ValueError("Select a window or an image first.")

        return RunConfig(
            window_title=window_title,
            image_path=image_path,
            auto=auto,
            delay=delay,
            wait_timeout=wait_timeout,
            wait_poll=wait_poll,
        )

    def _run_worker(self, config: RunConfig) -> None:
        try:
            if config.image_path:
                image = read_image(config.image_path)
                offset = (0, 0)
            else:
                image, offset = screenshot(config.window_title)

            result = recognize(image)
            result = offset_result(result, offset)
            solution = solve(result.grid)

            if not is_valid_solution(solution):
                raise SudokuError("Solver returned an invalid solution.")

            self._post_log("recognized grid and solved puzzle")
            self._post_log(self._format_grid(result.grid))
            self._post_log("solution")
            self._post_log(self._format_grid(solution))

            if config.auto:
                fill_solution(
                    result,
                    solution,
                    config.delay,
                    window_title=config.window_title,
                    wait_timeout=config.wait_timeout,
                    wait_poll=config.wait_poll,
                )
                self._post_status("Auto run complete.")
            else:
                self._post_status("Dry run complete.")
        except Exception as exc:
            self._post_status(f"error: {exc}")
        finally:
            self._post_busy(False)

    def _post_log(self, message: str) -> None:
        self.after(0, lambda: self._append_log(message))

    def _post_status(self, message: str) -> None:
        self.after(0, lambda: self.status_var.set(message))
        self.after(0, lambda: self._append_log(message))

    def _post_busy(self, busy: bool) -> None:
        def update() -> None:
            self.busy_var.set(busy)
            self.set_widgets_state(busy)

        self.after(0, update)

    def set_widgets_state(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.window_combo.configure(state="disabled" if busy else "readonly")
        self.image_entry.configure(state=state)
        self.delay_entry.configure(state=state)
        self.wait_timeout_entry.configure(state=state)
        self.wait_poll_entry.configure(state=state)
        self.refresh_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.dry_button.configure(state=state)
        self.auto_button.configure(state=state)
        self.clear_button.configure(state=state)

    @staticmethod
    def _format_grid(grid: list[list[int]]) -> str:
        return "\n".join(" ".join(str(value) if value else "." for value in row) for row in grid)


def main() -> int:
    app = SudokuGuiApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
