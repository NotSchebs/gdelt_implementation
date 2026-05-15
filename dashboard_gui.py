import tkinter as tk
from tkinter import messagebox
import os

try:
    # import run_app to allow returning to the main GDELT GUI
    from src.app import run_app
except Exception:
    run_app = None


def _back_to_search(root: tk.Tk) -> None:
    try:
        root.destroy()
    except Exception:
        pass

    if run_app:
        try:
            run_app()
        except Exception:
            # If returning fails, just exit silently — user can re-run main GUI.
            pass


def launch_dashboard(timeline_csv_path: str, articles_csv_path: str = None, keyword: str = "") -> None:
    """
    Minimal dashboard placeholder. Kept intentionally simple so the full
    analysis UI can be rebuilt later. Provides a single 'Back to Search'
    button that returns to the main GDELT GUI when available.
    """
    try:
        root = tk.Tk()
        root.title(f"GDELT Dashboard - {keyword}")
        root.geometry("1000x700")

        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Analysis dashboard (placeholder)", font=(None, 16)).pack(pady=10)

        # Show loaded data paths for convenience
        if timeline_csv_path:
            tk.Label(frame, text=f"Timeline: {os.path.basename(timeline_csv_path)}").pack()
        if articles_csv_path:
            tk.Label(frame, text=f"Articles: {os.path.basename(articles_csv_path)}").pack()

        tk.Button(frame, text="Back to Search", command=lambda: _back_to_search(root), width=16, bg="lightgray").pack(pady=20)

        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open dashboard: {str(e)}")


if __name__ == "__main__":
    launch_dashboard(None, None, "test")
