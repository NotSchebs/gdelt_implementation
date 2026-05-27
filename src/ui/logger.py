"""Logger for UI log panel."""

from datetime import datetime
import tkinter as tk


class Logger:
    """Handles all logging to the UI log panel."""
    
    def __init__(self, log_text: tk.Text):
        self.log_text = log_text
    
    def log(self, message: str) -> None:
        """Add timestamped message to log panel."""
        self.log_text.config(state=tk.NORMAL)
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{time_str}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
