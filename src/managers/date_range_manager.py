"""Date range selection and validation."""

from datetime import datetime, timedelta
from typing import Tuple
import tkinter as tk


class DateRangeManager:
    """Handles date range selection and validation."""
    
    def __init__(self, time_span_var: tk.StringVar, start_date_entry: tk.Entry, 
                 end_date_entry: tk.Entry):
        self.time_span_var = time_span_var
        self.start_date_entry = start_date_entry
        self.end_date_entry = end_date_entry
    
    def update_entry_state(self) -> None:
        """Enable/disable custom date entries based on selection."""
        state = tk.NORMAL if self.time_span_var.get() == "Custom" else tk.DISABLED
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def get_date_range(self) -> Tuple[str, str]:
        """Return start and end dates based on selected time span."""
        span = self.time_span_var.get()
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        if span == "Last Week":
            return (yesterday - timedelta(days=7)).strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
        elif span == "Last Month":
            return (yesterday - timedelta(days=30)).strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
        elif span == "2020 - Yesterday":
            return "2020-01-01", yesterday.strftime("%Y-%m-%d")
        else:  # Custom
            return self.start_date_entry.get(), self.end_date_entry.get()
    
    def validate_dates(self, start_date: str, end_date: str) -> Tuple[bool, str]:
        """Validate date format and ordering."""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD."

        if start_dt > end_dt:
            return False, "Start date must be before or equal to end date."
        
        return True, ""
