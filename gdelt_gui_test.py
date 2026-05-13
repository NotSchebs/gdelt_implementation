import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import zipfile
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gdeltdoc import GdeltDoc, Filters
from gdeltdoc.errors import RateLimitError
from datetime import datetime, timedelta
import threading
import time

class GdeltApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GDELT Trend Analysis Tool")
        self.root.geometry("1000x700")

        self.df = None  # To store the current fetched data
        self.articles_df = None  # To store article list if requested
        self.stop_event = threading.Event()
        self.is_fetching = False
        self._create_ui()

    def _create_ui(self):
        # Top Frame for Controls
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Keyword
        tk.Label(
            control_frame,
            text="Keyword:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 5),
            pady=5
        )

        self.keyword_entry = tk.Entry(
            control_frame,
            width=25
        )

        self.keyword_entry.grid(
            row=0,
            column=0,
            sticky="e",
            padx=(0, 10),
            pady=5
        )

        self.keyword_entry.insert(0, "quantum computing")

        # Articles option
        tk.Label(control_frame, text="Include Articles:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.fetch_articles_var = tk.BooleanVar(value=False)

        self.fetch_articles_check = tk.Checkbutton(
            control_frame,
            text="Fetch Articles",
            variable=self.fetch_articles_var
        )

        self.fetch_articles_check.grid(
            row=1,
            column=0,
            sticky="e",
            padx=10,
            pady=5
        )

        # Time Span
        tk.Label(
            control_frame,
            text="Time Span:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 5),
            pady=5
        )

        self.time_span_var = tk.StringVar(value="Last Month")

        time_spans = [
            "Last Week",
            "Last Month",
            "2020 - Yesterday",
            "Custom"
        ]

        self.time_span_menu = ttk.Combobox(
            control_frame,
            textvariable=self.time_span_var,
            values=time_spans,
            state="readonly",
            width=15
        )

        self.time_span_menu.grid(
            row=2,
            column=0,
            sticky="e",
            padx=(0, 10),
            pady=5
        )

        self.time_span_menu.bind(
            "<<ComboboxSelected>>",
            self._on_time_span_change
        )

        # Custom Dates (Initially disabled)
        self.date_frame = tk.Frame(control_frame)
        self.date_frame.grid(row=3, column=0)
        
        tk.Label(self.date_frame, text="Start (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.start_date_entry = tk.Entry(self.date_frame, width=12)
        self.start_date_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.date_frame, text="End (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.end_date_entry = tk.Entry(self.date_frame, width=12)
        self.end_date_entry.pack(side=tk.LEFT, padx=5)

        self._update_date_entries_state()

        # Buttons
        btn_frame = tk.Frame(control_frame)
        btn_frame.grid(row=0, column=2, rowspan=1, padx=10)

        self.search_btn = tk.Button(btn_frame, text="Search", command=self.start_search, width=10, bg="green")
        self.search_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="Stop", command=self.stop_search, width=10, state=tk.DISABLED, bg="red")
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.export_btn = tk.Button(btn_frame, text="Export CSV", command=self.export_csv, width=10, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)

        self.analyze_btn = tk.Button(btn_frame, text="Analyze", command=self.open_dashboard, width=10, state=tk.DISABLED, bg="orange")
        self.analyze_btn.pack(side=tk.LEFT, padx=5)

        # Plot Area
        self.plot_frame = tk.Frame(self.root, bg="white", bd=2, relief=tk.SUNKEN)
        self.plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Log Area
        log_frame = tk.Frame(self.root)
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        tk.Label(log_frame, text="Status Log:").pack(side=tk.TOP, anchor=tk.W)
        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED)
        self.log_text.pack(side=tk.TOP, fill=tk.X)

    def _on_time_span_change(self, event=None):
        self._update_date_entries_state()

    def _update_date_entries_state(self):
        if self.time_span_var.get() == "Custom":
            self.start_date_entry.config(state=tk.NORMAL)
            self.end_date_entry.config(state=tk.NORMAL)
        else:
            self.start_date_entry.config(state=tk.DISABLED)
            self.end_date_entry.config(state=tk.DISABLED)

    def _confirm_article_range_warning(self, days):
        dialog = tk.Toplevel(self.root)
        dialog.title("Long Article Date Range")
        dialog.geometry("360x150")
        dialog.transient(self.root)
        dialog.grab_set()

        frame = tk.Frame(dialog, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text=(
                f"Selected date range is {days} days, which is longer than two weeks.\n"
                "Article results are limited to 250 records."
            ),
            justify=tk.LEFT,
            wraplength=330
        ).pack(pady=(0, 10))

        result = {"continue": False}

        def search_anyway():
            result["continue"] = True
            dialog.destroy()

        def stop():
            dialog.destroy()

        btn_frame = tk.Frame(frame)
        btn_frame.pack()

        tk.Button(btn_frame, text="Search Anyway", command=search_anyway, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Stop", command=stop, width=8).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result["continue"]

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{time_str}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _get_date_range(self):
        span = self.time_span_var.get()
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        if span == "Last Week":
            start = yesterday - timedelta(days=7)
            end = yesterday
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        elif span == "Last Month":
            start = yesterday - timedelta(days=30)
            end = yesterday
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        elif span == "2020 - Yesterday":
            return "2020-01-01", yesterday.strftime("%Y-%m-%d")
        else:
            return self.start_date_entry.get(), self.end_date_entry.get()

    def start_search(self):
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
        self.df = None
        self.articles_df = None
        self.ax.clear()
        self.canvas.draw()

        # Run in a background thread
        threading.Thread(target=self._fetch_data, args=(keyword, start_date, end_date), daemon=True).start()

    def stop_search(self):
        self.log("Stopping search requested...")
        self.stop_event.set()
        # Immediately reset GUI state
        self.is_fetching = False
        self.search_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED if self.df is None else tk.NORMAL)

    def _fetch_data(self, keyword, start_date, end_date):
        gd = GdeltDoc()
        f = Filters(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date
        )
        self.articles_df = None

        try:
            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Search stopped by user.")
                return

            self._sleep_before_request(15, "timeline")
            self.log("Calling GDELT API for timeline data (this may take a while)...")
            timeline = gd.timeline_search("timelinevol", f)

            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Search stopped by user.")
                return

            self.log("API call successful. Processing timeline data...")
            df = pd.DataFrame(timeline)
            
            if df.empty:
                self._on_search_finished(success=False, msg="No timeline data found for this query.")
                return

            df['datetime'] = pd.to_datetime(df['datetime'])
            df['date'] = df['datetime'].dt.date
            daily = df.groupby("date")["Volume Intensity"].mean().reset_index()
            daily.columns = ["date", "volume"]

            self.df = daily

            if self.fetch_articles_var.get():
                self._fetch_articles_after_timeline(keyword, start_date, end_date, gd)
            else:
                self._on_search_finished(success=True, msg="Timeline successfully fetched and processed.")

        except RateLimitError:
            self._handle_rate_limit(
                keyword,
                start_date,
                end_date,
                callback=self._fetch_data,
                args=(keyword, start_date, end_date)
            )
        except Exception as e:
            self.root.after(
                0,
                self._show_retry_dialog,
                f"An error occurred while fetching timeline data: {str(e)}",
                self._fetch_data,
                (keyword, start_date, end_date),
                False,
                None,
            )

    def _handle_rate_limit(self, keyword, start_date, end_date, callback, args=None, cancel_success=False, cancel_msg=None):
        if self.stop_event.is_set():
            self._on_search_finished(success=False, msg="Search stopped by user.")
            return

        self.log("Rate Limit Reached!")
        self.root.after(0, self._show_rate_limit_dialog, keyword, start_date, end_date, callback, args or (), cancel_success, cancel_msg)

    def _show_rate_limit_dialog(self, keyword, start_date, end_date, callback, args, cancel_success, cancel_msg):
        dialog = tk.Toplevel(self.root)
        dialog.title("API Limit Reached")
        dialog.geometry("380x170")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="GDELT API rate limit reached.\nHow would you like to proceed?", pady=10).pack()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        def retry_now():
            dialog.destroy()
            self.log("Retrying immediately...")
            threading.Thread(target=callback, args=args, daemon=True).start()

        def wait_and_retry(minutes):
            dialog.destroy()
            self.log(f"Waiting for {minutes} minutes before retrying...")
            threading.Thread(target=self._wait_timer, args=(minutes, callback, args), daemon=True).start()

        def cancel():
            dialog.destroy()
            if cancel_success:
                self._on_search_finished(success=True, msg=cancel_msg or "Timeline fetched; article retrieval cancelled.")
            else:
                self._on_search_finished(success=False, msg=cancel_msg or "Search cancelled due to rate limit.")

        tk.Button(btn_frame, text="Retry Now", command=retry_now).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 1 Min", command=lambda: wait_and_retry(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 5 Min", command=lambda: wait_and_retry(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Stop", command=cancel).pack(side=tk.LEFT, padx=5)

    def _show_retry_dialog(self, message, callback, args=None, cancel_success=False, cancel_msg=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("API Error")
        dialog.geometry("380x170")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=message, pady=10, wraplength=360, justify=tk.LEFT).pack()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        def retry_now():
            dialog.destroy()
            self.log("Retrying immediately...")
            threading.Thread(target=callback, args=args or (), daemon=True).start()

        def wait_and_retry(minutes):
            dialog.destroy()
            self.log(f"Waiting for {minutes} minutes before retrying...")
            threading.Thread(target=self._wait_timer, args=(minutes, callback, args or ()), daemon=True).start()

        def cancel():
            dialog.destroy()
            if cancel_success:
                self._on_search_finished(success=True, msg=cancel_msg or "Timeline fetched; article retrieval cancelled.")
            else:
                self._on_search_finished(success=False, msg=cancel_msg or "Search cancelled due to an error.")

        tk.Button(btn_frame, text="Retry Now", command=retry_now).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 1 Min", command=lambda: wait_and_retry(1)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Wait 5 Min", command=lambda: wait_and_retry(5)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)

    def _sleep_before_request(self, seconds, request_type):
        self.log(f"Sleeping {seconds} seconds before sending the {request_type} request...")
        for i in range(seconds):
            if self.stop_event.is_set():
                self.log("Request cancelled before sending.")
                return
            time.sleep(1)

    def _fetch_articles_after_timeline(self, keyword, start_date, end_date, gd):
        if self.stop_event.is_set():
            self._on_search_finished(success=False, msg="Search stopped by user.")
            return

        try:
            self._sleep_before_request(20, "article list")
            self.log("Calling GDELT API for article list (this may take a while)...")
            article_filters = Filters(
                keyword=keyword,
                start_date=start_date,
                end_date=end_date,
                num_records=250
            )
            articles = gd.article_search(article_filters)

            if self.stop_event.is_set():
                self._on_search_finished(success=False, msg="Search stopped by user.")
                return

            if articles is None or articles.empty:
                self.articles_df = pd.DataFrame()
                self._on_search_finished(success=True, msg="Timeline fetched successfully, but no articles were returned.")
                return

            self.articles_df = articles.copy()
            columns = list(articles.columns)
            col_summary = ", ".join(columns[:12]) + ("..." if len(columns) > 12 else "")
            self.log(f"Fetched {len(articles)} articles with columns: {col_summary}")

            date_column = None
            parse_format = None
            if 'seendate' in self.articles_df.columns:
                date_column = 'seendate'
                parse_format = "%Y%m%dT%H%M%SZ"
            elif 'publish_date' in self.articles_df.columns:
                date_column = 'publish_date'
            elif 'date' in self.articles_df.columns:
                date_column = 'date'

            if date_column is not None:
                if parse_format:
                    self.articles_df['article_datetime'] = pd.to_datetime(
                        self.articles_df[date_column], format=parse_format, errors='coerce'
                    )
                else:
                    self.articles_df['article_datetime'] = pd.to_datetime(
                        self.articles_df[date_column], errors='coerce'
                    )
                self.articles_df['article_date'] = self.articles_df['article_datetime'].dt.date

                if self.articles_df['article_datetime'].notna().any():
                    dates = self.articles_df['article_datetime'].dropna()
                    self.log(
                        f"Article date range: {dates.min().date()} to {dates.max().date()} using '{date_column}' column"
                    )
                else:
                    self.log(f"Unable to parse article dates from '{date_column}' values.")
            else:
                self.log("No publish/date column found in fetched articles.")

            # Add n_articles to timeline if article dates are available
            if 'article_date' in self.articles_df.columns and self.articles_df['article_date'].notna().any():
                article_counts = (
                    self.articles_df.groupby('article_date').size()
                    .rename('n_articles')
                    .reset_index()
                )
                self.df = self.df.merge(
                    article_counts,
                    left_on='date',
                    right_on='article_date',
                    how='left'
                )
                self.df['n_articles'] = self.df['n_articles'].fillna(0).astype(int)
                self.df.drop(columns=['article_date'], inplace=True)
                self.log("Added n_articles counts to timeline data.")

            self._on_search_finished(success=True, msg="Timeline and article list fetched successfully.")

        except RateLimitError:
            self._handle_rate_limit(
                keyword,
                start_date,
                end_date,
                callback=self._fetch_articles_after_timeline,
                args=(keyword, start_date, end_date, gd),
                cancel_success=True,
                cancel_msg="Timeline fetched; article retrieval cancelled due to rate limit."
            )
        except Exception as e:
            self.root.after(
                0,
                self._show_retry_dialog,
                f"An error occurred while fetching articles: {str(e)}",
                self._fetch_articles_after_timeline,
                (keyword, start_date, end_date, gd),
                True,
                "Timeline fetched; article retrieval cancelled due to an error."
            )

    def _wait_timer(self, minutes, callback, args):
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

    def _on_search_finished(self, success, msg):
        self.is_fetching = False
        
        # Schedule GUI updates on the main thread
        def update_gui():
            self.log(msg)
            self.search_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            if success and self.df is not None:
                self.export_btn.config(state=tk.NORMAL)
                self.analyze_btn.config(state=tk.NORMAL)
                self._plot_data()
        
        self.root.after(0, update_gui)

    def _plot_data(self):
        self.ax.clear()
        
        if self.df is not None and not self.df.empty:
            self.ax.plot(self.df['date'], self.df['volume'], color='blue', linewidth=1.5)
            self.ax.set_title(f"Media Coverage Volume Intensity", fontsize=12)
            self.ax.set_xlabel("Date", fontsize=10)
            self.ax.set_ylabel("Relative Coverage (%)", fontsize=10)
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # Rotate x-axis dates for better readability
            self.fig.autofmt_xdate()
            
            self.canvas.draw()
            self.log("Plot updated.")

    def export_csv(self):
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
            filetypes=filetypes
        )
        
        if filepath:
            try:
                if self.articles_df is not None and not self.articles_df.empty:
                    if not filepath.lower().endswith('.zip'):
                        filepath += '.zip'
                    with zipfile.ZipFile(filepath, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                        timeline_name = os.path.basename(filepath).replace('.zip', '_timeline.csv')
                        articles_name = os.path.basename(filepath).replace('.zip', '_articles.csv')
                        zf.writestr(timeline_name, self.df.to_csv(index=False))
                        zf.writestr(articles_name, self.articles_df.to_csv(index=False))
                    self.log(f"Timeline and article data exported successfully to: {filepath}")
                    messagebox.showinfo(
                        "Export Success",
                        f"Timeline and article data exported successfully in ZIP:\n{filepath}"
                    )
                else:
                    if not filepath.lower().endswith('.csv'):
                        filepath += '.csv'
                    self.df.to_csv(filepath, index=False)
                    self.log(f"Timeline data exported successfully to: {filepath}")
                    messagebox.showinfo("Export Success", "Timeline data exported successfully! It is now ready for Power BI.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save file:\n{str(e)}")

    def open_dashboard(self):
        if self.df is None or self.df.empty:
            messagebox.showwarning("Analysis Error", "No timeline data to analyze.")
            return

        try:
            keyword = self.keyword_entry.get().strip()
            temp_dir = os.path.join(os.path.expanduser("~"), ".gdelt_temp")
            os.makedirs(temp_dir, exist_ok=True)

            timeline_path = os.path.join(temp_dir, "timeline_data.csv")
            articles_path = None

            self.df.to_csv(timeline_path, index=False)
            self.log(f"Temporary timeline data saved to: {timeline_path}")

            if self.articles_df is not None and not self.articles_df.empty:
                articles_path = os.path.join(temp_dir, "articles_data.csv")
                self.articles_df.to_csv(articles_path, index=False)
                self.log(f"Temporary articles data saved to: {articles_path}")

            from dashboard_gui import launch_dashboard

            threading.Thread(
                target=launch_dashboard,
                args=(timeline_path, articles_path, keyword),
                daemon=True
            ).start()

            self.log("Dashboard launched. Closing search window...")
            self.root.quit()

        except Exception as e:
            messagebox.showerror("Dashboard Error", f"Failed to open dashboard: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GdeltApp(root)
    root.mainloop()
