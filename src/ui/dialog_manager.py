"""Dialog windows and popups."""

import threading
import time
from typing import Callable, Optional, Tuple

import tkinter as tk

from .logger import Logger


class DialogManager:
    """Handles all dialog windows and popups."""
    
    def __init__(self, root: tk.Tk, logger: Logger):
        self.root = root
        self.logger = logger
    
    def show_article_range_warning(self, days: int) -> bool:
        """Confirm with user if article fetch range is too large."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Long Article Date Range")
        dialog.geometry("360x150")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = tk.Frame(dialog, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text=(
            f"Selected date range is {days} days, which is longer than two weeks.\n"
            "Article results are limited to 250 records."
        ), justify=tk.LEFT, wraplength=330).pack(pady=(0, 10))

        result = {"continue": False}

        def search_anyway() -> None:
            result["continue"] = True
            dialog.destroy()

        def stop() -> None:
            dialog.destroy()

        btn_frame = tk.Frame(frame)
        btn_frame.pack()
        tk.Button(btn_frame, text="Search Anyway", command=search_anyway, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Stop", command=stop, width=8).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result["continue"]
    
    def show_error_dialog(self, message: str, callback: Callable, args: Tuple, 
                         cancel_success: bool, cancel_msg: Optional[str]) -> None:
        """Show error dialog with retry options."""
        dialog = tk.Toplevel(self.root)
        dialog.title("API Error")
        dialog.geometry("380x170")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text=message, pady=10, wraplength=360, justify=tk.LEFT).pack()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        def retry_now() -> None:
            dialog.destroy()
            self.logger.log("Retrying immediately...")
            threading.Thread(target=callback, args=args or (), daemon=True).start()

        def wait_and_retry(minutes: int) -> None:
            dialog.destroy()
            self.logger.log(f"Waiting for {minutes} minutes before retrying...")
            threading.Thread(target=self._wait_timer, args=(minutes, callback, args), daemon=True).start()

        def cancel() -> None:
            dialog.destroy()
            if cancel_success:
                msg = cancel_msg or "Timeline fetched; article retrieval cancelled."
            else:
                msg = cancel_msg or "Search cancelled due to an error."
            callback(-1, msg)  # Signal completion

        tk.Button(btn_frame, text="Retry Now", command=retry_now).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 1 Min", command=lambda: wait_and_retry(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 5 Min", command=lambda: wait_and_retry(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
    
    def _wait_timer(self, minutes: int, callback: Callable, args: Tuple, 
                    stop_event: threading.Event) -> None:
        """Wait for specified minutes, showing countdown."""
        seconds = minutes * 60
        for i in range(seconds):
            if stop_event.is_set():
                return
            if i % 60 == 0:
                mins_left = (seconds - i) // 60
                self.logger.log(f"Waiting... {mins_left} minutes left.")
            time.sleep(1)

        self.logger.log("Wait complete. Retrying...")
        callback(*args)
