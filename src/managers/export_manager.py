"""Exporting timeline and article data to files."""

import os
import zipfile
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox

import pandas as pd

from ..ui.logger import Logger


class ExportManager:
    """Handles exporting timeline and article data."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def export_data(self, timeline_df: pd.DataFrame, articles_df: Optional[pd.DataFrame], 
                    keyword: str, root: tk.Tk) -> None:
        """Export timeline and/or article data to file."""
        if timeline_df is None or timeline_df.empty:
            messagebox.showwarning("Export Error", "No data to export.")
            return

        keyword_clean = keyword.replace(" ", "_")
        
        if articles_df is not None and not articles_df.empty:
            self._export_zip(timeline_df, articles_df, keyword_clean, root)
        else:
            self._export_csv(timeline_df, keyword_clean, root)
    
    def _export_csv(self, df: pd.DataFrame, keyword: str, root: tk.Tk) -> None:
        """Export timeline data to CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"gdelt_trend_{keyword}.csv",
            title="Save Timeline CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        
        if not filepath:
            return

        try:
            if not filepath.lower().endswith(".csv"):
                filepath += ".csv"
            df.to_csv(filepath, index=False)
            self.logger.log(f"Timeline data exported to: {filepath}")
            messagebox.showinfo("Export Success", 
                              "Timeline data exported successfully! It is now ready for Power BI.")
        except Exception as error:
            messagebox.showerror("Export Error", f"Failed to save file:\n{str(error)}")
    
    def _export_zip(self, timeline_df: pd.DataFrame, articles_df: pd.DataFrame, 
                    keyword: str, root: tk.Tk) -> None:
        """Export timeline and articles to ZIP."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".zip",
            initialfile=f"gdelt_trend_{keyword}.zip",
            title="Save Timeline and Articles ZIP",
            filetypes=[("ZIP Archive", "*.zip"), ("All Files", "*.*")],
        )
        
        if not filepath:
            return

        try:
            if not filepath.lower().endswith(".zip"):
                filepath += ".zip"
            with zipfile.ZipFile(filepath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                timeline_name = os.path.basename(filepath).replace(".zip", "_timeline.csv")
                articles_name = os.path.basename(filepath).replace(".zip", "_articles.csv")
                zf.writestr(timeline_name, timeline_df.to_csv(index=False))
                zf.writestr(articles_name, articles_df.to_csv(index=False))
            self.logger.log(f"Timeline and article data exported to: {filepath}")
            messagebox.showinfo("Export Success", 
                              f"Timeline and article data exported successfully in ZIP:\n{filepath}")
        except Exception as error:
            messagebox.showerror("Export Error", f"Failed to save file:\n{str(error)}")
