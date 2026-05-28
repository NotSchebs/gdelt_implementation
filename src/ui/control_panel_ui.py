"""Control panel UI building and management."""

from typing import Callable

import tkinter as tk
from tkinter import ttk

from ..core.constants import TIMELINE_MODES
from .tooltip import ToolTip


class ControlPanelUI:
    """Builds and manages the control panel UI."""
    
    def __init__(self, root: tk.Tk, on_search: Callable, on_stop: Callable, 
                 on_export: Callable, on_filters: Callable, on_analyse: Callable,
                 on_time_span_change: Callable):
        self.root = root
        self.on_search = on_search
        self.on_stop = on_stop
        self.on_export = on_export
        self.on_filters = on_filters
        self.on_analyse = on_analyse 
        self.on_time_span_change = on_time_span_change
        
        # UI elements
        self.keyword_entry = None
        self.fetch_articles_var = None
        self.timeline_mode_var = None
        self.time_span_var = None
        self.start_date_entry = None
        self.end_date_entry = None
        self.search_btn = None
        self.stop_btn = None
        self.export_btn = None
        
        self._build()
    
    def _build(self) -> None:
        """Build control panel UI."""
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Keyword input
        tk.Label(control_frame, text="Keyword:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        self.keyword_entry = tk.Entry(control_frame, width=25)
        self.keyword_entry.grid(row=0, column=0, sticky="e", padx=(0, 10), pady=5)
        self.keyword_entry.insert(0, "quantum computing")

        # Articles checkbox
        tk.Label(control_frame, text="Include Articles:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.fetch_articles_var = tk.BooleanVar(value=False)
        self.fetch_articles_check = tk.Checkbutton(control_frame, text="Fetch Articles", 
                                                   variable=self.fetch_articles_var)
        self.fetch_articles_check.grid(row=1, column=0, sticky="e", padx=10, pady=5)

        # Timeline mode
        timeline_label = tk.Label(control_frame, text="Timeline Mode:")
        timeline_label.grid(row=2, column=0, sticky="w", padx=(0, 5), pady=5)

        help_label = tk.Label(
            control_frame,
            text="ⓘ",
            fg="white",
            cursor="hand2"
        )

        help_label.grid(row=2, column=0, sticky="w", padx=(110, 0))

        ToolTip(
            help_label,
            "timelinevol:\nNormalized volume of mentions over time\n\n"

            "timelinevolraw:\nRaw article mention counts over time\n\n"

            "timelinelang:\nBreakdown of coverage by language\n\n"

            "timelinesourcecountry:\nCoverage grouped by source country\n\n"

            "timelinetone:\nSentiment and emotional tone over time"
        )


        self.timeline_mode_var = tk.StringVar(value="timelinevol")
        self.timeline_mode_menu = ttk.Combobox(control_frame, textvariable=self.timeline_mode_var, 
                                              values=TIMELINE_MODES, state="readonly", width=15)
        self.timeline_mode_menu.grid(row=2, column=0, sticky="e", padx=(0, 10), pady=5)

        # Time span
        tk.Label(control_frame, text="Time Span:").grid(row=3, column=0, sticky="w", padx=(0, 5), pady=5)
        self.time_span_var = tk.StringVar(value="Last Month")
        time_spans = ["Last Week", "Last Month", "2020 - Yesterday", "Custom"]
        self.time_span_menu = ttk.Combobox(control_frame, textvariable=self.time_span_var, 
                                          values=time_spans, state="readonly", width=15)
        self.time_span_menu.grid(row=3, column=0, sticky="e", padx=(0, 10), pady=5)
        self.time_span_menu.bind("<<ComboboxSelected>>", lambda e: self.on_time_span_change())

        # Date entries
        self.date_frame = tk.Frame(control_frame)
        self.date_frame.grid(row=4, column=0)
        tk.Label(self.date_frame, text="Start (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.start_date_entry = tk.Entry(self.date_frame, width=12)
        self.start_date_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(self.date_frame, text="End (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.end_date_entry = tk.Entry(self.date_frame, width=12)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)

        # Filters button
        tk.Button(control_frame, text="Filters", command=self.on_filters, width=20).grid(
            row=2, column=1, sticky="ew", padx=(0, 5), pady=5
        )

        # Analyse button
        tk.Button(control_frame, text="Analyse", command=self.on_analyse, width=20).grid(
            row=3, column=1, sticky="ew", padx=(0, 5), pady=5
        )

        # Search/Stop/Export buttons
        btn_frame = tk.Frame(control_frame)
        btn_frame.grid(row=0, column=1, rowspan=1, padx=10)
        self.search_btn = tk.Button(btn_frame, text="Search", command=self.on_search, 
                                   width=10, bg="green")
        self.search_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(btn_frame, text="Stop", command=self.on_stop, 
                                 width=10, state=tk.DISABLED, bg="red")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.export_btn = tk.Button(btn_frame, text="Export CSV", command=self.on_export, 
                                   width=10, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)
