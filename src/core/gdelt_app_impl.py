"""Main GDELT application orchestrator."""

from datetime import datetime, timedelta

import tkinter as tk
from tkinter import messagebox

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.core.analysis import AnalysisWindow

from .gdelt_api import GdeltApiClient
from .plotter import TimelinePlotter
from .filters import FiltersWindow
from ..ui.logger import Logger
from ..managers.date_range_manager import DateRangeManager
from ..managers.data_manager import DataManager
from ..managers.export_manager import ExportManager
from ..ui.dialog_manager import DialogManager
from ..managers.search_manager import SearchManager
from ..ui.control_panel_ui import ControlPanelUI


class GdeltApp:
    """Main application orchestrator."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GDELT Trend Analysis Tool")
        self.root.geometry("1000x700")

        # Initialize managers
        self.logger = self._setup_logger()
        self.api_client = GdeltApiClient()
        self.data_manager = DataManager(self.api_client, self.logger)
        self.dialog_manager = DialogManager(self.root, self.logger)
        self.export_manager = ExportManager(self.logger)
        self.search_manager = SearchManager(self.api_client, self.data_manager, 
                                           self.logger, self.dialog_manager)
        
        # Build UI
        self.control_panel = ControlPanelUI(
            self.root, 
            on_search=self.start_search,
            on_stop=self.stop_search,
            on_export=self.export_csv,
            on_filters=self._filters_window,
            on_analyse=self._analysis_window,  # Placeholder for future analysis feature
            on_time_span_change=self._on_time_span_change
        )
        
        self.date_range_manager = DateRangeManager(
            self.control_panel.time_span_var,
            self.control_panel.start_date_entry,
            self.control_panel.end_date_entry
        )
        self.date_range_manager.update_entry_state()
        
        self._setup_plot_area()

    def _setup_logger(self) -> Logger:
        """Setup logger with log text widget."""
        log_frame = tk.Frame(self.root)
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        tk.Label(log_frame, text="Status Log:").pack(side=tk.TOP, anchor=tk.W)
        log_text = tk.Text(log_frame, height=6, state=tk.DISABLED)
        log_text.pack(side=tk.TOP, fill=tk.X)
        return Logger(log_text)

    def _setup_plot_area(self) -> None:
        """Setup matplotlib plot area."""
        plot_frame = tk.Frame(self.root, bg="white", bd=2, relief=tk.SUNKEN)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.plotter = TimelinePlotter(self.fig, self.ax)

    def _on_time_span_change(self) -> None:
        """Handle time span change."""
        self.date_range_manager.update_entry_state()

    def _filters_window(self) -> None:
        """Open filters window."""
        FiltersWindow(self.root)

    def _analysis_window(self) -> None:
        """Open analysis window."""
        AnalysisWindow(self.root)

    def start_search(self) -> None:
        """Validate input and start search."""
        keyword = self.control_panel.keyword_entry.get().strip()
        if not keyword:
            messagebox.showerror("Input Error", "Please enter a keyword.")
            return

        start_date, end_date = self.date_range_manager.get_date_range()
        
        # Validate dates
        is_valid, error_msg = self.date_range_manager.validate_dates(start_date, end_date)
        if not is_valid:
            messagebox.showerror("Input Error", error_msg)
            return

        # Check article range
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return

        if self.control_panel.fetch_articles_var.get() and (end_dt - start_dt).days > 14:
            if not self.dialog_manager.show_article_range_warning((end_dt - start_dt).days):
                return

        # Update UI
        self.logger.log(f"Starting search for '{keyword}' from {start_date} to {end_date}...")
        self.control_panel.search_btn.config(state=tk.DISABLED)
        self.control_panel.stop_btn.config(state=tk.NORMAL)
        self.control_panel.export_btn.config(state=tk.DISABLED)
        self.data_manager.timeline_df = None
        self.data_manager.articles_df = None
        self.ax.clear()
        self.canvas.draw()

        # Start search
        timeline_mode = self.control_panel.timeline_mode_var.get() or "timelinevol"
        self.search_manager.start_fetch(
            keyword, start_date, end_date, timeline_mode,
            self.control_panel.fetch_articles_var.get(),
            self._on_search_finished
        )

    def stop_search(self) -> None:
        """Stop ongoing search."""
        self.logger.log("Stopping search requested...")
        self.search_manager.stop_event.set()
        self.search_manager.is_fetching = False
        self.control_panel.search_btn.config(state=tk.NORMAL)
        self.control_panel.stop_btn.config(state=tk.DISABLED)
        export_state = tk.DISABLED if self.data_manager.timeline_df is None else tk.NORMAL
        self.control_panel.export_btn.config(state=export_state)

    def _on_search_finished(self, success: bool, msg: str) -> None:
        """Handle search completion."""
        self.search_manager.is_fetching = False

        def update_gui() -> None:
            self.logger.log(msg)
            self.control_panel.search_btn.config(state=tk.NORMAL)
            self.control_panel.stop_btn.config(state=tk.DISABLED)
            if success and self.data_manager.timeline_df is not None:
                self.control_panel.export_btn.config(state=tk.NORMAL)
                self.plotter.plot(self.data_manager.timeline_df, 
                                self.control_panel.timeline_mode_var.get())

        self.root.after(0, update_gui)

    def export_csv(self) -> None:
        """Export data to file."""
        keyword = self.control_panel.keyword_entry.get().strip()
        self.export_manager.export_data(
            self.data_manager.timeline_df,
            self.data_manager.articles_df,
            keyword,
            self.root
        )

