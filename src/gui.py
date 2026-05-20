from logging import root
import os
import threading
import time
import zipfile
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from typing import Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .constants import TIMELINE_MODES
from .gdelt_api import GdeltApiClient
from .plotter import TimelinePlotter
from .filters import FiltersWindow


class GdeltApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GDELT Trend Analysis Tool")
        self.root.geometry("1000x700")

        self.df = None
        self.articles_df = None
        self.timeline_mode = "timelinevol"
        self.stop_event = threading.Event()
        self.is_fetching = False
        self.api_client = GdeltApiClient()

        self._create_ui()

    def _create_ui(self) -> None:
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(control_frame, text="Keyword:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        self.keyword_entry = tk.Entry(control_frame, width=25)
        self.keyword_entry.grid(row=0, column=0, sticky="e", padx=(0, 10), pady=5)
        self.keyword_entry.insert(0, "quantum computing")

        tk.Label(control_frame, text="Include Articles:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.fetch_articles_var = tk.BooleanVar(value=False)
        self.fetch_articles_check = tk.Checkbutton(control_frame, text="Fetch Articles", variable=self.fetch_articles_var)
        self.fetch_articles_check.grid(row=1, column=0, sticky="e", padx=10, pady=5)

        tk.Label(control_frame, text="Timeline Mode:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=5)
        self.timeline_mode_var = tk.StringVar(value="timelinevol")
        self.timeline_mode_menu = ttk.Combobox(control_frame, textvariable=self.timeline_mode_var, values=TIMELINE_MODES, state="readonly", width=15)
        self.timeline_mode_menu.grid(row=2, column=0, sticky="e", padx=(0, 10), pady=5)

        tk.Label(control_frame, text="Time Span:").grid(row=3, column=0, sticky="w", padx=(0, 5), pady=5)
        self.time_span_var = tk.StringVar(value="Last Month")
        time_spans = ["Last Week", "Last Month", "2020 - Yesterday", "Custom"]
        self.time_span_menu = ttk.Combobox(control_frame, textvariable=self.time_span_var, values=time_spans, state="readonly", width=15)
        self.time_span_menu.grid(row=3, column=0, sticky="e", padx=(0, 10), pady=5)
        self.time_span_menu.bind("<<ComboboxSelected>>", self._on_time_span_change)

        self.date_frame = tk.Frame(control_frame)
        self.date_frame.grid(row=4, column=0)
        tk.Label(self.date_frame, text="Start (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.start_date_entry = tk.Entry(self.date_frame, width=12)
        self.start_date_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(self.date_frame, text="End (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.end_date_entry = tk.Entry(self.date_frame, width=12)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)
        self._update_date_entries_state()

    
        tk.Button(control_frame, text="Filters", command=self._filters_window, width=20).grid(
            row=2, column=1, sticky="ew", padx=(0, 5), pady=5
            )

        btn_frame = tk.Frame(control_frame)
        btn_frame.grid(row=0, column=1, rowspan=1, padx=10)
        self.search_btn = tk.Button(btn_frame, text="Search", command=self.start_search, width=10, bg="green")
        self.search_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(btn_frame, text="Stop", command=self.stop_search, width=10, state=tk.DISABLED, bg="red")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.export_btn = tk.Button(btn_frame, text="Export CSV", command=self.export_csv, width=10, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)

        self.plot_frame = tk.Frame(self.root, bg="white", bd=2, relief=tk.SUNKEN)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.plotter = TimelinePlotter(self.fig, self.ax)

        log_frame = tk.Frame(self.root)
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        tk.Label(log_frame, text="Status Log:").pack(side=tk.TOP, anchor=tk.W)
        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED)
        self.log_text.pack(side=tk.TOP, fill=tk.X)

    def _on_time_span_change(self, event=None) -> None:
        self._update_date_entries_state()

    def _update_date_entries_state(self) -> None:
        state = tk.NORMAL if self.time_span_var.get() == "Custom" else tk.DISABLED
        self.start_date_entry.config(state=state)
        self.end_date_entry.config(state=state)
    
    def _filters_window(self) -> None:
        FiltersWindow(self.root)


    def _confirm_article_range_warning(self, days: int) -> bool:
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

    def log(self, message: str) -> None:
        self.log_text.config(state=tk.NORMAL)
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{time_str}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _get_date_range(self) -> Tuple[str, str]:
        span = self.time_span_var.get()
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        if span == "Last Week":
            return (yesterday - timedelta(days=7)).strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
        if span == "Last Month":
            return (yesterday - timedelta(days=30)).strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
        if span == "2020 - Yesterday":
            return "2020-01-01", yesterday.strftime("%Y-%m-%d")
        return self.start_date_entry.get(), self.end_date_entry.get()

    def start_search(self) -> None:
        keyword = self.keyword_entry.get().strip()
        start_date, end_date = self._get_date_range()

        if not keyword:
            messagebox.showerror("Input Error", "Please enter a keyword.")
            return

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        if start_dt > end_dt:
            messagebox.showerror("Input Error", "Start date must be before or equal to end date.")
            return

        if self.fetch_articles_var.get() and (end_dt - start_dt).days > 14:
            if not self._confirm_article_range_warning((end_dt - start_dt).days):
                return

        self.log(f"Starting search for '{keyword}' from {start_date} to {end_date}...")
        self.search_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        self.stop_event.clear()
        self.is_fetching = True
        self.timeline_mode = self.timeline_mode_var.get() or "timelinevol"
        self.df = None
        self.articles_df = None
        self.ax.clear()
        self.canvas.draw()

        threading.Thread(target=self._fetch_data, args=(keyword, start_date, end_date), daemon=True).start()

    def stop_search(self) -> None:
        self.log("Stopping search requested...")
        self.stop_event.set()
        self.is_fetching = False
        self.search_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED if self.df is None else tk.NORMAL)

    def _fetch_data(self, keyword: str, start_date: str, end_date: str) -> None:
        try:
            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Search stopped by user.")
                return

            self._sleep_before_request(15, "timeline")
            self.log(f"Calling GDELT API for {self.timeline_mode} data (this may take a while)...")
            timeline_data = self.api_client.fetch_timeline(keyword, start_date, end_date, self.timeline_mode)

            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Search stopped by user.")
                return

            self.df = self._prepare_timeline_df(timeline_data)

            if self.fetch_articles_var.get():
                self._fetch_articles_after_timeline(keyword, start_date, end_date)
            else:
                self._on_search_finished(success=True, msg="Timeline successfully fetched and processed.")

        except Exception as error:
            self.root.after(
                0,
                self._show_retry_dialog,
                f"An error occurred while fetching timeline data: {str(error)}",
                self._fetch_data,
                (keyword, start_date, end_date),
                False,
                None,
            )

    def _prepare_timeline_df(self, timeline_data: pd.DataFrame) -> pd.DataFrame:
        df = pd.DataFrame(timeline_data)
        if df.empty:
            raise ValueError("No timeline data found for this query.")

        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df["date"] = df["datetime"].dt.date
        elif "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        else:
            raise ValueError("Timeline response did not include a datetime or date column.")

        if self.timeline_mode in ("timelinevol", "timelinevolraw", "timelinetone"):
            metric_col = self._find_metric_column(df)
            daily = df.groupby("date")[metric_col].mean().reset_index()
            daily.columns = ["date", "tone" if self.timeline_mode == "timelinetone" else "volume"]
            return daily

        numeric_cols = [
            column for column in df.columns
            if column not in ("datetime", "date") and pd.api.types.is_numeric_dtype(df[column])
        ]
        if not numeric_cols:
            raise ValueError("No numeric timeline columns found for the selected breakdown mode.")

        grouped = df.groupby("date")[numeric_cols].sum().reset_index()
        return grouped.sort_values("date")

    def _find_metric_column(self, df: pd.DataFrame) -> str:
        search_columns = [
            "Average Tone", "Tone", "average_tone", "tone",
            "Volume Intensity", "volume", "Volume", "Total Articles", "Total", "total", "total_articles",
        ]
        for column in search_columns:
            if column in df.columns:
                return column

        numeric_columns = [
            column for column in df.columns
            if column not in ("datetime", "date") and pd.api.types.is_numeric_dtype(df[column])
        ]
        if numeric_columns:
            fallback = numeric_columns[0]
            self.log(f"Warning: using fallback numeric column '{fallback}' for {self.timeline_mode}.")
            return fallback

        raise ValueError("Unable to locate the timeline metric column for the selected mode.")

    def _fetch_articles_after_timeline(self, keyword: str, start_date: str, end_date: str) -> None:
        if self.stop_event.is_set():
            self._on_search_finished(success=False, msg="Search stopped by user.")
            return

        try:
            self._sleep_before_request(20, "article list")
            self.log("Calling GDELT API for article list (this may take a while)...")
            articles = self.api_client.fetch_articles(keyword, start_date, end_date)

            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Search stopped by user.")
                return

            if articles is None or articles.empty:
                self.articles_df = pd.DataFrame()
                self._on_search_finished(success=True, msg="Timeline fetched successfully, but no articles were returned.")
                return

            self.articles_df = articles.copy()
            self._enrich_article_data()
            self._on_search_finished(success=True, msg="Timeline and article list fetched successfully.")

        except Exception as error:
            self.root.after(
                0,
                self._show_retry_dialog,
                f"An error occurred while fetching articles: {str(error)}",
                self._fetch_articles_after_timeline,
                (keyword, start_date, end_date),
                True,
                "Timeline fetched; article retrieval cancelled due to an error.",
            )

    def _enrich_article_data(self) -> None:
        date_column = None
        parse_format = None
        for column_name in ("seendate", "publish_date", "date"):
            if column_name in self.articles_df.columns:
                date_column = column_name
                break

        if date_column == "seendate":
            parse_format = "%Y%m%dT%H%M%SZ"

        if date_column is None:
            self.log("No publish/date column found in fetched articles.")
            return

        self.articles_df["article_datetime"] = pd.to_datetime(
            self.articles_df[date_column], format=parse_format, errors="coerce"
        )
        self.articles_df["article_date"] = self.articles_df["article_datetime"].dt.date

        if self.articles_df["article_datetime"].notna().any():
            dates = self.articles_df["article_datetime"].dropna()
            self.log(f"Article date range: {dates.min().date()} to {dates.max().date()} using '{date_column}' column")
        else:
            self.log(f"Unable to parse article dates from '{date_column}' values.")

        if self.articles_df["article_date"].notna().any():
            article_counts = (
                self.articles_df.groupby("article_date").size().rename("n_articles").reset_index()
            )
            self.df = self.df.merge(article_counts, left_on="date", right_on="article_date", how="left")
            self.df["n_articles"] = self.df["n_articles"].fillna(0).astype(int)
            self.df.drop(columns=["article_date"], inplace=True)
            self.log("Added n_articles counts to timeline data.")

    def _wait_timer(self, minutes: int, callback, args: tuple) -> None:
        seconds = minutes * 60
        for i in range(seconds):
            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Wait cancelled by user.")
                return
            if i % 60 == 0:
                mins_left = (seconds - i) // 60
                self.log(f"Waiting... {mins_left} minutes left.")
            time.sleep(1)

        self.log("Wait complete. Retrying...")
        callback(*args)

    def _show_rate_limit_dialog(self, keyword: str, start_date: str, end_date: str, callback, args: tuple, cancel_success: bool, cancel_msg: str | None) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("API Limit Reached")
        dialog.geometry("380x170")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="GDELT API rate limit reached.\nHow would you like to proceed?", pady=10).pack()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        def retry_now() -> None:
            dialog.destroy()
            self.log("Retrying immediately...")
            threading.Thread(target=callback, args=args, daemon=True).start()

        def wait_and_retry(minutes: int) -> None:
            dialog.destroy()
            self.log(f"Waiting for {minutes} minutes before retrying...")
            threading.Thread(target=self._wait_timer, args=(minutes, callback, args), daemon=True).start()

        def cancel() -> None:
            dialog.destroy()
            if cancel_success:
                self._on_search_finished(success=True, msg=cancel_msg or "Timeline fetched; article retrieval cancelled.")
            else:
                self._on_search_finished(success=False, msg=cancel_msg or "Search cancelled due to rate limit.")

        tk.Button(btn_frame, text="Retry Now", command=retry_now).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 1 Min", command=lambda: wait_and_retry(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 5 Min", command=lambda: wait_and_retry(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Stop", command=cancel).pack(side=tk.LEFT, padx=5)

    def _show_retry_dialog(self, message: str, callback, args: Optional[Tuple] = None, cancel_success: bool = False, cancel_msg: Optional[str] = None) -> None:
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
            self.log("Retrying immediately...")
            threading.Thread(target=callback, args=args or (), daemon=True).start()

        def wait_and_retry(minutes: int) -> None:
            dialog.destroy()
            self.log(f"Waiting for {minutes} minutes before retrying...")
            threading.Thread(target=self._wait_timer, args=(minutes, callback, args or ()), daemon=True).start()

        def cancel() -> None:
            dialog.destroy()
            if cancel_success:
                self._on_search_finished(success=True, msg=cancel_msg or "Timeline fetched; article retrieval cancelled.")
            else:
                self._on_search_finished(success=False, msg=cancel_msg or "Search cancelled due to an error.")

        tk.Button(btn_frame, text="Retry Now", command=retry_now).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 1 Min", command=lambda: wait_and_retry(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 5 Min", command=lambda: wait_and_retry(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)

    def _on_search_finished(self, success: bool, msg: str) -> None:
        self.is_fetching = False

        def update_gui() -> None:
            self.log(msg)
            self.search_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            if success and self.df is not None:
                self.export_btn.config(state=tk.NORMAL)
                self.plotter.plot(self.df, self.timeline_mode)

        self.root.after(0, update_gui)

    def export_csv(self) -> None:
        if self.df is None or self.df.empty:
            messagebox.showwarning("Export Error", "No data to export.")
            return

        keyword = self.keyword_entry.get().strip().replace(" ", "_")
        if self.articles_df is not None and not self.articles_df.empty:
            default_filename = f"gdelt_trend_{keyword}.zip"
            def_ext = ".zip"
            filetypes = [("ZIP Archive", "*.zip"), ("All Files", "*.*")]
            title = "Save Timeline and Articles ZIP"
        else:
            default_filename = f"gdelt_trend_{keyword}.csv"
            def_ext = ".csv"
            filetypes = [("CSV Files", "*.csv"), ("All Files", "*.*")]
            title = "Save Timeline CSV"

        filepath = filedialog.asksaveasfilename(
            defaultextension=def_ext,
            initialfile=default_filename,
            title=title,
            filetypes=filetypes,
        )

        if not filepath:
            return

        try:
            if self.articles_df is not None and not self.articles_df.empty:
                if not filepath.lower().endswith(".zip"):
                    filepath += ".zip"
                with zipfile.ZipFile(filepath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    timeline_name = os.path.basename(filepath).replace(".zip", "_timeline.csv")
                    articles_name = os.path.basename(filepath).replace(".zip", "_articles.csv")
                    zf.writestr(timeline_name, self.df.to_csv(index=False))
                    zf.writestr(articles_name, self.articles_df.to_csv(index=False))
                self.log(f"Timeline and article data exported successfully to: {filepath}")
                messagebox.showinfo("Export Success", f"Timeline and article data exported successfully in ZIP:\n{filepath}")
            else:
                if not filepath.lower().endswith(".csv"):
                    filepath += ".csv"
                self.df.to_csv(filepath, index=False)
                self.log(f"Timeline data exported successfully to: {filepath}")
                messagebox.showinfo("Export Success", "Timeline data exported successfully! It is now ready for Power BI.")
        except Exception as error:
            messagebox.showerror("Export Error", f"Failed to save file:\n{str(error)}")

    def open_dashboard(self) -> None:
        messagebox.showinfo("Analysis Disabled", "Analysis features are temporarily disabled.")

    def _sleep_before_request(self, seconds: int, request_type: str) -> None:
        self.log(f"Sleeping {seconds} seconds before sending the {request_type} request...")
        for _ in range(seconds):
            if self.stop_event.is_set():
                self.log("Request cancelled before sending.")
                return
            time.sleep(1)
