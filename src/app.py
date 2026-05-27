"""Application entry point."""

import tkinter as tk

from .gui import GdeltApp


def run_app() -> None:
    """Launch the GDELT application."""
    root = tk.Tk()
    GdeltApp(root)
    root.mainloop()
