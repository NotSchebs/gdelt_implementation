import tkinter as tk

from .gui import GdeltApp


def run_app() -> None:
    root = tk.Tk()
    GdeltApp(root)
    root.mainloop()
